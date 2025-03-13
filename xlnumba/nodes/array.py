import ast
from abc import ABCMeta

from .literal import LiteralNode
from .node import Node
from ..ast import ast_call, ast_tuple
from ..excel_reference import DataType
from ..exceptions import UnsupportedException
from ..shape import Shape

# Todo - this hard codes maximum string length at 25 characters which is likely not what we really want to do.
STR_DTYPE = ast.keyword(arg='dtype', value=ast.Constant(value='<U25'))


class BaseArrayNode(Node, metaclass=ABCMeta):
    """
    Base class to represent array nodes, provides some common capabilities around determining the type of the array
    and automatically replacing any blank nodes.
    """

    def __init__(self, variable_name: str, children: list[Node]):
        super().__init__(variable_name, children)

        # replace blank nodes with the default value for array type
        default_node = LiteralNode(variable_name + "_d", '' if self.data_type == DataType.String else 0)
        for idx in range(0, len(children)):
            if children[idx].data_type == DataType.Blank:
                children[idx] = default_node

    @property
    def data_type(self):
        """
        Determine the data type of the array but iterating through all the elements and detemring what type they
        can be.
        """
        data_type = DataType.Blank
        for child in self._children:
            if data_type == DataType.Blank:
                data_type = child.data_type
            elif child.data_type == DataType.Blank:
                pass  # can skip this child.
            elif data_type != child.data_type:
                raise UnsupportedException(f"Array contains unsupported mixed types: {data_type} and {child.data_type}")
        if data_type == DataType.Blank:
            raise UnsupportedException("All elements in array are blank.  Cannot deduce data type")
        return data_type

    def __repr__(self):
        return f"AN:{self._var}"


class FlatArrayNode(BaseArrayNode):
    """
    Flat arrays represent situations where many variables need to be joined into a single array argument for a
    function such as "SUM" which take a variable number of arguments.  All inputs are flattened and merged to allow
    for differing sizes of arrays to be handled.
    """

    @property
    def shape(self):
        return Shape(sum([x.shape.size for x in self._children]), 1)

    @property
    def ast(self):
        if self.data_type == DataType.String:
            array_arg = ast_call('numpy.empty', [ast.Constant(self.shape.size)], [STR_DTYPE])
            children_ref = [child.ref for child in self._children]
            call = ast_call('special.create_string_array', [array_arg] + children_ref)
            return self._ast_wrap(call)

        values = []
        last_list = None

        # now the annoying part if we need to merge all the arrays together.
        for child in self._children:
            if not child.shape.is_scalar:
                values.append(child.ref)
                last_list = None
            elif last_list is None:
                last_list = ast_call('numpy.array', [ast.List(elts=[child.ref], ctx=ast.Load())])
                values.append(last_list)
            else:
                last_list.args[0].elts.append(child.ref)

        if len(values) == 1:
            call = values[0]
        else:
            # Must use pair-wise append because numba doesn't support the list ammend version in numpy.
            call = values[-1]
            for val in reversed(values[:-1]):
                call = ast_call('numpy.append', args=[val, call])
        return self._ast_wrap(call)


class ExcelArrayNode(BaseArrayNode):
    """
    Excel Array's represent a range in Excel.  They are always stored as 2D arrays with the dimension maching the
    range in Excel.
    """

    def __init__(self, variable_name: str, shape: Shape, children: list[Node]):
        assert shape is not None
        super().__init__(variable_name, children)
        self._shape = shape

    def __repr__(self):
        return f"EAN:{self._var}"

    @property
    def shape(self):
        return self._shape

    @property
    def ast(self):
        if self.data_type == DataType.String:
            array_arg = ast_call('numpy.empty', [ast.Constant(self.shape.size)], [STR_DTYPE])
            children_ref = [child.ref for child in self._children]
            call = ast_call('special.create_string_array', [array_arg] + children_ref)
        else:
            args = [ast.List(elts=[child.ref for child in self._children], ctx=ast.Load())]
            call = ast_call('numpy.array', args)

        reshape_call = ast_call(ast.Attribute(call, 'reshape', ctx=ast.Load()), [self.shape.ast])
        return self._ast_wrap(reshape_call)


class IndexNode(Node):
    """
    Take slices out of an array node object.  This is primarily used to reference a slice of an array function
    during calculation.
    """

    def __init__(self, variable_name: str, array_node: Node, idx):
        super().__init__(variable_name, [array_node])
        self._idx = idx

    @property
    def array(self):
        return self._children[0]

    @property
    def shape(self):
        return Shape(self._idx[0][1] - self._idx[0][0], self._idx[1][1] - self._idx[1][0])

    @property
    def data_type(self):
        return self.array.data_type

    @property
    def ref(self):
        """
        Set the reference to be the subscipt itself.  This eliminates the need for a line just to dereference
        the range and instead puts it directly into the appropriate function making code a bit easier to read.
        """
        return ast.Subscript(value=self.array.ref, slice=self._ast_from_idx(), ctx=ast.Load())

    @property
    def ast(self):
        return None

    def __repr__(self):
        return f"{self.varname} = IDX:{self.varname}={self.array.varname}[{self._idx}]"

    def _ast_from_idx(self):
        """
        Index nodes can do two things - extract a partial range from a larger array, or extract a single element
        from an array. It must never convert a 2D array down to a 1D array as we expect all ranges in the core code
        to behave as 2D arrays.
        """
        idx = self._idx
        if (idx[0][1] - idx[0][0] == 1) and (idx[1][1] - idx[1][0] == 1):
            return ast_tuple(idx[0][0], idx[1][0])
        else:
            def helper(sub_idx, full):
                if sub_idx[1] - sub_idx[0] == full:
                    return ast.Slice(None, None)
                else:
                    return ast.Slice(ast.Constant(sub_idx[0]), ast.Constant(sub_idx[1]))

            col_slice = helper(idx[0], self.array.shape.width)
            row_slice = helper(idx[1], self.array.shape.height)

            return ast_tuple(col_slice, row_slice)
