import builtins
import math

import numpy as np
import scipy as scipy

from . import information, text, statistical, logical, special, mathematical, lookup, user_functions
from .function_details import Function, ConstantFunction, NumpyUFunction, ScalarFunction, AggregatingFunction, \
    UnsupportedFunction, numba_disabled, xjit
from .logical import IfsFunction, SwitchFunction
from .lookup import Lookup
from ..exceptions import UnsupportedException
from ..logger import logger
from ..shape import SCALAR_SHAPE

# Helpful listing of Excel functions
# https://www.excelfunctions.net/excel-functions-list.html

######################################
#           Internal Utility Functions
######################################
INTERNAL_CONCAT = ScalarFunction(text.bin_op_concat)
RECIPROCAL = NumpyUFunction(np.reciprocal)

######################################
#       Aggregation Operators
######################################

AVERAGE = AggregatingFunction(np.mean)
AVERAGEA = UnsupportedFunction(UnsupportedFunction.MULTIPLE_TYPES)
AVERAGEIF = Function(statistical.average_ifs, shape=SCALAR_SHAPE).reorder_inputs([2, 0, 1])
#AVERAGEIFS = numba_disabled(Function(statistical.average_ifs, shape=SCALAR_SHAPE))
MEDIAN = AggregatingFunction(np.median)
# MODE = UnsupportedFunction(UnsupportedFunction.)
# MODE.SNGL = UnsupportedFunction(UnsupportedFunction.NUMBA_UNSUPPORTED)
# MODE.MULTIPLE_TYPES = UnsupportedFunction(UnsupportedFunction.NUMBA_UNSUPPORTED)
GEOMEAN = AggregatingFunction(statistical.geo_mean)
HARMEAN = AggregatingFunction(statistical.harmonic_mean)
TRIMMEAN = Function(statistical.trim_mean, shape=SCALAR_SHAPE)

######################################
#       Bases
######################################
BIN2DEC = numba_disabled(ScalarFunction(mathematical.base_repr).append(2))
HEX2DEC = numba_disabled(ScalarFunction(mathematical.base_repr).append(16))
OCT2DEC = numba_disabled(ScalarFunction(mathematical.base_repr).append(8))

BIN2HEX = numba_disabled(ScalarFunction(np.base_repr).chain(BIN2DEC).append(16))
BIN2OCT = numba_disabled(ScalarFunction(np.base_repr).chain(BIN2DEC).append(8))
DEC2BIN = numba_disabled(Function(np.base_repr).append(2))
DEC2HEX = numba_disabled(Function(np.base_repr).append(16))
DEC2OCT = numba_disabled(Function(np.base_repr).append(8))
HEX2BIN = numba_disabled(ScalarFunction(np.base_repr).chain(HEX2DEC).append(2))
HEX2OCT = numba_disabled(ScalarFunction(np.base_repr).chain(HEX2DEC).append(8))
OCT2BIN = numba_disabled(ScalarFunction(np.base_repr).chain(OCT2DEC).append(2))
OCT2HEX = numba_disabled(ScalarFunction(np.base_repr).chain(OCT2DEC).append(16))

######################################
#       Boolean Operator
######################################
AND = AggregatingFunction(np.all, return_type=bool)
OR = AggregatingFunction(np.any, return_type=bool)
NOT = AggregatingFunction(np.logical_not, return_type=bool)
XOR = AggregatingFunction(logical.excel_xor, return_type=bool)

######################################
#           CONDITIONAL OPERATORS
######################################
IF = Function(np.where)
IFERROR = UnsupportedFunction(UnsupportedFunction.ERROR_CODE)
IFNA = UnsupportedFunction(UnsupportedFunction.ERROR_CODE)
IFS = IfsFunction(logical.ifs_impl)
SWITCH = SwitchFunction(logical.switch_impl)

######################################
#           Constant Value
######################################
TRUE = ConstantFunction(True)
FALSE = ConstantFunction(False)

