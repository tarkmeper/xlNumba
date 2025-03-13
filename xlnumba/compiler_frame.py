from abc import ABCMeta, abstractmethod
from collections import deque
from dataclasses import dataclass
from enum import Enum

from openpyxl.formula import Tokenizer

from .excel_reference import ExcelReference, BIN_OP_MAP
from .logger import logger
from .nodes import FunctionOpNode, Node, LiteralNode, ComparisonNode, BinOpNode, ExcelArrayNode, IndexNode
from .shunting_yards import ShuntingYardsOperator

TokenType = type(Tokenizer('').token)


class CompilerReference:
    """
    CompilerReferences represent a request that the main loop needs to satisfy by providing a Node which matches this
    reference.  There are 3 types of references which take different data packages.
        1) Range - these are excel ranges
        2) Function - represents a function call
        3) Paraen - A bracketted statement
    """

    @dataclass
    class FunctionCallData:
        name: str
        args: tuple[tuple[TokenType, ...], ...]

        def __hash__(self): return hash(self.name) ^ hash(self.args)

    class Mode(Enum):
        range = 1
        function = 2
        paren = 3

    def __init__(self,
                 mode: Mode,
                 active_cell: ExcelReference,
                 data: FunctionCallData | tuple[TokenType, ...] | None = None
                 ):
        self.mode: CompilerReference.Mode = mode
        self.active_cell: ExcelReference = active_cell
        self.data: CompilerReference.FunctionCallData | tuple[TokenType, ...] | None = data
        # check setup correctly
        if mode == CompilerReference.Mode.range:
            assert data is None
            self.data = self.active_cell
        elif mode == CompilerReference.Mode.paren:
            assert isinstance(data, tuple)
        elif mode == CompilerReference.Mode.function:
            assert isinstance(data, self.__class__.FunctionCallData)
            self.func_data = data
        else:
            raise NotImplementedError(f"Mode {mode} has not be implemented")

    def __repr__(self) -> str:
        return f"{self.mode} : {self.active_cell.sheet} : {self.data}"

    def __eq__(self, other):
        return self.active_cell.sheet == other.active_cell.sheet and self.data == other.data

    def __hash__(self):
        return hash(self.active_cell.sheet) ^ hash(self.data)


class CompilerFrame(metaclass=ABCMeta):
    """
    Compiler frames are the base use of work in parsing the Excel framework.  Each represents a portion of the
    work book to convert in to our internal graph representation.

    Each frame represents a token in the Excel sheet we are attempting to process.
    """

    def __init__(self, ref: CompilerReference, parent: 'CompilerFrame' = None):
        self._idx = 0
        self._ref = ref
        self._parent = parent

    def next_idx(self) -> str:
        """
        Return the unique name that we should use for variables that are generated from
        this expression.

        If this frame refers to a specific cell, we return that.  If it is a sub-expression
        of some sort we get the variable name from the parent variable.
        ."""
        if isinstance(self._ref.data, ExcelReference):
            self._idx += 1
            return f"{self._ref.data.encode_name()}_{self._idx}"
        else:
            return self._parent.next_idx()

    @abstractmethod
    def next_reference(self) -> CompilerReference:
        """
        Value of internal state machine for this frame. Move forward to the next reference that this
        complier frame is looking for.

        Return None when we have reached the last reference to processes.
        """
        raise NotImplementedError()

    def __repr__(self):
        return f"{self.__class__.__name__} - {self.referenced_object}"

    @abstractmethod
    def push_node(self, node: Node):
        """
        Push the value of the last reference requested and continue processing until we hit the
        next unknown reference.
        """
        raise NotImplementedError()

    @property
    def referenced_object(self) -> CompilerReference:
        """ The source that created this frame """
        return self._ref

    @property
    def active_cell(self) -> ExcelReference:
        """ The cell in Excel that created this frame. """
        return self._ref.active_cell

    @abstractmethod
    def finalize(self) -> Node:
        raise NotImplementedError()

    def consume(self):
        # shouldn't happen unless enters START state which is only on _Token frames.  Added here to avoid
        # alerts in IDE messages in compiler.py, however, if ever called should error.
        raise NotImplementedError()


