import pytest
import openpyxl

from .util import get_param_from_sheet, default_test
import pyxloptimizer.excel_functions as excel_functions
from pyxloptimizer import UnsupportedException

FILE_NAME = 'tests/fixtures/functions.xlsx'


@pytest.fixture(scope='module')
def xls_sheet(request):
    return openpyxl.load_workbook(FILE_NAME)


@pytest.mark.parametrize("sheet, row, expected_result", get_param_from_sheet(FILE_NAME))
@pytest.mark.parametrize("disable_numba",
                         [True, False],  # order is important.  Want first to test functionality, then numba compile
                         ids=['python', 'numba']
                         )
def test_function(xls_sheet, sheet, row, expected_result, disable_numba):
    fn_name = xls_sheet[sheet.title][f"A{row}"].value
    if hasattr(excel_functions, fn_name):
        fn_obj = getattr(excel_functions, fn_name)
        if not disable_numba and hasattr(fn_obj, 'underlying_fnc_str'):
            with pytest.raises(UnsupportedException):
                default_test(xls_sheet, sheet, row, expected_result, disable_numba=disable_numba)
            return
    default_test(xls_sheet, sheet, row, expected_result, disable_numba=disable_numba)
