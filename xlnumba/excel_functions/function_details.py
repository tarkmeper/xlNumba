import abc
import builtins
import functools
from typing import Iterable

import numpy as np
from numba import jit

from ..excel_reference import DataType
from ..exceptions import UnsupportedException
from ..nodes import Node, LiteralNode, FlatArrayNode, FunctionOpNode
from ..shape import SCALAR_SHAPE

xjit = jit(nopython=True, fastmath=True)


class UnsupportedFunction:
    """
    Special class to mark Excel functions that there is no intention to support in the optimizer.
    """
    MULTIPLE_TYPES = "Do not support mixed types within single range"
    ERROR_CODE = "Relies on Excel Error Codes which are not supported"
    COMPILE_TIME_TYPES = "Types must be set at compile time, function relies on dynamic types"

    def __init__(self, reason):
        self.reason = reason


class BaseFunction(metaclass=abc.ABCMeta):
    """
    Base class for all "real" functions that will call some form of a function.
    """

    def __init__(self):
        self.excel_name = None  # this is populated later in __init__.py, it's a bit magic how this works see __init__

    @abc.abstractmethod
    def prepare_function(self, idx_gen, args):
        """
        Transform an Excel function into a Function node which will then be used to generate the structure
        of teh Python code.

        :param idx_gen: Callable for creating variable names.
        :param args: Arguments to the functions.
        :return: A node object that will either represent this function or the calculated value of the function.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def compute_shape(self, args):
        """
        :param args: Arguments.
        :return: The resulting dimensions and shape of the function based on its arguments.
        """
        pass

    def in_place_supported(self):
        """
        Some numpy functions on arrays can be applied in-place.  This can be very beneficial if there are deeply
        nexted functions on large arrays of data.

        :return: True if we can enable in palce.
        """
        return False

    @abc.abstractmethod
    def compute_resulting_type(self, args) -> DataType:
        """
        :param args: Arguments to the fucntion.
        :return: The resulting type of the function call.
        """
        pass

    def __repr__(self):
        return f"[Details:{self.excel_name}]"


class ConstantFunction(BaseFunction):
    """
    Constant functions simply return a literal value for True/False/PI etc.
    """

    def __init__(self, value=0):
        """ set default value for subclasses so that we don't need to set this"""
        super().__init__()
        self.value = value

    def prepare_function(self, idx, args):
        return LiteralNode(idx, self.value)

    def compute_shape(self, children): return SCALAR_SHAPE

    def compute_resulting_type(self, children):
        return DataType.Boolean if self.value is bool else DataType.Number


def numba_disabled(wrap):
    """
    Special class to mark Excel functions that are not supported by Numba.  This acts as a wrapper aroudn the function
    definition which throws an exception when we attempt to generate AST if this is a Numba function.
    """
    wrap.underlying_fnc_str = wrap.fnc_str

    def fnc_str(_, disable_numba):
        if not disable_numba:
            raise UnsupportedException(f"Function {wrap.underlying_fnc_str(False)} does not support numba")
        return wrap.underlying_fnc_str(disable_numba)

    wrap.fnc_str = type(wrap.fnc_str)(fnc_str, wrap)
    return wrap


class Function(BaseFunction):
    def __init__(self, func, shape=None, return_type=DataType.Number):
        super().__init__()
        self.func = func
        self.prep = []
        self.module = extract_module_name(func)

        self.shape = shape
        self.return_type = return_type

    def prepare_function(self, idx_gen, args):
        final_args = args
        for step in self.prep:
            final_args = step(idx_gen, final_args)
        node = FunctionOpNode(idx_gen(), self, final_args)
        return node

    def fnc_str(self, disable_numba):
        if disable_numba and self.module not in ['str', 'builtins', 'numpy', 'scipy.special']:
            return f"{self.module}.{self.func.__name__}.py_func"
        else:
            return f"{self.module}.{self.func.__name__}"

    def in_place_supported(self):
        return False

    def compute_resulting_type(self, _):
        return self.return_type

    def compute_shape(self, children):
        shape = children[0].shape
        if self.shape is not None:
            shape = self.shape(children) if callable(self.shape) else self.shape
        return shape

    def chain(self, other_func):
        return self._add_prep(_chain_op, other_func)

    def append(self, new_args):
        return self._add_prep(_append_op, new_args)

    def cast_inputs(self, target_type):
        return self._add_prep(_cast_inputs_op, target_type)

    def reorder_inputs(self, new_order):
        return self._add_prep(_reorder_inputs_op, new_order)

    def _add_prep(self, function, *args, **kwargs):
        func = functools.partial(function, *args, **kwargs)
        self.prep.append(func)
        return self


