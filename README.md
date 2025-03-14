# xlNumba

xlNumba is utility to convert Excel spreadsheets into optimized Python code using Numba.  This idea is to enable taking 
complex models built in Excel and converting them into high-performance Python code.

This library does not attempt to provide full Excel compatability.  Instead it focusses on providing a subset of capabilities
which can be compiled by Numba and optimized to provide high-performance execution.

In general numerical (and in the future date) related functions are supported while text functions have very limited 
support.  Excel has some fairly complex exception handling and type coercion rules which are not supported. 


## Basic Example

```
from xlnumba import Compiler

ctx = Compiler("tests/fixtures/basic")
ctx.add_input('Raw', 'A1')
ctx.add_output('Adjusted', 'B1')
fn = ctx.compile()
adjusted = fn(Raw=3.0)
```


## User Defined Functions example.

User defined functions can be created using the `@xlnumba_function` decorator. This decorator takes the name of the 
excel function.  Note that the function must be numba compilable. 

```
@xlnumba_function("EXCEL_FNC_NAME")
def custom_func(x):
    return 3 * x + 5
```

## Acknowledgements

The original idea for this was inspired from the excellent [pycel](https://github.com/dgorissen/pycel) library.