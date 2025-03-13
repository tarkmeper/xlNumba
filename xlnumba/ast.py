import ast

import astor

from .excel_reference import ExcelReference
from .logger import logger

NUMBA_FLAGS = {
    'nopython': True,
    'fastmath': True,
    'nogil': True,
}

GENERATOR_VAR_NAME = "_rgenerator"


def ast_tuple(x, y):
    """ Helper function for quickly creating two element tuples in AST which are fairly commonly needed"""
    if isinstance(x, int) and isinstance(y, int):
        return ast.Tuple(elts=[ast.Constant(x), ast.Constant(y)], ctx=ast.Load())
    else:
        return ast.Tuple(elts=[x, y], ctx=ast.Load())


def ast_call(func, args, keywords=None) -> ast.Call:
    """ Helper function for building AST call structure, hanlding functions in modules"""
    if isinstance(func, str):
        path = func.split(".")
        func = ast.Name(id=path[0], ctx=ast.Load())
        for attr in path[1:]:
            func = ast.Attribute(value=func, attr=attr, ctx=ast.Load())
    keywords = [] if keywords is None else keywords
    return ast.Call(func=func, args=args, keywords=keywords)


def numba_decorator() -> list[ast.Call]:
    """
    Ast decorator for compiled function to enable numba compilation and optimization of the
    function.
    """
    keywords = []
    for key, value in NUMBA_FLAGS.items():
        keywords.append(ast.keyword(arg=key, value=ast.Constant(value)))

    return [ast_call('numba.jit', [], keywords)]


def ast_function_body(graph, output_cells) -> list[ast.AST]:
    """ Given a graph generate the function body for this graph """
    visited = set()
    statement_list = list()

    for cell, ref in graph:
        statement_list.extend(ref.generate_ast_tree(visited))

    # Create return statement.
    output_keys = [ast.Constant(output_cells[k[0]]) for k in graph]
    output_values = [k[1].output_variable for k in graph]
    ast_dictionary = ast.Dict(keys=output_keys, values=output_values)
    statement_list.append(ast.Return(ast_dictionary))

    # This is useful in a very verbose debug mode to determine if there is one invalid
    # AST structure to determine which one it is and help identify what is wrong.
    if logger.level <= logger.VERBOSE_LOG_LEVEL:
        _test_each_statement(statement_list)

    return statement_list


def ast_arguments(inputs: dict[str, ExcelReference]):
    """
    Given a set of inputs generate the AST as input to the function
    :param inputs: List of input objects.
    :return: An ast argument object
    """
    args = []
    defaults = []

    for name, node in inputs.items():
        # Todo set annotation to appropriate type for numba.
        args.append(ast.arg(arg=name, annotation=None))
        if node.data_type != 'f':
            defaults.append(ast.Constant(node.value))
        else:
            defaults.append(ast.Constant(0))

    return ast.arguments(args=args,
                         vararg=None,
                         kwonlyargs=[],
                         kw_defaults=[],
                         kwarg=None,
                         defaults=defaults
                         )


def _test_each_statement(statements):
    """
    This creates a  verbose dump log for each statement confirming the AST tree statement is valid.
    This is useful when complex AST breaks due to structure being incorrect.
    """
    logger.verbose("-------- START OF STATEMENT COMPILER -----")
    for stmt in statements[:-1]:  # don't attempt to compile return statement, as it will fail.
        logger.verbose("--Staring on next statement--")
        logger.verbose("\t\t" + astor.to_source(stmt).strip())
        logger.verbose(astor.dump_tree(stmt))
        ast.fix_missing_locations(stmt)
        logger.verbose("\t--Compiling")
        compile(ast.Module(body=[stmt]), "<string>", "exec")
        logger.verbose("\t--Done Compiling")
    logger.verbose("-------- END OF STATEMENT COMPILER -----")
