"""
Merge array's optimization attempts to find overlapping regions in the graph and merge them together to leverage
numpy views on data as opposed to creating numerous arrays representing the same data.  This can have tremendous
performance improvements on ranges that aggregate incrementally, as re-creating the arrays can quickly be the
bottleneck.

There are two different modes this works in:
    1) Re-order nodes.  This applies if none of the nodes in a cluster have dependencies between them.  In this case
    we can just push the calculation of the largest array first, and have all other utilizations act as a view
    onto this first array.

    2) Incrementally build array.  If the creation of the array depends on earlier values in the array we instead
    create a buffer array to hold all the values and incrementally write new values into the array.
"""
import ast
from math import prod

from ..ast import ast_tuple, ast_call
from ..nodes.node import Node
from ..excel_reference import DataType
from ..nodes import Graph, ExcelArrayNode, IndexNode
from ..logger import logger
from ..shape import Shape


class BufferNode(Node):
    """
    Buffer nodes are necessary in situations where we are incrementally building an array, where each element
    depends on previous elements (for example array where each element is sum of preceeding elemeents).

    To handle this we create an empty array and populate it as we go then execute any dependencies.
    """

    def __init__(self, variable_name: str, length: int, element_type: DataType):
        super().__init__(variable_name, [])
        self.length = length  # todo we need to figure out how to support this on 2D arrays
        self._data_type = element_type

    @property
    def shape(self):
        return Shape(self.length, 1)

    @property
    def data_type(self):
        return self._data_type

    @property
    def ast(self):
        inner_ast = ast_call('numpy.empty', [self.shape.ast])
        return self._ast_wrap(inner_ast)

    def __repr__(self):
        return f"MERGE_BUFFER:{self.varname}"


class BufferAssignmentNode(Node):
    """
    Buffer assignment nodes are a sepcial type of node that writes the results of a calculation into the buffer array
    above.

    One unique behaviour for these nodes is that they create a dependency between them.  We need to ensure that they
    execute in the same order as the values are written, since they are used to populate the previous BufferNodes.

    The first assignment has a pointer to the array as a child, after that each assignment has a pointer to the previous
    assignment to ensure they are executed in order and that the buffer is instantiated first.
    """

    def __init__(self, buffer_node: BufferNode, idx: int, child: Node, last_idx_node: Node):
        """
        last_idx_node is the previous assignment object.
        child is the value taht thisis being assigned to.
        """
        super().__init__(buffer_node.varname, [child, last_idx_node])
        self.idx = idx

    @property
    def value(self):
        return self._children[0]

    @property
    def shape(self):
        raise NotImplementedError('Should not need the shape of an assignment')

    @property
    def data_type(self):
        raise NotImplementedError('Should not need the data_type of an assignment')

    @property
    def ast(self):
        return ast.Assign(
            targets=[
                ast.Subscript(
                    value=self.ref,
                    slice=ast_tuple(self.idx, 0),
                    ctx=ast.Store(),
                )],
            value=self.value.ref
        )


class BufferIndexNode(IndexNode):
    """
    Buffer index nodes dereference a range from the buffer.  More or less the same as a normal Index Node,
    other than in its construction.
    """

    def __init__(self, variable_name: str, child: BufferNode, index_slice, last_idx_node: Node):
        super().__init__(variable_name + "_bf_" + str(index_slice[0]), child, index_slice)
        self._children.append(last_idx_node)
        last_idx_node.append_parent(self)


def merge_array(graph: Graph):
    """
    Algorithm starts with array with most elements in each cluster and attempts to merge all
    other arrays in the cluster into the largest array.
    """
    logger.debug("Starting merge ranges with graph %s", graph)
    visited = set()
    array_nodes = []
    for name, root in graph:
        find_array_nodes(root, visited, array_nodes)

    sorted_arrays = sorted(array_nodes, key=lambda x: x[0].shape.size, reverse=True)

    clusters = cluster_ranges(sorted_arrays)

    for cluster in clusters:
        # two cases if there are dependencies between the cells of the cluster we built up the larger
        # arrays from smaller arrays.  If not we can just use index to create view.
        if has_dependencies(cluster):
            # case 2 we have dependencies, and so we build incrementally
            logger.debug("Can't merge array due to dependencies for cluster %s", cluster)
            build_array_from_cluster(cluster)
        else:
            # no dependnecies so just view of the existing cluster.
            replace_array_node_with_index_node(cluster)

    return graph


