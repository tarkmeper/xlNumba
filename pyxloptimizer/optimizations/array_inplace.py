from ..nodes.node import Node
from ..nodes import Graph, FunctionOpNode
from ..logger import logger


def array_inplace(graph: Graph):
    """
    This optimization checks for functions that are called which have only one parent and leveraging Numpy inplace
    functionality would allow to avoid extra memory allocation and copying of data.

    In Excel this can happen fairly commonly when array functions are used for example POWER(SIN(A1:A10), 2) the sin
    function can safely be executed in place past up.

    Depth first search is executed looking for any functions with only one parent, and where the function details
    would enable in_place operation.
    """
    visited = set()
    for name, node in graph:
        if node not in visited:
            _exec_recursive(node, visited)
    return graph


def _exec_recursive(node: Node, visited: set[Node]):
    if node in visited:
        return

    visited.add(node)
    for child in node.children:
        _exec_recursive(child, visited)

    # function that takes an array node as a parameter
    if isinstance(node, FunctionOpNode) and node.in_place_supported:
        logger.debug("Function node %s will execute in place", node)
        node.in_place = True
