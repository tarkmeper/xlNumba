import ast

from .node import Node
from ..ast import ast_tuple
from ..excel_reference import ExcelReference


class OutputNode(Node):
    """
    Output nodes map the result of a function to an output variable for vectors we turn these back into a 1D
    numpy array for ease of use.
    """

    @property
    def top(self):
        return self._children[0]

    @property
    def data_type(self):
        return self.top.data_type

    @property
    def shape(self):
        return self.top.shape

    @property
    def output_variable(self):
        if not self.shape.is_vector:
            return self.top.ref
        else:
            return super().ref

    @property
    def ast(self):
        if not self.shape.is_vector:
            return None
        else:
            if self.shape.horizontal:
                slc = ast_tuple(ast.Constant(0), ast.Slice(None, None))
            else:
                slc = ast_tuple(ast.Slice(None, None), ast.Constant(0))

            return self._ast_wrap(
                ast.Subscript(
                    value=self.top.ref,
                    slice=slc,
                    ctx=ast.Load()
                )
            )


class InputNode(Node):
    def __init__(self, src_name, shape, input_type):
        super().__init__(src_name, children=[])
        self._shape = shape
        self._data_type = input_type

    @property
    def shape(self):
        return self._shape

    @property
    def data_type(self):
        return self._data_type

    @property
    def ast(self):
        return None

    def __repr__(self):
        return f"IN:{self._var}"


Graph = list[tuple[ExcelReference, OutputNode]]
