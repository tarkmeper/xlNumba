import ast

from pyxloptimizer.excel_reference import BIN_OP_MAP
from pyxloptimizer.nodes import Node, BinOpNode, LiteralNode


class ShuntingYardsOperator:
    """
    See https://en.wikipedia.org/wiki/Shunting-yard_algorithm with slight modification to support pre-fix and
    post-fix unary operators.

    To handle paranethesis, we leverage recursion rather than the adjustment into the algorithm. Since ultimately
    the tree we are building can handle the recursion this makes the algorithm simpler.

    The other difference with the standard algorithm is a minor modification to support prefix/postfix unary operates
    in the tokens.
    """

    def __init__(self):
        """
        next_prefix special case to store a modifier for next output object supplied.
        """
        self.operator_stack = []
        self.output_stack = []
        self.precedence = {k: v.precedence for k, v in BIN_OP_MAP.items()}
        self.next_prefix = None

    def push_output(self, node: Node):
        if self.next_prefix:
            assert self.next_prefix == '-'  # only prefix I'm aware of is negative, and there must be a value after it.
            node = wrap_node_with_multiplier(node, -1, '_neg')
        self.output_stack.append(node)
        self.next_prefix = None

    def push_operator(self, op: str):
        token_precedence = self.precedence[op]
        while self.operator_stack and self.precedence[self.operator_stack[-1]] >= token_precedence:
            self.output_stack.append(self.operator_stack.pop())
        self.operator_stack.append(op)

    def apply_prefix(self, op: str):
        self.next_prefix = op

    def apply_postfix(self, op: str):
        # postfix are a bit easier than prefix since we know it came after an output can just apply directly to last
        # output.
        assert len(self.output_stack) > 0
        assert op == '%'  # only currently supported postfix.
        self.output_stack[-1] = wrap_node_with_multiplier(self.output_stack[-1], 0.01, "_pct")

    def finalize(self) -> list[Node]:
        assert self.next_prefix is None  # prefix should have been cleared before we got here, if not something wrong
        self.output_stack.extend(reversed(self.operator_stack))
        return self.output_stack


def wrap_node_with_multiplier(node: Node, multiplier: float, postfix: str) -> Node:
    """
    Modify the node to handle prefix/postfix operators with a multiplication (specifically % or -).
    """
    new_node = BinOpNode(node.varname, ast.Mult, node, LiteralNode(node.varname + postfix, multiplier))
    return new_node
