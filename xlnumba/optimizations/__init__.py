from .array_inplace import array_inplace
from .collapse_literals import collapse_literals
from .lazy_conditional import lazy_conditional
from .merge_array import merge_array
from ..logger import logger
from ..nodes import Graph

OPTIMIZATION_LIST = {
    'collapse_literals': collapse_literals,
    'merge_array': merge_array,
    'array_inplace': array_inplace,

    # lazy conditional needs to be towards end as it pulls nodes out of the normal graph and
    # into subgraphs; or support more broadly for subgraphs needs to be added.
    'lazy_conditional': lazy_conditional
}


def optimize_graph(graph: Graph, disable_optimization) -> Graph:
    logger.debug("Graph optimization started")
    for name, optimization in OPTIMIZATION_LIST.items():
        if not disable_optimization or not disable_optimization:
            logger.debug(f"Optimization {name} starting")
            graph = optimization(graph)
            logger.debug(f"Optimization {name} complete")
    return graph
