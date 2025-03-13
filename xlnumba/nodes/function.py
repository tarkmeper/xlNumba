import ast

from .node import Node
from ..ast import ast_call


class FunctionOpNode(Node):
    def __init__(self, variable_name: str, function_details, children: list[Node]):
        super().__init__(variable_name, children)
        self.in_place = False
        self.disable_numba = False
        self._function_details = function_details

    @property
    def excel_name(self):
        return self._function_details.excel_name

    @property
    def shape(self):
        return self._function_details.compute_shape(self.children)

    @property
    def ref(self):
        """
        If this calculation is in place, then it needs to be executed in place and the variable
        name is not updated.
        """
        if self.in_place:
            return self._children[0].ref
        else:
            return super().ref

    @property
    def data_type(self):
        return self._function_details.compute_resulting_type(self.children)

    @property
    def in_place_supported(self):
        return len(self.children) == 1 and \
            not self._function_details.compute_shape(self.children).is_scalar and \
            self.children[0].data_type == self.data_type and \
            len(self.children[0]._parents) == 1 and \
            self._function_details.in_place_supported()

    @property
    def ast(self):
        fnc_name = self._function_details.fnc_str(self.disable_numba)

        if self.in_place:
            assert self._function_details.in_place_supported()
            call = ast_call(fnc_name, [x.ref for x in self.children] + [self.children[0].ref])
            return ast.Expr(call)
        else:
            call = ast_call(fnc_name, [x.ref for x in self.children])
            return self._ast_wrap(call)

    def __repr__(self):
        fnc_name = self._function_details.fnc_str(True).replace(".py_func", "")
        fnc_args = ",".join([str(x) for x in self.children])
        return f"{self.varname} = FN:{fnc_name}({fnc_args})"
