import openpyxl
import pytest

from .util import get_param_from_sheet, default_test

FILE_NAME = 'tests/fixtures/operators.xlsx'


@pytest.fixture(scope='module')
def xls_sheet(request):
    return openpyxl.load_workbook(FILE_NAME)


@pytest.mark.parametrize("sheet, row, expected_result", get_param_from_sheet(FILE_NAME))
# order is important.  Want to run Python first so that if it is broken will break before numba.
@pytest.mark.parametrize("disable_numba", [True, False], ids=['python', 'numba'])
def test_operator(xls_sheet, sheet, row, expected_result, disable_numba):
    default_test(xls_sheet, sheet, row, expected_result, disable_numba=disable_numba)
