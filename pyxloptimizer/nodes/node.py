import ast
from abc import abstractmethod

from pyxloptimizer.excel_reference import DataType


class Node:
    """
    Nodes represent high higher level graph then the base AST graph .  They are a layer of abstraction on top of the
    Python AST library grouping the library together to better match the Excel structure and provide a level of
    abstraction which allows easier manipulation of the concepts at Excel's level.
    """

    def __init__(self, variable_name, children):
        self._children = children
        self._parents = []
        self._var = variable_name
        for child in self._children:
            child.append_parent(self)

    def append_parent(self, parent):
        self._parents.append(parent)

    def remove_parent(self, parent):
        self._parents.remove(parent)

    @property
    def children(self) -> list['Node']:
        return self._children

    def generate_ast_tree(self, visited) -> list[ast.stmt]:
        stmts = []
        if self in visited:
            return stmts
        visited.add(self)

        for child in self._children:
            stmts += child.generate_ast_tree(visited)
        if self.ast:
            stmts.append(self.ast)
        return stmts

    def depends_on(self, targets: list['Node']) -> bool:
        """
        Check if any of the elements in the target list are a parent of the current element.
        """
        return any(filter(lambda parent: parent in targets or parent.depends_on(targets), self._parents))

    @property
    def ref(self):
        return ast.Name(id=self._var, ctx=ast.Load())

    @property
    def varname(self) -> str:
        return self._var

    @property
    def data_type(self):
        return DataType.Number

    @property
    @abstractmethod
    def shape(self):
        pass

    @property
    @abstractmethod
    def ast(self) -> ast.stmt:
        pass

    def replace_in_graph(self, new_node):
        """
        Execute algoirthm to replace this node with another node in the graph.  This finds all
        parents and updates their mappings to repalce the existing node with a new one.
        """
        parents_cache = list(self._parents)
        for parent in parents_cache:
            parent.replace_child(self, new_node)

    def replace_child(self, old, new):
        """
        As long the variable name of old and new are the same there is no need to rewrite the AST
        statements on the parent object.  If the variable names change this becomes much more complicated.
        """
        assert old in self._children
        idx = self._children.index(old)
        self._children[idx] = new
        new.append_parent(self)
        old.remove_parent(self)

    def _ast_wrap(self, value):
        """ Helper to assign the value to this objects variable """
        return ast.Assign(targets=[ast.Name(id=self._var, ctx=ast.Store())], value=value)

    def replace_self(self, new_node: "Node") -> None:
        """
        In general the only reason outside this node we need the parent
        :return:
        """
        parents_cache = list(self._parents)
        for parent in parents_cache:
            parent.replace_child(self, new_node)

    def parents_set(self) -> set["Node"]:
        return set(self._parents)