######################################
#           Information
######################################
ISNUMBER = information.DataTypeFunction("NUMBER")
ISEVEN = Function(mathematical.is_even, return_type=bool)
ISODD = Function(mathematical.is_odd, return_type=bool)
N = UnsupportedFunction(UnsupportedFunction.MULTIPLE_TYPES)
ISBLANK = information.DataTypeFunction("BLANK")
ISTEXT = information.DataTypeFunction("TEXT")
ISNONTEXT = information.DataTypeFunction("NONTEXT")
TYPE = information.DataTypeFunction("TYPE")

######################################
#       Lookup Operators
######################################
CHOOSE = AggregatingFunction(lookup.choose, 1)
HLOOKUP = Lookup(Lookup.Mode.HORIZONTAL)
VLOOKUP = Lookup(Lookup.Mode.VERTICAL)
LOOKUP = Lookup(Lookup.Mode.DETECT)

######################################
#       Math Operators
######################################
SUM = AggregatingFunction(np.sum)
PRODUCT = AggregatingFunction(np.prod)
POWER = NumpyUFunction(np.power)
SQRT = AggregatingFunction(np.sqrt)
QUOTIENT = NumpyUFunction(np.floor_divide)
MOD = NumpyUFunction(np.mod)

SUMPRODUCT = Function(mathematical.sumproduct, shape=SCALAR_SHAPE)
SUMSQ = AggregatingFunction(np.sum).chain(NumpyUFunction(np.power).append(2))
SUMX2MY2 = Function(mathematical.sumx2my2, shape=SCALAR_SHAPE)
SUMXMY2 = Function(mathematical.sumxmy2, shape=SCALAR_SHAPE)
SERIESSUM = Function(mathematical.sumseries, shape=SCALAR_SHAPE)

ABS = NumpyUFunction(np.abs)
SIGN = NumpyUFunction(np.sign)
GCD = NumpyUFunction(np.gcd)
LCM = NumpyUFunction(np.lcm)

BASE = numba_disabled(Function(np.base_repr))
DECIMAL = numba_disabled(ScalarFunction(mathematical.base_repr))
COMBIN = numba_disabled(Function(scipy.special.comb))
COMBINA = numba_disabled(Function(statistical.combina).append([False, True]))

FACT = numba_disabled(Function(scipy.special.factorial))
FACTDOUBLE = numba_disabled(Function(scipy.special.factorial2))
MULTINOMIAL = numba_disabled(AggregatingFunction(mathematical.multinomial))

######################################
#           Matrix Functions
######################################
MMULT = Function(np.dot).cast_inputs(np.float64)  # numba matrix mult only works on floats.

TRANSPOSE = Function(np.transpose)

######################################
#           RAND FUNCTIONS
######################################
# due to the array behaviour of random functions they are all handed by special functions.

######################################
#           Small and Large
######################################
MAX = AggregatingFunction(np.max)
MAXA = UnsupportedFunction(UnsupportedFunction.MULTIPLE_TYPES)
MAXIFS = Function(statistical.maxifs, shape=SCALAR_SHAPE)
MIN = AggregatingFunction(np.min)
MINA = UnsupportedFunction(UnsupportedFunction.MULTIPLE_TYPES)
MINIFS = Function(statistical.minifs, shape=SCALAR_SHAPE)
LARGE = ScalarFunction(statistical.large, iteration_idx=1)
SMALL = ScalarFunction(statistical.small, iteration_idx=1)

######################################
#           Text Functions
######################################
CEILING = NumpyUFunction(mathematical.ceil).append(0)
CEILING_x_PRECISE = CEILING
ISO_x_CEILING = CEILING
CEILING_x_MATH = CEILING
EVEN = NumpyUFunction(mathematical.ceil).append([2, 1])  # round to nearest even rounding out.
FLOOR = NumpyUFunction(mathematical.floor).append(0)
FLOOR_x_PRECISE = FLOOR
FLOOR_x_MATH = FLOOR
INT = NumpyUFunction(mathematical.ceil).append([1, 1])
MROUND = NumpyUFunction(mathematical.ceil).append(1)
ODD = NumpyUFunction(mathematical.odd)
ROUND = NumpyUFunction(np.round)
ROUNDUP = NumpyUFunction(mathematical.roundup)
ROUNDDOWN = NumpyUFunction(np.round)
TRUNC = ROUNDDOWN

