import openpyxl
import pytest

from xlnumba import Compiler
from .util import get_param_from_sheet

FILE_NAME = 'tests/fixtures/ranges.xlsx'


@pytest.fixture(scope='module')
def xls_sheet(request):
    return openpyxl.load_workbook(FILE_NAME)


@pytest.mark.parametrize("sheet, row, expected_result", get_param_from_sheet(FILE_NAME))
def test_ranges(xls_sheet, sheet, row, expected_result):
    """ standard tests to run through all the cells in the ranges.xlsx sheet"""
    ctx = Compiler(xls_sheet)
    ctx.add_input("src", f"{sheet.title}!F1")
    ctx.add_output("dst", f"{sheet.title}!B{row}")
    fn = ctx.compile(disable_numba=True)
    result = fn(src=3)
    if isinstance(expected_result, float):
        assert result['dst'] == pytest.approx(expected_result)
    else:
        assert result['dst'] == expected_result


def test_return_1d_range_ref(xls_sheet):
    ctx = Compiler(xls_sheet)
    ctx.add_input("src", "Range_1d!F1")
    ctx.add_output("dst", "Range_1d!H1#")
    fn = ctx.compile(disable_numba=True)
    result = fn(src=3)
    expected_result = [8, 14, 20, 26, 32, 38, 44, 50, 56, 62]
    assert (result['dst'] == expected_result).all()


def test_return_1d_range_element(xls_sheet):
    ctx = Compiler(xls_sheet)
    ctx.add_input("src", "Range_1d!F1")
    ctx.add_output("dst", "Range_1d!H3")
    fn = ctx.compile(disable_numba=True)
    result = fn(src=3)
    assert result['dst'] == 20


def test_return_1d_range_full(xls_sheet):
    ctx = Compiler(xls_sheet)
    ctx.add_input("src", "Range_1d!F1")
    ctx.add_output("dst", "Range_1d!H1:H10")
    fn = ctx.compile(disable_numba=True)
    result = fn(src=3)
    expected_result = [8, 14, 20, 26, 32, 38, 44, 50, 56, 62]
    assert (result['dst'] == expected_result).all()


def test_return_1d_range_partial(xls_sheet):
    ctx = Compiler(xls_sheet)
    ctx.add_input("src", "Range_1d!F1")
    ctx.add_output("dst", "Range_1d!H1:H5")
    fn = ctx.compile(disable_numba=True)
    result = fn(src=3)
    expected_result = [8, 14, 20, 26, 32]
    assert (result['dst'] == expected_result).all()