class NumpyUFunction(Function):
    def in_place_supported(self):
        return True


class AggregatingFunction(Function):
    """
    Aggregating functions are functions such as "SUM" that can take an entire list of values and apply a single funciton
    to all of them.  This applies a postprocessor which creates a FlatArrayNode from all the elements past
    aggregation_idx
    """

    def __init__(self, func, aggregation_idx=0, *args, **kwargs):
        super().__init__(func, shape=SCALAR_SHAPE, *args, **kwargs)
        self._add_prep(_aggregate_op, aggregation_idx)


class ScalarFunction(Function):
    """
    Scalar functions apply to asingle element at a time and require a looping algorithm to apply them to all the
    elements in an array.
    """

    def __init__(self, func, iteration_idx=0, *args, **kwargs):
        super().__init__(func, *args, **kwargs)
        self.iteration_idx = iteration_idx

    def compute_shape(self, children):
        if isinstance(self.iteration_idx, Iterable):
            shape = SCALAR_SHAPE
            for idx in self.iteration_idx:
                shape = shape.merge(children[idx].shape)
            return shape
        else:
            return children[self.iteration_idx].shape


def extract_module_name(func):
    if hasattr(np, func.__name__) and func == getattr(np, func.__name__):
        return 'numpy'
    elif hasattr(str, func.__name__) and func == getattr(str, func.__name__):
        return 'str'
    elif func.__module__.startswith('scipy'):
        return '.'.join(func.__module__.split('.')[:-1])
    else:
        return func.__module__.split(".")[-1]


def _reorder_inputs_op(idx_list, _idx_gen, args):
    assert len(args) > max(idx_list)
    original_args = args[:]
    for idx, old_idx in enumerate(idx_list):
        args[idx] = original_args[old_idx]
    return args


def _aggregate_op(aggregation_idx: int, _, args: list[Node]):
    if len(args) > aggregation_idx + 1:
        name = args[aggregation_idx].varname + "_agg"
        new_node = FlatArrayNode(name, args[aggregation_idx:])
        return args[:aggregation_idx] + [new_node]
    else:
        return args


def _chain_op(other_fn: Function, idx_gen, children):
    chain_node = other_fn.prepare_function(idx_gen, children)
    return [chain_node]


def _append_op(new_args, idx_gen, args):
    """
    This function automatically adds extra arguments to the end of the specified function.
    """
    if isinstance(new_args, (list, tuple)):  # might be a better way to do this can't apply to strings.
        args.extend([LiteralNode(idx_gen(), a) for a in new_args])
    else:
        args.append(LiteralNode(idx_gen(), new_args))
    return args


_CAST_FUNCTIONS = {
    np.float64: (ScalarFunction(builtins.float), Function(np.copy).append('float')),
}


def _cast_inputs_op(tp, idx_gen, args):
    """
    Force input parameters to specified type before calling the parent function.
    """
    scalar_details, array_details = _CAST_FUNCTIONS[tp]
    new_args = []
    for arg in args:
        fn_details = scalar_details if arg.shape.is_scalar else array_details
        new_node = FunctionOpNode(idx_gen(), fn_details, [arg])
        new_args.append(new_node)
    return new_args
