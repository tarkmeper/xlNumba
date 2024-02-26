import openpyxl
import pytest

from pyxloptimizer import Compiler, logger
from pyxloptimizer.nodes import LiteralNode, wrap_output
from pyxloptimizer.optimizations import collapse_literals


def get_collapsed_result(node):
    out_node = wrap_output("dst", node)
    collapsed_node = collapse_literals([("N/A", out_node)])[0][1]

    assert len(collapsed_node.children) == 1
    child = collapsed_node.children[0]
    assert isinstance(child, LiteralNode)
    return child.value  # Output node -> ast.Constant -> value


def default_test(xls_sheet, sheet, row, expected_result, disable_numba=False):
    """
    Most basic of test cases - ensure that a simple formula can be processed, and produce a result
    given an input.
    """
    ctx = Compiler(xls_sheet)
    ctx.add_input("src", f"{sheet.title}!B{row}")
    ctx.add_output("dst", f"{sheet.title}!C{row}")
    fn = ctx.compile(disable_numba=disable_numba)
    result = fn()
    logger.debug("Result was %s with dst value of %s and expected value of %s", result, result['dst'], expected_result)
    if isinstance(expected_result, float):
        assert result['dst'] == pytest.approx(expected_result)
    else:
        assert result['dst'] == expected_result


def get_param_from_sheet(filename):
    """
    Given a sample xlsx sheet in our standard test format we have one test per row in the sheet that
    exists on A, with results stored in C.

    :param filename: xlsx sheet
    :return: pytest object
    """
    wb = openpyxl.load_workbook(filename, read_only=True, data_only=True)

    results = []
    for sheet in wb.worksheets:
        for idx in range(2, sheet.max_row + 1):
            if sheet[f"A{idx}"].value:
                param = pytest.param(sheet, idx, sheet[f"C{idx}"].value, id=f"{sheet.title}_{sheet[f"A{idx}"].value}")
                results.append(param)

    return results
