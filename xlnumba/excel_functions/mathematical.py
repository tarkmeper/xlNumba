import math

import numpy as np
from scipy.special import factorial

from .function_details import xjit


@xjit
def sqrt_pi(arr: np.ndarray, out: np.ndarray = None):
    """
    >>> sqrt_pi.py_func(np.array([2,3]))
    array([2.50662827, 3.06998012])

    >>> y = np.array([3., 4.])
    >>> sqrt_pi.py_func(y, y)
    array([3.06998012, 3.5449077 ])

    >>> y
    array([3.06998012, 3.5449077 ])

    """
    if out is not None:
        return np.sqrt(arr * math.pi, out)
    else:
        return np.sqrt(arr * math.pi)


@xjit
def base_repr(txt, base):
    return int(str(txt), base)


@xjit
def sumproduct(a, b):
    return np.sum(a * b)


@xjit
def sumx2my2(a, b):
    return np.sum(a ** 2 - b ** 2)


@xjit
def sumxmy2(a, b):
    return np.sum((a - b) ** 2)


@xjit
def sumseries(x, n, m, a):
    """
    >>> sumseries.py_func(2,3,1,5)
    40
    """
    res = 0
    if isinstance(a, (int, float)):
        res += a * x ** n
    else:
        a_flat = a.reshape(-1)
        for i in range(a_flat.shape[0]):
            res += a_flat[i] * x ** (n + i * m)
    return res


@xjit
def multinomial(args):
    return factorial(np.sum(args)) / np.prod(factorial(args))


@xjit
def is_even(arr):
    return arr % 2 == 0


@xjit
def is_odd(arr):
    return arr % 2 == 1


@xjit
def ceil(arr, sig, mode, out=None):
    """
    >>> ceil.py_func(np.array([3.,-4.,5.]), 5, 0)
    array([ 5., -0.,  5.])

    >>> y = np.array([3.,-4.,5.])
    >>> ceil.py_func(y, 5, 1, y)
    array([ 5., -5.,  5.])

    """
    if isinstance(arr, (int, float)):
        if mode == 0:
            return sig * np.ceil(arr / sig)
        else:
            return sig * np.copysign(np.ceil(np.abs(arr) / sig), arr)
    else:
        if out is None:
            out = arr.copy()
        out /= sig
        if mode == 0:
            np.ceil(out, out)
        else:
            # away from zero rounding is a bit tricky.
            sign = np.sign(out)
            np.abs(out, out)
            np.ceil(out, out)
            np.copysign(out, sign, out)
        out *= sig
        return out


@xjit
def roundup(arr, digits, out=None):
    return ceil(arr, 1.0 / (10 ** digits), 1, out)


@xjit
def odd(arr, out=None):
    """
    >>> odd.py_func(np.array([3.,4.,5.]))
    array([3., 5., 5.])

    """
    if isinstance(arr, (float, int)):
        return ceil(arr - 1, 2.0, 1) + 1
    else:
        arr -= 1
        if out is None:
            out = arr.copy()
        ceil.py_func(arr, 2.0, 1, out)
        out += 1
        return out


@xjit
def floor(arr, sig, mode, out=None):
    """
    >>> floor.py_func(np.array([3.,-4.,5.]), 5, 0)
    array([ 0., -5.,  5.])

    >>> y = np.array([3.,-4.,5.])
    >>> floor.py_func(y, 5, 1, y)
    array([ 0., -0.,  5.])

    >>> floor.py_func(-4., 5., 1)
    -0.0

    """
    if isinstance(arr, (int, float)):
        if mode == 0:
            return sig * np.floor(arr / sig)
        else:
            return sig * np.trunc(arr / sig)
    else:
        if out is None:
            out = arr.copy()
        out /= sig
        if mode == 0:
            np.floor(out, out)
        else:
            np.trunc(out, out)
        out *= sig
        return out
