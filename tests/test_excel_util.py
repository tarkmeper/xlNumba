import pytest
import openpyxl

from pyxloptimizer.excel_reference import ExcelReference


@pytest.fixture(scope='module')
def xl(request):
    return openpyxl.load_workbook('tests/fixtures/basic.xlsx')


def test_cell_reference(xl):
    reference = ExcelReference(xl, 'A4')
    assert reference._ref_type == ExcelReference.ReferenceType.CELL


def test_range_reference(xl):
    reference = ExcelReference(xl, '$A3:B$4')
    assert reference._ref_type == ExcelReference.ReferenceType.RANGE


def test_range_reference_cells(xl):
    reference = ExcelReference(xl, '$A3:B$4')
    reference.get_cells()
