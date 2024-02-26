import numpy as np

from .function_details import BaseFunction, xjit
from ..excel_reference import DataType
from ..nodes import RandBetweenNode
from ..shape import Shape


@xjit
def random_between_operator(width: int, height: int, low: int, high: int):
    return np.random.randint(low, high, (width, height))


class RandomBetweenFunction(BaseFunction):
    """
    Function to compute random numbers - this woould be relatively simple except for one thing - Excel has an
    "interesting" behaviour on random numbers between how it works on a standalone basis and in an array formula.

    "Dynamic" arrays in Excel [those that are defined as an array functio and can spill over ] make sure of a single
    value of the  random variable, while when used as an array function (i.e. a function surrounded by squigly marks
    and ctrl+shift+enter will use a different rand value for each entry).

    Given that dynamic arrays are new and OpenPyxl doesn't really support them - we can't identify them and so
    the random function instead produces a different random value for each case.
    """

    def __init__(self, shape: Shape):
        super().__init__()
        self._shape = shape
        self.excel_name = 'rand_between'

    def prepare_function(self, idx_gen, args):
        assert len(args) == 2
        node = RandBetweenNode(idx_gen(), args[0], args[1], self._shape)
        return node

    def compute_shape(self, children):
        return self._shape

    def compute_resulting_type(self, children) -> DataType:
        return DataType.Number
