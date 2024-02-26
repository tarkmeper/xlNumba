import openpyxl
import pytest

from pyxloptimizer import Compiler


@pytest.fixture(scope='module')
def xlsx_sheet(request):
    return openpyxl.load_workbook('tests/fixtures/basic.xlsx')


def test_setup():
    """
    Most basic of test cases - ensure that a simple formula can be processed, and produce a result
    given an input.
    """
    ctx = Compiler('tests/fixtures/basic.xlsx')
    ctx.add_input("src", "A1")
    ctx.add_output("dst", "B1")
    fn = ctx.compile()
    result = fn(src=2)
    assert result == {'dst': 3}


def test_generate_code(xlsx_sheet):
    """
    Most basic of test cases - ensure that a simple formula can be processed, and produce a result
    given an input.
    """
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("src", "A1")
    ctx.add_output("dst", "B1")
    fn = ctx.generate_code(disable_optimizations=True)
    expected = """
@numba.jit(nopython=True, fastmath=True, nogil=True)
def compiled_function(src=4):
    sheet1_b1_2 = src + 1
    return {'dst': sheet1_b1_2}"""
    assert fn.strip() == expected.strip()


def test_input_default(xlsx_sheet):
    """
    Test that when an input is not specified for a function the default value is used.
    """
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("src", "A1")
    ctx.add_output("dst", "B1")
    fn = ctx.compile(disable_numba=True)
    result = fn()
    assert result == {'dst': 5}


def test_function(xlsx_sheet):
    """
    Test that an Excel formula can be used and converted to a Python formula.
    """
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("base", "A2")
    ctx.add_input("exp", "B2")
    ctx.add_output("dst", "C2")
    fn = ctx.compile(disable_numba=True)
    result = fn(base=3, exp=4)
    assert result == {'dst': 3 ** (4 + 1)}


def test_named_cells(xlsx_sheet):
    """
    Test that named cells work the same way as the explicit reference to those cells
    """
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("src", "Input")
    ctx.add_output("dst", "Output")
    fn = ctx.compile(disable_numba=True)
    result = fn(src=2)
    assert result == {'dst': 3}


def test_sheet_name(xlsx_sheet):
    """
    Test that named cells work the same way as the explicit reference to those cells
    """
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("src", "'Sheet'Name ! Test'!A1")
    ctx.add_output("dst", "'Sheet'Name ! Test'!B1")
    fn = ctx.compile(disable_numba=True)
    result = fn(src=2)
    assert result == {'dst': 3}


def test_formula_input(xlsx_sheet):
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("src", "Sheet1!B1")
    ctx.add_output("dst", "Sheet1!C1")
    fn = ctx.compile(disable_numba=True)
    result = fn(src=2)
    assert result == {'dst': 4}
