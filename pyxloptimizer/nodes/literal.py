import ast

import numpy
from numpy import ndarray

from ..ast import ast_call
from .node import Node
from ..excel_reference import DataType
from ..shape import Shape, SCALAR_SHAPE


class LiteralNode(Node):
    def __init__(self, variable_name, value):
        super().__init__(variable_name, children=[])
        self.value = value

    @classmethod
    def build(cls, varname, token):
        match token.subtype:
            case token.NUMBER:
                try:
                    result = LiteralNode(varname, int(token.value))
                except ValueError:
                    result = LiteralNode(varname, float(token.value))
            case token.TEXT:
                # Strings are quoted so drop the starting and ending quotes.
                # Todo deal with quotes, need to check how excel handles them.
                result = LiteralNode(varname, token.value[1:-1])
            case token.LOGICAL:
                result = LiteralNode(varname, token.value.lower() == "true")
            case _:
                raise NotImplemented(f"Unknown operator token of subtype {token.subtype} and value {token.value}")
        return result

    @property
    def shape(self):
        if isinstance(self.value, numpy.ndarray):
            return Shape(*self.value.shape)
        else:
            return SCALAR_SHAPE

    @property
    def data_type(self):
        if self.value is None:
            return DataType.Blank
        elif isinstance(self.value, numpy.ndarray):
            # todo build mapping from dtype to DataType
            return DataType.Number
        elif isinstance(self.value, str):
            return DataType.String
        elif isinstance(self.value, bool):
            return DataType.Boolean
        else:
            return DataType.Number

    @property
    def ref(self):
        """
        If this is an array, then we use the normal convention, but if this is a constant value use the value
        itself as a reference to make the output code more readable.
        """
        if isinstance(self.value, ndarray):
            return super().ref
        else:
            return ast.Constant(value=self.value)

    @property
    def ast(self):
        """
        If this is an array literal then we create a variable otherwise the ref is the constant itself, and
        we don't require a statement for it.
        """
        if isinstance(self.value, ndarray):
            vals = self.value.tolist()
            if self.value.ndim == 2:
                elts = [ast.List([ast.Constant(v) for v in row], ctx=ast.Load()) for row in vals]
            else:
                assert self.value.ndim == 1
                elts = [ast.Constant(v) for v in vals]
            ast_value = ast_call('numpy.array', [ast.List(elts=elts, ctx=ast.Load())])
            return self._ast_wrap(ast_value)
        else:
            return None

    def __repr__(self):
        return f"LN:{self.value}"
