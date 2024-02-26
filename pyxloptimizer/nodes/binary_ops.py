import abc
import ast
from .node import Node
from ..excel_reference import DataType
from ..shape import Shape


class _BinaryHelperNode(Node, metaclass=abc.ABCMeta):
    """
    A helper class for the two different binary operation nodes (comparison versus binOps).  The two are mostly the same
    but due to differences in how the AST is structured are represented as two different classes.

    This class provides most of the functionality while the two subclasses provide data types and ast generation.
    """

    def __init__(self, variable_name: str, operator, left_child: Node, right_child: Node):
        super().__init__(variable_name, [left_child, right_child])
        self.operator = operator

    @property
    def left(self) -> Node: return self._children[0]

    @property
    def right(self) -> Node: return self._children[1]

    @property
    def shape(self) -> Shape: return self.left.shape.merge(self.right.shape)


class ComparisonNode(_BinaryHelperNode):
    @property
    def data_type(self): return DataType.Boolean

    @property
    def ast(self):
        return self._ast_wrap(
            ast.Compare(
                left=self.left.ref,
                ops=[self.operator()],
                comparators=[self.right.ref]
            )
        )

    def __repr__(self): return f"{self.varname} = ON:{self.ast.value.ops.__class__.__name__}"


class BinOpNode(_BinaryHelperNode):
    @property
    def data_type(self): return DataType.Number

    @property
    def ast(self):
        return self._ast_wrap(
            ast.BinOp(
                left=self.left.ref,
                op=self.operator(),
                right=self.right.ref)
        )

    def __repr__(self): return f"{self.varname} = ON:{self.ast.value.op.__class__.__name__}"
