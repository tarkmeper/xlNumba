"""
Special functions are not mathematical functions but need references from other parts of the sheet or workbook.
"""
from .compiler_frame import CompilerFrame, ArrayReferenceCompilerFrame, FunctionCompilerFrame
from .excel_functions import random as excel_random_fn
from .nodes import Node, LiteralNode, RandomValueNode


def anchor_array(frame: CompilerFrame, parameters: list) -> CompilerFrame:
    """
    Anchor array takes a string reference and turns it into field.

    :param frame: Parent frame that called this.
    :param parameters: Parameter list; should only be a single paramter, but my have some whitespace filters.
    :return: New frame that references the underlying array.
    """
    assert len(parameters) == 1
    ref_str = list(filter(lambda x: x.type != x.WSPACE, parameters[0]))
    assert len(ref_str) == 1
    new_ref = frame.active_cell.create_relative(ref_str[0].value + "#")
    return ArrayReferenceCompilerFrame(ref=frame.next_reference(), array_src=new_ref, parent=frame)


def sheet_count(frame: CompilerFrame, _child_deque: list) -> Node:
    return LiteralNode(frame.next_idx(), frame.active_cell.sheet_count)


def basic_lookup(fnc):
    def row(frame: CompilerFrame, child_deque: list) -> Node:
        assert len(child_deque) == 0
        return LiteralNode(frame.next_idx(), fnc(frame))

    return row


def random(frame, _parameters):
    """
    Random in Excel is special because in an array context the random generator will generate a number of random values
    to match what is needed.  When rand is called we need to determine the size of the current active cells array
    reference
    :return:
    """
    cell = frame.active_cell
    node = RandomValueNode(frame.next_idx(), cell.shape)
    return node


def random(frame, _parameters):
    """
    Random in Excel is special because in an array context the random generator will generate a number of random values
    to match what is needed.  When rand is called we need to determine the size of the current active cells array
    reference
    :return:
    """
    cell = frame.active_cell
    node = RandomValueNode(frame.next_idx(), cell.shape)
    return node


def random_between(frame, _parameters):
    """
    RandBetween returns a random number between two values.  Since this does need to parse the input parameters we
    can't just return a node directly but need to create a function node for this purpose.

    However, there is a degree of complexity here as we also need to provide the "shape" of the random node
    in order for the generator to create it.  We force these as two preliminary arguments to the function.

    :return:
    """
    cell = frame.active_cell
    next_reference = frame.next_reference()
    fn_details = excel_random_fn.RandomBetweenFunction(shape=cell.shape)
    frame = FunctionCompilerFrame(next_reference, frame, "rand_between", fn_details)
    return frame


SPECIAL_FUNCTION_MAP = {
    'ANCHORARRAY': anchor_array,
    'COLUMN': basic_lookup(lambda frame: frame.active_cell.column),
    'ROW': basic_lookup(lambda frame: frame.active_cell.row),
    'SHEETS': sheet_count,
    'RAND': random,
    'RANDBETWEEN': random_between,
}