######################################
#           Text Functions
######################################
CLEAN = ScalarFunction(text.clean)
TRIM = ScalarFunction(text.trim)
LEN = ScalarFunction(builtins.len)
FIND = ScalarFunction(text.find)
SEARCH = ScalarFunction(text.search, iteration_idx=[0, 1])
EXACT = ScalarFunction(text.equal, iteration_idx=[0, 1])
T = UnsupportedFunction(UnsupportedFunction.COMPILE_TIME_TYPES)

LOWER = numba_disabled(ScalarFunction(str.lower))
UPPER = numba_disabled(ScalarFunction(str.upper))
PROPER = numba_disabled(ScalarFunction(str.title))

CHAR = ScalarFunction(builtins.chr)
CODE = ScalarFunction(builtins.ord)
UNICHAR = CHAR
UNICODE = CODE

VALUE = numba_disabled(ScalarFunction(builtins.float))
CONCAT = AggregatingFunction(text.concat)
CONCATENATE = CONCAT
LEFT = ScalarFunction(text.left)
MID = ScalarFunction(text.mid)
RIGHT = ScalarFunction(text.right)
TEXTJOIN = numba_disabled(AggregatingFunction(text.textjoin, aggregation_idx=2))

REPLACE = ScalarFunction(text.replace)
SUBSTITUTE = ScalarFunction(text.substitute)

######################################
#           Trigonometry
######################################
PI = ConstantFunction(math.pi)
SQRTPI = Function(mathematical.sqrt_pi)
DEGREES = NumpyUFunction(np.rad2deg)
RADIANS = NumpyUFunction(np.deg2rad)
COS = NumpyUFunction(np.cos)
ACOS = NumpyUFunction(np.arccos)
COSH = NumpyUFunction(np.cosh)
ACOSH = NumpyUFunction(np.arccosh)
SEC = NumpyUFunction(np.reciprocal).chain(COS)
SECH = NumpyUFunction(np.reciprocal).chain(COSH)
SIN = NumpyUFunction(np.sin)
SINH = NumpyUFunction(np.sinh)
ASIN = NumpyUFunction(np.arcsin)
ASINH = NumpyUFunction(np.arcsinh)
CSC = NumpyUFunction(np.reciprocal).chain(SIN)
CSCH = NumpyUFunction(np.reciprocal).chain(SINH)
TAN = NumpyUFunction(np.tan)
TANH = NumpyUFunction(np.tanh)
ATAN = NumpyUFunction(np.arctan)
ATAN2 = Function(np.arctan2).cast_inputs(np.float64).reorder_inputs([1, 0])
COT = NumpyUFunction(np.reciprocal).chain(TAN)
COTH = NumpyUFunction(np.reciprocal).chain(TANH)
ACOT = NumpyUFunction(np.arctan).chain(RECIPROCAL)
ACOTH = NumpyUFunction(np.arctanh).chain(RECIPROCAL)

# this is somewhat hacky approach - but enables quickly adding the Excel name to each function object.
for itm in globals().copy():
    val = globals()[itm]
    if isinstance(val, Function):
        val.excel_name = itm


def find_function_details(fn_name: str) -> Function:
    """
    Return details for given function name based on this object.
    """
    fns = globals()

    if fn_name not in fns:
        raise NotImplementedError(f"Excel function name {fn_name} has not been implemented")

    fn_details = fns[fn_name]
    if isinstance(fn_details, UnsupportedFunction):
        raise UnsupportedException(f"Function {fn_name} is not supported, with reason {fn_details.reason}")

    return fn_details


def xlnumba_function(name):
    """
    Decorator to create custom-user functions external to the library. These functions are registered into the
    normally empty "user functions" module but otherwise behave the same as existing functions.
    """

    def decorator(fn):
        cmp_fn = xjit(fn)
        cmp_fn.__module__ = 'user_functions'
        logger.debug(f"Registering custom user function {name} with {cmp_fn.__module__}:{cmp_fn.__name__}")

        assert not hasattr(user_functions, fn.__name__)
        setattr(user_functions, fn.__name__, cmp_fn)
        globals()[name] = Function(cmp_fn)
        return fn

    return decorator
