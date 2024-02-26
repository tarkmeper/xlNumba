import numpy
from .function_details import xjit


@xjit
def create_string_array(arr, *args):
    """
    >>> create_string_array.py_func(numpy.empty(4, dtype='U4'), 'a', 'b', None, 'd')
    array(['a', 'b', '', 'd'], dtype='<U4')
    """
    for i in range(len(args)):
        if args[i] is None:
            arr[i] = ""
        else:
            arr[i] = args[i]
    return arr
