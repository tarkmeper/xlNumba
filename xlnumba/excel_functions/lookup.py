from enum import StrEnum

import numpy as np

from .function_details import xjit, Function
from ..nodes import IndexNode, FunctionOpNode


@xjit
def choose(idx, arr):
    return arr[idx - 1]


@xjit
def lookup(target, target_vector, value_vector, _approx=False):
    for t, v in zip(target_vector[0], value_vector[0]):
        if target == t:
            return v
    raise NotImplementedError("Lookups must find match to execute correctly")


class Lookup(Function):
    class Mode(StrEnum):
        HORIZONTAL = 'H'
        VERTICAL = 'V'
        DETECT = 'D'

    def __init__(self, mode: Mode):
        super().__init__(lookup)
        self.mode = mode

    def prepare_function(self, idx_gen, args):
        target = args[0]

        # determine sou*0rce and target array
        if self.mode == Lookup.Mode.DETECT:
            src_array = args[1]
            target_array = args[2]
        else:
            array = args[1]
            idx = args[2].value

            if self.mode == Lookup.Mode.HORIZONTAL:
                width = array.shape.width
                src_array = IndexNode(idx_gen(), array, [[0, 1], [0, width]])
                target_array = IndexNode(idx_gen(), array, [[idx - 1, idx], [0, width]])
            else:
                height = array.shape.height
                src_array = IndexNode(idx_gen(), array, [[0, height], [0, 1]])
                target_array = IndexNode(idx_gen(), array, [[0, height], [idx - 1, idx]])

        # make sure we have two arrays and that they make sense.
        assert src_array.shape.is_vector and target_array.shape.is_vector
        assert src_array.shape.horizontal == target_array.shape.horizontal

        if src_array.shape.vertical:
            transpose_fnc = Function(np.transpose)
            # vertical arrays need to be transposed before this will work correctly.
            src_array = FunctionOpNode(src_array.varname + "_T", transpose_fnc, [src_array])
            target_array = FunctionOpNode(target_array.varname + "_T", transpose_fnc, [target_array])

        return super().prepare_function(idx_gen, [target, src_array, target_array])