class _TokenFrame(CompilerFrame):
    """
    Token frame is the root processor for tokenized expressions.  It takes a string of tokens
    and applies the ShutingYards algoirthm to them to build up a tree for evaluation.
    """

    def __init__(self, ref: CompilerReference, tokens: deque, parent: CompilerFrame = None):
        super().__init__(ref, parent)
        self._operator = ShuntingYardsOperator()
        self._tokens = tokens
        self._next_reference = None  # not needed consume will set, but this elimiantes warnning is PyCharm
        self.consume()

    def next_reference(self) -> CompilerReference:
        return self._next_reference

    def consume(self):
        while self._tokens:
            token = self._tokens.popleft()

            match token.type:
                case token.OPERAND:
                    if token.subtype == token.RANGE:
                        new_reference = self.active_cell.create_relative(token.value)
                        assert new_reference
                        self._next_reference = CompilerReference(mode=CompilerReference.Mode.range,
                                                                 active_cell=new_reference)
                        return
                    else:
                        node = LiteralNode.build(self.next_idx(), token)
                        self._operator.push_output(node)
                case token.OP_IN:
                    self._operator.push_operator(token.value)
                case token.OP_PRE:
                    self._operator.apply_prefix(token.value)
                case token.OP_POST:
                    self._operator.apply_postfix(token.value)
                case token.FUNC:
                    assert token.subtype == token.OPEN
                    args = consume_until_matching_paren(self._tokens)
                    self._next_reference = CompilerReference(mode=CompilerReference.Mode.function,
                                                             active_cell=self.active_cell,
                                                             data=CompilerReference.FunctionCallData(token.value, args))
                    return
                case token.PAREN:
                    assert token.subtype == token.OPEN
                    args = consume_until_matching_paren(self._tokens)
                    assert len(args) == 1
                    self._next_reference = CompilerReference(mode=CompilerReference.Mode.paren,
                                                             active_cell=self.active_cell, data=args[0])
                    return
                case token.WSPACE:
                    continue
                case _:
                    raise NotImplementedError(f"Token of type {token.type} and value {token.value} not handled.")

        self._next_reference = None

    def push_node(self, node: Node):
        self._operator.push_output(node)
        self.consume()

    def finalize(self):
        stack = []
        output_stack = self._operator.finalize()
        logger.debug(f"{self} - RPN stack: {output_stack}")
        for elem in output_stack:
            if isinstance(elem, Node):
                stack.append(elem)
            else:
                right = stack.pop()
                left = stack.pop()
                elem_details = BIN_OP_MAP[elem]
                if elem == "&":
                    from . import excel_functions as exl

                    node = FunctionOpNode(self.next_idx(), exl.INTERNAL_CONCAT, [left, right])
                    stack.append(node)
                elif elem_details.comparison:
                    stack.append(ComparisonNode(self.next_idx(), elem_details.astOperator, left, right))
                else:
                    stack.append(BinOpNode(self.next_idx(), elem_details.astOperator, left, right))
        assert len(stack) == 1  # If more than 1 something has gone badly wrong and RPN doesn't evaluate.
        return stack.pop()


class CellReferenceCompilerFrame(_TokenFrame):
    def __init__(self, ref: CompilerReference, parent: CompilerFrame = None):
        if ref.data.is_array or ref.data.data_type == 'f':
            logger.debug(f"Starting on reference {ref} with value {ref.data.value}")
            tokens = deque(Tokenizer(ref.data.value).items)
            super().__init__(ref=ref, tokens=tokens, parent=parent)
        else:
            # very hacky but for literal nodes just change them to an expression which
            # can evaluate to their value
            super().__init__(ref=ref, tokens=deque(), parent=parent)
            node = LiteralNode(ref.data.encode_name(), ref.data.value)
            self._operator.push_output(node)


class NestedCompilerFrame(_TokenFrame):
    def __init__(self, ref: CompilerReference, parent: CompilerFrame):
        assert isinstance(ref.data, tuple)
        super().__init__(ref=ref, parent=parent, tokens=deque(ref.data))


class ArrayReferenceCompilerFrame(_TokenFrame):
    def __init__(self, ref: CompilerReference, array_src: ExcelReference, parent: CompilerFrame):
        super().__init__(ref=ref, parent=parent, tokens=deque(Tokenizer(array_src.value).items))


