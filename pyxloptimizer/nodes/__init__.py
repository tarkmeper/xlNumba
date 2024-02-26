from .array import FlatArrayNode, ExcelArrayNode, IndexNode
from .binary_ops import ComparisonNode, BinOpNode
from .function import FunctionOpNode
from .io import InputNode, OutputNode, Graph
from .literal import LiteralNode
from .node import Node
from .random import RandomValueNode, RandBetweenNode
from ..excel_reference import ExcelReference
from ..shape import SCALAR_SHAPE


def wrap_output(output_name: str, output_node: Node, shape=SCALAR_SHAPE) -> OutputNode:
    assert output_node.shape.size == shape.size
    return OutputNode(output_name, [output_node])


def wrap_input(input_cell: ExcelReference, input_name: str) -> InputNode:
    return InputNode(input_name, input_cell.shape, input_cell.data_type)
