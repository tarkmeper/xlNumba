"""
Helper functions for the Excel Text functions.
"""
import numpy

from .function_details import xjit


@xjit
def clean(val: str):
    return "".join(filter(lambda x: ord(x) > 0, val))


@xjit
def trim(val: str):
    return ' '.join(filter(lambda x: len(x) > 0, val.split(' ')))


@xjit
def search(val: str, target: str, start=0):
    return target.upper().find(val.upper(), start) + 1


@xjit
def find(val: str, target: str, start=0):
    return target.find(val, start) + 1


@xjit
def equal(val: str, target: str):
    return val == target


@xjit
def bin_op_concat(left_s, right_s):
    return str(left_s) + str(right_s)


@xjit
def concat(arr):
    return "".join(arr.reshape(-1))


@xjit
def left(val, num):
    return val[:num]


@xjit
def mid(val, start, num):
    return val[start - 1:start + num - 1]


@xjit
def right(val, num):
    return val[-1 * num:]


@xjit
def textjoin(delim, skip, arr):
    """
    >>> textjoin.py_func(',', False, numpy.array(['a','b','','c']))
    'a,b,,c'

    >>> textjoin.py_func(',', True, numpy.array(['a','b','','c']))
    'a,b,c'
    """
    if skip:
        return delim.join(filter(lambda x: len(x) > 0, arr.reshape(-1).tolist()))
    else:
        return delim.join(arr.reshape(-1).tolist())


@xjit
def replace(s, start, end, new):
    return s[:start - 1] + new + s[end + 1:]


@xjit
def substitute(s: str, find_t: str, new: str):
    return s.replace(find_t, new)