def find_array_nodes(node: Node, visited: set[Node], array_nodes: list[tuple[ExcelArrayNode, set[str]]]):
    """
    Depth first search to find all array nodes.
    """
    if node not in visited:
        visited.add(node)
        if isinstance(node, ExcelArrayNode):
            variables = {child.varname for child in node.children}
            array_nodes.append((node, variables))
        children = list(node.children)
        for child in children:
            find_array_nodes(child, visited, array_nodes)


def cluster_ranges(array_nodes):
    """
    Clustering algoirthm.  This is currentely very simple, there might be better ways to do it.  Starts with most
    number of elements in the arrays, and then attempts to put smaller arrays fully within them.  If it can they are
     part of its cluster.  If smaller group isn't covered by the larger group create new cluster.
    """
    cluster_map = {}
    clusters = []
    logger.debug("Found array nodes %s", array_nodes)
    for idx, (node, details) in enumerate(array_nodes):
        cluster_idx = None

        for other_idx in range(0, idx):
            _, other_details = array_nodes[other_idx]
            cluster_idx = None
            if details.issubset(other_details):
                cluster_idx = other_idx
                break

        if cluster_idx is None:
            clusters.append([node])
            cluster_map[idx] = len(clusters) - 1
        else:
            clusters[cluster_map[cluster_idx]].append(node)
    logger.debug("Created clusters %s", clusters)
    return clusters


def has_dependencies(cluster):
    for idx in range(1, len(cluster)):
        current_node = cluster[idx]
        if current_node.depends_on(cluster[:idx]):
            return True
    return False


def replace_array_node_with_index_node(cluster):
    covering_node = cluster[0]
    for node in cluster[1:]:
        if node.children == covering_node.children:
            node.replace_in_graph(covering_node)
        else:
            index_slice = get_slice(node, covering_node)
            new_node = IndexNode(node.varname, covering_node, index_slice)
            node.replace_in_graph(new_node)
            for child in node.children:
                child.remove_parent(node)


def build_array_from_cluster(cluster: list[Node]):
    covering_node = cluster[0]
    covering_children = covering_node.children
    bf = BufferNode(cluster[0].varname + "_buffer", prod(cluster[0].shape), covering_node.data_type)
    current_set = set()
    last_idx_node = bf

    for node in reversed(cluster):
        new_children = set(node.children) - current_set
        current_set = current_set.union(new_children)

        for child in new_children:
            idx = covering_children.index(child)
            idx_node = BufferAssignmentNode(bf, idx, child, last_idx_node)
            last_idx_node = idx_node

        index_slice = get_slice(node, covering_node)
        new_node = BufferIndexNode(bf.varname, bf, index_slice, last_idx_node)
        node.replace_in_graph(new_node)
        for child in node.children:
            child.remove_parent(node)


def get_slice(child, covering_node: Node):
    child_variables = [child for child in child.children]
    cluster_variables = [node for node in covering_node.children]

    # Create list of indexes for each of the child variables in the cluster variable
    indexes = [cluster_variables.index(var) for var in child_variables]

    # for now this only supports contiguous indexes, for the future need to enhance if somehow we wind up discrete
    # subsets
    # todo support non-continguous indexes
    logger.debug("Indexes are %s", indexes)
    assert indexes == list(range(min(indexes), max(indexes) + 1))
    if covering_node.shape.vertical:
        return (min(indexes), max(indexes) + 1), (0, 1)
    else:
        assert covering_node.shape.horizontal
        return (0, 1), (min(indexes), max(indexes) + 1)
