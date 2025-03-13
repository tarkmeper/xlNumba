class UnsupportedBroadcastException(Exception):
    """
    This exception gets thrown when two incompatible shapes are broadcast together.  The usual reason for this
    would be errors on the Excel sheet, which were then passed into the compiler.
    """
    pass


class InvalidExcelReferenceException(Exception):
    """
    This exception is thrown when an invalid reference is passed as an input or output parameter to the compiler.
    It can also be used when an addressing function is called with an invalid compile time value.
    """
    pass


class UnsupportedException(Exception):
    """
    This exception is thrown when a function is not supported by the compiler.  This could be due to the function
    being unsupported by Numba, or due to usage of dynamic location/type information.
    """
    pass
