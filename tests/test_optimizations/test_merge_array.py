import xlnumba.excel_functions as excel_functions
from xlnumba.nodes import LiteralNode, FunctionOpNode, FlatArrayNode, ExcelArrayNode, wrap_output
from xlnumba.optimizations import merge_array
from xlnumba.shape import Shape
from ..util import get_collapsed_result


def _create_array(name, lst):
    return ExcelArrayNode(name, Shape(len(lst), 1), lst)


def test_merge_array_simple_equal():
    # Test that the optimization collapses literals in a simple expression.
    arr1 = _create_array("arr1", [lt1, lt2])
    arr2 = _create_array("arr2", [lt1, lt2])

    base_node = FunctionOpNode("top",
                               excel_functions.SUM,
                               [FlatArrayNode("topArg", [arr1, arr2])]
                               )
    node = wrap_output("dst", base_node)
    assert _array_count(node, set()) == 2
    merge_array([("dst", node), ])
    assert _array_count(node, set()) == 1
    assert get_collapsed_result(base_node) == 6


def test_merge_array_disjoint():
    # Test that the optimization collapses literals in a simple expression.
    arr1 = _create_array("arr1", [lt1, lt2])
    arr2 = _create_array("arr2", [lt1, lt2, lt3])

    base_node = FunctionOpNode("top",
                               excel_functions.SUM,
                               [FlatArrayNode("topArg", [arr1, arr2])]
                               )
    node = wrap_output("dst", base_node)
    assert _array_count(node, set()) == 2
    merge_array([("dst", node), ])
    assert _array_count(node, set()) == 1

    assert get_collapsed_result(base_node) == 9


def test_merge_array_dependent():
    # Test that the optimization collapses literals in a simple expression.
    arr1 = _create_array("arr1", [lt1, lt2])
    nx3 = FunctionOpNode("nx3", excel_functions.SUM, [arr1])
    arr2 = _create_array("arr2", [lt1, lt2, nx3])

    base_node = FunctionOpNode("top",
                               excel_functions.SUM,
                               [FlatArrayNode("topArg", [arr1, arr2])]
                               )
    node = wrap_output("dst", base_node)
    assert _array_count(node, set()) == 2
    merge_array([("dst", node), ])
    assert _array_count(node, set()) == 0  # can't but array nodes will be replaced.

    # can't test with collapse literal as that doesn't support collapsing it onto the buffer arrays yet


def _array_count(node, visited):
    if node in visited:
        return 0
    visited.add(node)
    cnt = 1 if isinstance(node, ExcelArrayNode) else 0
    for child in node.children:
        cnt += _array_count(child, visited)
    return cnt


lt1 = LiteralNode("tmp1", 1)
lt2 = LiteralNode("tmp2", 2)
lt3 = LiteralNode("tmp3", 3)