class FunctionCompilerFrame(CompilerFrame):
    def __init__(self, ref: CompilerReference, parent, name, details):
        assert isinstance(ref.data, CompilerReference.FunctionCallData)

        super().__init__(ref=ref, parent=parent)
        self._name = name
        self._details = details
        self._args: list[Node] = []
        self._child_tokens: tuple[tuple[TokenType, ...], ...] = ref.data.args

    def next_reference(self) -> CompilerReference | None:
        if len(self._child_tokens) == len(self._args):
            return None
        else:
            return CompilerReference(mode=CompilerReference.Mode.paren, active_cell=self.active_cell,
                                     data=self._child_tokens[len(self._args)])

    def finalize(self):
        logger.debug(f"Function node {self._name} created with args {self._args}")
        node = self._details.prepare_function(self.next_idx, self._args)
        return node

    def push_node(self, node: Node):
        self._args.append(node)

    def force_additional_args(self, args: list[Node]):
        self._child_tokens = tuple([tuple() for _ in range(len(args))]) + self._child_tokens
        self._args.extend(args)


class RangeBuildFrame(CompilerFrame):
    def __init__(self, range_ref: CompilerReference, parent: CompilerFrame = None):
        super().__init__(ref=range_ref, parent=parent)
        self._cells = list(range_ref.data.get_cells())
        self._args: list[Node] = []

    def next_reference(self):
        if len(self._cells) == len(self._args):
            return None
        else:
            return CompilerReference(mode=CompilerReference.Mode.range, active_cell=self._cells[len(self._args)])

    def push_node(self, node: Node):
        self._args.append(node)

    def finalize(self):
        return ExcelArrayNode(self.next_idx(), self._ref.data.shape, self._args)


class IndexExtractFrame(CompilerFrame):
    def __init__(self, ref: CompilerReference, offsets, parent: CompilerFrame = None):
        super().__init__(ref=ref, parent=parent)
        self._array_ref = ref.data.array_src
        self._offset = offsets
        self._array_node = None

    def next_reference(self):
        if self._array_node is None:
            assert self._array_ref
            return CompilerReference(mode=CompilerReference.Mode.range, active_cell=self._array_ref)
        else:
            return None

    def push_node(self, node: Node):
        self._array_node = node

    def finalize(self):
        return IndexNode(self.next_idx(), self._array_node, self._offset)


def consume_until_matching_paren(tokens: deque) -> tuple[tuple[TokenType, ...], ...]:
    """
    Consume elements from the token stack storing them on a list of children stacks until we have
    matched the end of the current parameter.  This is used to handle nested functions and
    sub-expressions.
    """
    stack_count = 1
    sub_tokens: list[TokenType] = []
    children: list[list[TokenType]] = []

    while stack_count > 0:
        next_token = tokens.popleft()

        if next_token.type == next_token.FUNC or next_token.type == next_token.PAREN:
            # if we hit a nested object increase stack count, if not decrase stack count.
            stack_count += 1 if next_token.subtype == next_token.OPEN else -1
            if stack_count != 0:
                sub_tokens.append(next_token)
        elif next_token.type == next_token.SEP and stack_count == 1:
            # If we are in the top stack & hit a seperator is another aparemeter
            assert next_token.subtype == next_token.ARG
            children.append(sub_tokens)
            sub_tokens = list()
        else:
            sub_tokens.append(next_token)
    children.append(sub_tokens)

    # if the last child is empty remove it from the results
    if len(children[-1]) == 0:
        children.pop()

    return tuple(tuple(x for x in sublist) for sublist in children)


def create_compiler_frame(ref: CompilerReference) -> CompilerFrame:
    """
    Create compiler frame to build and return a specific reference.
    """
    logger.debug(f"Starting on creation of data for {ref}")
    if ref.active_cell.is_range:
        new_frame = RangeBuildFrame(ref)
    elif ref.active_cell.is_array:
        logger.debug(f"Building index frame for reference {ref.data} with offsets {ref.data.offsets}")
        new_frame = IndexExtractFrame(ref, ref.data.offsets)
    else:
        new_frame = CellReferenceCompilerFrame(ref)
    return new_frame
