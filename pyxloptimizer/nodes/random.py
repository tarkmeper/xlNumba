import ast
from abc import ABCMeta

from .node import Node
from ..ast import ast_tuple
from ..excel_reference import DataType
from ..shape import Shape


class _RandBaseNode(Node, metaclass=ABCMeta):
    """
    A helper class for the two different binary operation nodes (comparison versus binOps).  The two are mostly the same
    but due to differences in how the AST is structured are represented as two different classes.

    This class provides most of the functionality while the two subclasses provide data types and ast generation.
    """

    def __init__(self, variable_name: str, children: list[Node], shape: Shape):
        super().__init__(variable_name, children)
        self._shape = shape

    @property
    def data_type(self): return DataType.Number

    @property
    def shape(self) -> Shape: return self._shape

    def __repr__(self): return f"Random:{self.__class__.__name__}"


class RandomValueNode(_RandBaseNode):

    def __init__(self, varname, shape):
        super().__init__(varname, [], shape)

    @property
    def ast(self) -> ast.stmt:
        # if numba ever supports generators this is probably better way to do it.
        # ast_name = ast.Name(GENERATOR_VAR_NAME, ctx=ast.Load())
        # ast_method = ast.Attribute(value=ast_name, attr="random", ctx=ast.Load())

        ast_name = ast.Name('numpy', ctx=ast.Load())
        ast_module = ast.Attribute(value=ast_name, attr="random", ctx=ast.Load())
        ast_method = ast.Attribute(value=ast_module, attr="rand", ctx=ast.Load())

        call = ast.Call(
            func=ast_method,
            args=[ast.Constant(self._shape.width), ast.Constant(self._shape.height)],
            keywords=[]
        )

        return self._ast_wrap(call)


class RandBetweenNode(_RandBaseNode):
    """
    Random between nodes has two children nodes which represent the low and high value for the randbetween
    function.
    """

    def __init__(self, variable_name: str, low: Node, high: Node, shape: Shape):
        super().__init__(variable_name, [low, high], shape)

    @property
    def ast(self) -> ast.stmt:
        # if numba ever supports generators this is probably better way to do it.
        # ast_name = ast.Name(GENERATOR_VAR_NAME, ctx=ast.Load())
        # ast_method = ast.Attribute(value=ast_name, attr="random", ctx=ast.Load())

        ast_name = ast.Name('numpy', ctx=ast.Load())
        ast_module = ast.Attribute(value=ast_name, attr='random', ctx=ast.Load())
        ast_method = ast.Attribute(value=ast_module, attr="randint", ctx=ast.Load())

        call = ast.Call(
            func=ast_method,
            args=[self._children[0].ref, self._children[1].ref, ast_tuple(self._shape.width, self._shape.height), ],
            keywords=[]
        )

        return self._ast_wrap(call)
