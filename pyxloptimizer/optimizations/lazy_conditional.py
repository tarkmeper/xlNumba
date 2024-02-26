import ast as astlib

from ..nodes import Node, Graph, FunctionOpNode
from ..shape import SCALAR_SHAPE


class ConditionalNode(Node):
    """
    Conditional nodes identify logic which feeds into IF statements in Excel and allows only the
    conditional branch to be executed.

    This can be useful in case where the two branches of the IF are very different; wihtout the optimization
    the normal approach woudl first evaluate both sides of the IF statement and then the IF statement
    conditional; this allows the graph to be dynamic with "sub-graphs" for aech side of the IF expression.

    Likely this concept needs a revist; the subgraphs only exist in this context and most of the other optimizations
    can't handle them correctly.
    """

    def __init__(self, node: Node):
        """Transfer over function Node object to this one."""
        super().__init__(node.varname, node.children)
        for child in node.children:
            child.remove_parent(node)

    @property
    def shape(self):
        return SCALAR_SHAPE

    @property
    def data_type(self):
        assert self.true_node.data_type == self.false_node.data_type
        return self.true_node.data_type

    @property
    def true_node(self):
        return self.children[1]

    @property
    def false_node(self):
        return self.children[2]

    def generate_ast_tree(self, visited: set):
        """
        Generate AST if statement.

        First deetermine if there are any statements that can be moved into the if/block
        for those that can move them into the if block, otehrwise follow normal pattern
        to generate ast statements.
        """
        stmts = []
        if self in visited:
            return
        visited.add(self)

        # the following will generate all statements needed ahead of the if statement
        _split_branch(self.true_node, stmts, visited)
        _split_branch(self.false_node, stmts, visited)

        # generate the condition logic
        stmts.extend(self.children[0].generate_ast_tree(visited))

        # generate both the True and False blocks
        true_statements = self.true_node.generate_ast_tree(visited)
        false_statements = self.false_node.generate_ast_tree(visited)

        if_stmt = astlib.If(
            test=self.children[0].ref,
            body=true_statements + [self._ast_wrap(self.true_node.ref)],
            orelse=false_statements + [self._ast_wrap(self.false_node.ref)]
        )
        stmts.append(if_stmt)
        return stmts

    @property
    def ast(self):
        raise NotImplementedError("Cannot directly generate AST - only can rebuild tree")


def lazy_conditional(graph: Graph) -> Graph:
    """
    Entry point for optimziation.
    """
    visited = set()
    for name, root in graph:
        children = list(root.children)
        for child in children:  # output nodes can't be collapsed so skip them to start the recursion.
            _exec_recursive(child, visited)
    return graph


def _exec_recursive(node: Node, visited):
    """
    Depth first search recursively for functions that use the "IF" function.
    Todo: Extend to other if (IFS/SWITCH) statements in the future.
    """
    if node in visited:
        return
    visited.add(node)

    # Depth first seach
    for child in node.children:
        _exec_recursive(child, visited)  # this may replace child.

    # process statements and replace if it matches items we have support for.
    if isinstance(node, FunctionOpNode) and node.excel_name == 'IF' and node.shape == SCALAR_SHAPE:
        new_node = ConditionalNode(node)
        node.replace_in_graph(new_node)


def _split_branch(node: Node, stmts: list, visited: set):
    """
    Algorithm to split the graph below an if branch into the dependnecies that need to
    be executed ahead of the if block.

    High-level the alrogithm looks for the subgraph that starts from node which has no dependencies
    outside that subgraph.

    Approach is the following:
        1. Determine all the nodes which descend form the top node and sort based on the
        maximum depth.
        2. Check each node in sorted order to make sure all the parent nodes are within the
        sub-graph.
    """
    included = node.parents_set()
    if len(included) > 1:
        parent_stmts = node.generate_ast_tree(visited)
        stmts.extend(parent_stmts)
    else:
        assert len(included) == 1

        # pass 1 find maximum distance from node to each part of the subtree
        depth_dict = {}
        stack = [(node, 0)]
        while stack:
            top_node, depth = stack.pop()
            if top_node not in depth_dict or depth > depth_dict[top_node]:
                depth_dict[top_node] = depth
                stack.extend([(x, depth + 1) for x in top_node.children])
        ordered_nodes = sorted(depth_dict.items(), key=lambda x: x[1])

        for (top_node, _) in ordered_nodes:
            top_node_parent_set = top_node.parents_set()
            all_included = len(top_node_parent_set - included) == 0
            if all_included:
                included.add(top_node)
            else:
                new_stmts = top_node.generate_ast_tree(visited)
                stmts.extend(new_stmts)
