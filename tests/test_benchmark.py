import pytest
import openpyxl

from pyxloptimizer import Compiler

from pycel import ExcelCompiler
import formulas

FILE_NAME = 'tests/fixtures/benchmark.xlsx'
EXCEL_NAME = FILE_NAME.split("/")[-1]

__idx = 1


def _next_idx():
    global __idx
    __idx += 0.0001
    return __idx


@pytest.fixture(scope='module')
def xls_sheet(request):
    return openpyxl.load_workbook(FILE_NAME)


@pytest.mark.benchmark(group="array_inplace")
@pytest.mark.parametrize(
    ['engine', 'disabled'],
    [('numba', 'array_inplace'), ('numba', False),
     ('python', 'array_inplace'), ('python', False),
     ('pycel', False),
     ],
    ids=[
        'Numba-Off', 'Numba-On',
        'Python-Off', 'Python+On',
        'Pycel',
    ]
)
def test_inplace(xls_sheet, benchmark, engine, disabled):
    _run_benchmark(
        wb=xls_sheet,
        benchmark=benchmark,
        engine=engine,
        sheet='array_inplace',
        input_cell="D1",
        output_cell="A1",
        expected_result=26.25663103,
        disable_optimizations=disabled
    )


# xlcalculator takes to long even on base evaluation and so was removed from this test.
# formulas doesn't appear to work on this case, it doesn't see the C column as an output of the input functions.

@pytest.mark.benchmark(group="merge_array")
@pytest.mark.parametrize(
    ['engine', 'disabled'],
    [('numba', 'merge_array'), ('numba', False),
     ('python', 'merge_array'), ('python', False),
     ('pycel', False),
     ],
    ids=[
        'Numba-Off', 'Numba-On',
        'Python-Off', 'Python+On',
        'Pycel',
    ]
)
def test_merge(xls_sheet, benchmark, engine, disabled):
    _run_benchmark(
        wb=xls_sheet,
        benchmark=benchmark,
        engine=engine,
        sheet='merge_array',
        input_cell="D1",
        output_cell="C20",
        expected_result=-0.761789193,
        disable_optimizations=disabled
    )


@pytest.mark.benchmark(group="lazy_conditional")
@pytest.mark.parametrize(
    ['engine', 'disabled'],
    [('numba', 'lazy_conditional'), ('numba', False),
     ('python', 'lazy_conditional'), ('python', False),
     ('pycel', False),
     ],
    ids=[
        'Numba-Lazy_Off', 'Numba-Lazy_On',
        'Python-Lazy_Off', 'Python-Lazy_On',
        'Pycel',
    ]
)
def test_lazy_conditional(xls_sheet, benchmark, engine, disabled):
    """
    This is the test of a conditional statmeent that cuts off much of logic is optimized correctly.

    Originally was going to rewrite the Python code to allow for lazy evalualtion of but wasn't implemented.
    May still look to implement at some point, where entire branch can be placed within a conditional evaluation.
    """
    _run_benchmark(
        wb=xls_sheet,
        benchmark=benchmark,
        engine=engine,
        sheet='merge_array',
        input_cell="D1",
        output_cell="H1",
        expected_result=-0.536572918,
        disable_optimizations=disabled
    )


def _run_benchmark(wb, benchmark, engine, sheet, input_cell, output_cell, expected_result, disable_optimizations=False):
    if engine == 'numba' or engine == 'python':
        ctx = Compiler(wb)
        ctx.add_input("incr", f"{sheet}!{input_cell}")
        ctx.add_output("dst", f"{sheet}!{output_cell}")
        # ctx.add_output("dst", f"{sheet}!C3")
        fn = ctx.compile(
            disable_numba=True if engine == 'python' else False,
            disable_optimizations={disable_optimizations} if disable_optimizations else False
        )
        result = fn(incr=2.000)
        assert result['dst'] == pytest.approx(expected_result)

        def runner():
            fn(incr=_next_idx())

        benchmark(runner)
    elif engine == 'pycel':
        val = ExcelCompiler(FILE_NAME)
        val.evaluate(f'{sheet}!{output_cell}')
        val.set_value(f'{sheet}!{input_cell}', 2.000)
        res = val.evaluate(f'{sheet}!{output_cell}')
        assert res == pytest.approx(expected_result)

        def runner():
            val.set_value(f'{sheet}!{input_cell}', _next_idx())
            val.evaluate(f'{sheet}!{output_cell}')

        benchmark(runner)
    elif engine == 'formulas':
        model = formulas.ExcelModel().loads(FILE_NAME).finish()
        # func = model.compile(
        #    inputs={f"'[{EXCEL_NAME}]{sheet}'!{input_cell}": 2.000},
        #    outputs=[f"'[{EXCEL_NAME}]{sheet}'!{output_cell}", ]
        # )
        results = model(2.0)
        assert results[0] == pytest.approx(expected_result)

        def runner():
            model.calculate(
                inputs={f"{sheet}!{input_cell}": _next_idx()},
                outputs=[f"{sheet}!{output_cell}"]
            )

        benchmark(runner)
