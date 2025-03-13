from xlnumba import xlnumba_function
from xlnumba.excel_functions import find_function_details
from xlnumba.nodes import LiteralNode, FunctionOpNode
from .util import get_collapsed_result


@xlnumba_function("TEST_CUSTOM_FUNC")
def custom_func(x):
    return 3 * x + 5


def test_compile_custom_functions():
    fn_details = find_function_details('TEST_CUSTOM_FUNC')
    # Test that the optimization collapses literals in a function call.
    node = FunctionOpNode(
        "tmp1",
        fn_details,
        [
            LiteralNode("tmp5", 1),
        ])
    assert get_collapsed_result(node) == 8
