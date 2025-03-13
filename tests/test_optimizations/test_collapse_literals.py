import ast

import xlnumba.excel_functions as excel_functions
from xlnumba.nodes import LiteralNode, FunctionOpNode, BinOpNode, ExcelArrayNode, IndexNode
from xlnumba.shape import Shape
from ..util import get_collapsed_result


def test_collapse_literals_simple():
    # Test that the optimization collapses literals in a simple expression.
    node = BinOpNode("tmp3",
                     ast.Add,
                     LiteralNode("tmp1", 1),
                     LiteralNode("tmp2", 2)
                     )
    assert get_collapsed_result(node) == 3


def test_collapse_literals_multilayer():
    # Test that the optimization collapses literals in a more complex expression with multiple levels.
    node = BinOpNode(
        "tmp5",
        ast.Mult,
        BinOpNode(
            "tmp1",
            ast.Add,
            LiteralNode("tmp2", 1),
            LiteralNode("tmp3", 2)
        ),
        LiteralNode("tmp4", 3)
    )
    assert get_collapsed_result(node) == 9


def test_collapse_literals_simple_function():
    # Test that the optimization collapses literals in a function call.
    node = FunctionOpNode(
        "tmp1",
        excel_functions.SUM,
        [
            ExcelArrayNode("ar1", Shape(3, 1), [
                LiteralNode("tmp2", 1),
                LiteralNode("tmp3", 2),
                LiteralNode("tmp4", 3)
            ])
        ]
    )
    assert get_collapsed_result(node) == 6


def test_collapse_index_element():
    # Test index node calls can work given that they work a bit differently then function calls.
    node = IndexNode(
        "tmp1",
        ExcelArrayNode("ar1", Shape(3, 1), [
            LiteralNode("tmp2", 1),
            LiteralNode("tmp3", 2),
            LiteralNode("tmp4", 3)
        ]),
        ((1, 2), (0, 1))
    )
    assert get_collapsed_result(node) == 2
