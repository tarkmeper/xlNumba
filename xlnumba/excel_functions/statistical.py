"""
Helper functions for implementing Excel stastical functions.
"""
import numpy as np
from numba import jit_module


def large(arr, k):
    tmp = arr.reshape(-1)
    return np.partition(tmp, -k)[-k]


def small(arr, k):
    tmp = arr.reshape(-1)
    return np.partition(tmp, k)[k - 1]


def _ifs_reduce(arr, invalid, *args):
    """
    This is somewhat fun - similar to C++ meta programming numba has issues applying the where clause directly to
    the array.  Instead, we use a recursive technique to create a new version of the function stripping off the last
    two arguments.

    >>> _ifs_reduce.py_func([1,2], 10, np.array([5, 3]), 3)
    array([10,  2])

    >>> _ifs_reduce.py_func([1,2], 10, np.array([5, 3]), 3, np.array([2,2]), 2)
    array([10,  2], dtype=int64)

    :param arr:  Input array
    :param invalid: Entry to put to the array when invalid
    :param args: Remaining args
    :return: New array with any items that do not match condition being set to invalid.
    """
    tmp = np.where(args[0] == args[1], arr, invalid)
    if len(args) >= 4:
        tmp = _ifs_reduce(tmp, invalid, *(args[2:]))
    return tmp


def maxifs(arr, *args):
    tmp = _ifs_reduce(arr, -1 * np.inf, *args)
    return np.max(tmp)


def minifs(arr, *args):
    tmp = _ifs_reduce(arr, np.inf, *args)
    return np.min(tmp)


def average_ifs(arr, *args):
    tmp_s = _ifs_reduce(arr, 0, *args)
    tmp_c = _ifs_reduce(arr, np.inf, *args)
    s = np.sum(tmp_s)
    c = np.count_nonzero(tmp_c != np.inf)
    return s / c


def geo_mean(arr):
    return arr.prod() ** (1.0 / arr.size)


def harmonic_mean(arr):
    inner = np.sum(np.reciprocal(arr)) / arr.size
    return 1 / inner


def trim_mean(arr, percent):
    k = int(arr.size * percent / 2)
    return np.mean(np.sort(arr.reshape(-1))[k:-k])


jit_module(nopython=True, fastmath=True)
