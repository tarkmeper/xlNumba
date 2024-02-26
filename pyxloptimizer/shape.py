import ast
from collections import namedtuple

from .exceptions import UnsupportedBroadcastException


class Shape(namedtuple("ShapeTuple", ["height", "width"])):
    """
    Shape acts similar to shape in Numpy providing a bridge to Excel array shapes structures.
    """

    @property
    def is_scalar(self):
        return self == SCALAR_SHAPE

    @property
    def is_vector(self):
        """
        Is this either a horizontal or vertical vector?

        >>> Shape(1,4).is_vector
        True

        >>> Shape(3,4).is_vector
        False

        """
        return (self.width == 1 and self.height > 1) or (self.height == 1 and self.width > 1)

    @property
    def ast(self) -> ast.Tuple:
        return ast.Tuple([ast.Constant(self.height), ast.Constant(self.width)], ctx=ast.Load())

    @property
    def size(self) -> int:
        """
        Total number of elements in the shap=e

        >>> Shape(3,4).size
        12

        """
        return self.width * self.height

    @property
    def horizontal(self) -> bool:
        return self.width > 1 and self.height == 1

    @property
    def vertical(self) -> bool:
        return self.width == 1 and self.height > 1

    def merge(self, other) -> 'Shape':
        """
        Merge shapes in the Excel sense.  As long as can broadcast shapes can be merged, if they are two different
        sized 2-d arrays ( or different sized 1-d array in same direction) then cannot be merged.

        >>> Shape(2,3).merge(Shape(2,3))
        Shape(height=2, width=3)

        >>> Shape(1,4).merge(Shape(4,4))
        Shape(height=4, width=4)

        >>> SCALAR_SHAPE.merge(Shape(4,4))
        Shape(height=4, width=4)

        >>> Shape(4, 2).merge(SCALAR_SHAPE)
        Shape(height=4, width=2)

        >>> Shape(5,4).merge(Shape(4,4))
        Traceback (most recent call last):
        ...
        pyxloptimizer.exceptions.UnsupportedBroadcastException: Cannot merge shapes Shape(height=5, width=4) and \
Shape(height=4, width=4)

        """
        if self == other:
            return self
        elif self.is_scalar:
            return other
        elif other.is_scalar:
            return self
        elif other.width == self.width and (self.horizontal or other.horizontal):
            return Shape(self.width, max(self.height, other.height))
        elif other.height == self.height and (self.vertical or other.vertical):
            return Shape(max(self.width, other.width), self.height)
        elif self.is_vector and other.is_vector and self.vertical != other.vertical:
            return Shape(max(self.width, other.width), max(self.height, other.height))
        else:
            raise UnsupportedBroadcastException(f"Cannot merge shapes {self} and {other}")


SCALAR_SHAPE = Shape(1, 1)
