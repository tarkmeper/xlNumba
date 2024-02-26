import numpy as np
import ast
import astor

from ..nodes import Graph, LiteralNode, IndexNode, Node
from ..execution import evaluate, get_execution_context
from ..logger import logger


def collapse_literals(graph: Graph):
    """
    Take the current graph and attempt to optimize it by collapsing any nodes which only rely on values known ahead of
    the compilation.

    For simple math nodes this likely does not serve a purpose, as the numba compiler will likely be able to do the
    same, however, in cases where multiple python function are called this enables collapsing of that logic if the
    inputs are not part of the compilers input function.
    """
    visited = set()
    for name, root in graph:
        children = list(root.children)
        for child in children:  # output nodes can't be collapsed so skip them to start the recursion.
            _exec_recursive(child, visited)
    return graph


def _exec_recursive(node: Node, visited):
    if node in visited or isinstance(node, LiteralNode) or len(node.children) == 0:
        return node
    visited.add(node)

    # Step 1 -- depth first search to see if all children of this node are literals.
    all_literal_children = True
    for child in node.children:
        child = _exec_recursive(child, visited)  # this will replace the child if it is a literal node
        if not isinstance(child, LiteralNode):
            all_literal_children = False

    # Step 2 - if all children are literals execute Python operation and return result.
    if all_literal_children:
        logger.debug("Preparing for static calculation of %s", node)
        visited = set()
        ast_list = node.generate_ast_tree(visited)

        if isinstance(node, IndexNode):
            # IndexNodes mean that this is assigning to a single cell within the array in that
            # situation we need to put into another variable to store it.
            new_stmt = ast.Assign(
                targets=[ast.Name(node.varname, ctx=ast.Store())],
                value=node.ref
            )
            ast_list.append(new_stmt)

        logger.debug("About to evaluate: %s", astor.to_source(ast_list[0]))
        # always disable numba in this context.  We are only calling functions once, there is no reason to use
        # numba here.
        exec_ctx = get_execution_context()
        evaluate(ast_list, exec_ctx, __name__)

        value = exec_ctx[node.varname]
        logger.debug("Static calculation for %s produced result of %s", node, value)

        # todo handle this better for lists, some functions return numpy equivalents which neeed to be cast back
        if hasattr(value, 'item') and not isinstance(value, np.ndarray):
            value = value.item()

        new_node = LiteralNode(node.varname, value)

        # replace child will update the parents list; if we don't cache it first then can't
        # do the interations.
        node.replace_self(new_node)

        return new_node
    else:
        return node
