import numpy
import openpyxl
import pytest
from numba import jit

from xlnumba import Compiler

FILE_NAME = 'tests/fixtures/random.xlsx'


@pytest.fixture(scope='module')
def xlsx_sheet(request):
    return openpyxl.load_workbook(FILE_NAME)


def test_basic_random_single_value(xlsx_sheet):
    """
    Test that at is most basic level random numbers are working.
    """
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("src", "A1")
    ctx.add_output("dst", "A2")
    fn = ctx.compile(disable_numba=True)
    result = fn()
    val = result['dst']
    assert val >= 1.0 and val <= 2.0


@jit
def set_seed(seed):
    numpy.random.seed(seed)


def test_basic_random_numba_seed(xlsx_sheet):
    """
    Test that at is most basic level random numbers are working.  Note that this hard codes a random number, not sure
    if this will work on any other machines even with the same seed; be curious about that fact.
    """
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("src", "A1")
    ctx.add_output("dst", "A2")
    fn = ctx.compile()
    set_seed(12)
    result = fn()
    val = result['dst']
    assert float(val) == pytest.approx(1.15416284)


def test_basic_random_between_single_value(xlsx_sheet):
    """
    Test that at is most basic level random numbers are working.  Note that this hard codes a random number, not sure
    if this will work on any other machines even with the same seed; be curious about that fact.
    """
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("src", "A1")
    ctx.add_output("dst", "A3")
    fn = ctx.compile(disable_numba=True)
    result = fn()
    val = int(result['dst'])
    assert 4 <= val <= 10


def test_random_range(xlsx_sheet):
    """
    Test that a random
    """
    ctx = Compiler(xlsx_sheet)
    ctx.add_input("src", "B1")
    ctx.add_output("dst", "C1:C10")
    fn = ctx.compile(disable_numba=True)
    result = fn()
    for idx, x in enumerate(result["dst"], start=1):
        assert idx <= x <= idx + 1
