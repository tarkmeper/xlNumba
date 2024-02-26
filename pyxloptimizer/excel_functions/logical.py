import numpy as np

from .function_details import Function, xjit
from ..nodes import Node, FlatArrayNode
from ..shape import SCALAR_SHAPE


@xjit
def excel_xor(arr):  # xor is defined as number of true values is odd
    return np.count_nonzero(arr) % 2 == 1


@xjit
def ifs_impl(conds, values):
    for c, vals in zip(conds, values):
        if c:
            return vals
    raise NotImplementedError("Ifs must return valid entry")


class IfsFunction(Function):
    """
    Excel makes use of alternating arguments, in the case of IFs a boolean and then a value.  Numba can't support that
    so instead in the translation we group all the boolean values and all the resulting values into two lists which can
    then be used in a Python or a numba accelerated function.

    Todo: This could be significantly accelerated by using teh same approach with use for "if" where we build
    a conditional accelerator.  That approach would not work with array arguments.
    """

    def prepare_function(self, idx_gen, children):
        first_args = FlatArrayNode(idx_gen(), children[::2])
        second_args = FlatArrayNode(idx_gen(), children[1::2])

        return super().prepare_function(idx_gen, [first_args, second_args])

    def compute_shape(self, args: list[Node]):
        if isinstance(args[1], FlatArrayNode):
            return args[1].children[0].shape
        else:
            # this could also be an array if we are copresing literal.
            return SCALAR_SHAPE


@xjit
def switch_impl(expr, conds, values):
    for c, vals in zip(conds, values):
        if c == expr:
            return vals
    raise NotImplementedError("Invalid switch function")


class SwitchFunction(Function):
    """
    See IFS above for idea.
    """

    def prepare_function(self, idx_gen, args):
        first_args = FlatArrayNode(idx_gen(), [x for x in args[1::2]])
        second_args = FlatArrayNode(idx_gen(), [x for x in args[2::2]])

        return super().prepare_function(idx_gen, [args[0], first_args, second_args])

    def compute_shape(self, args: list[Node]):
        if isinstance(args[2], FlatArrayNode):
            return args[2].children[0].shape
        else:
            # this could also be an array if we are copresing literal.
            return SCALAR_SHAPE


@xjit
def excel_if(test, true_val, false_val):
    return true_val if test else false_val
