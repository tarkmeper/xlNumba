from .function_details import BaseFunction
from ..excel_reference import DataType
from ..nodes import Node, LiteralNode


class DataTypeFunction(BaseFunction):
    """
    Function which returns if the argument mathches a specific data type.  This is processed at compile
    time, so is not very useful.  Dynamic types are not supported.
    """

    def __init__(self, option):
        super().__init__()
        self.option = option

    def prepare_function(self, idx: str, args: list[Node]) -> Node:
        val = args[0]

        if self.option == "TEXT":
            return LiteralNode(idx, val.data_type == DataType.String)
        elif self.option == "NONTEXT":
            return LiteralNode(idx, val.data_type != DataType.String)
        elif self.option == "NUMBER":
            return LiteralNode(idx, val.data_type == DataType.Number)
        elif self.option == "TYPE":
            if val.data_type == DataType.Number:
                return LiteralNode(idx, 1)
            elif val.data_type == DataType.String:
                return LiteralNode(idx, 2)
        else:
            assert self.option == "BLANK"
            if isinstance(val, LiteralNode) and val.value is None:
                return LiteralNode(idx, True)
            return LiteralNode(idx, False)

    def compute_shape(self, children):
        return children[0].shape

    def compute_resulting_type(self, children):
        return DataType.Boolean if self.option != "TYPE" else DataType.Number
