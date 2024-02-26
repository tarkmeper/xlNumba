import ast
import astor

from .logger import logger


def evaluate(statements, exec_ctx, logging_name):
    """
    Evaluates generated statements directly.  This is primarily used to build the function, but might be used
    by some optimizations to partially evaluate portions of the graph.

    :param statements:  List of statements for evaluation
    :param exec_ctx:    Execution context - this is expected to include numba/numpy and excel_functions along with
    anything else we might need to do the evaluation.
    :param logging_name: Name for logging purpose so that we can tell which evaluation drove this.
    """
    module_body = ast.Module(body=statements)
    tree = astor.dump_tree(module_body)
    logger.verbose("%s geneatation - tree is:\n%s", logging_name, tree)
    code = astor.to_source(module_body)
    logger.debug("%s generation - src_code is:\n%s", logging_name, code)

    ast.fix_missing_locations(module_body)
    code_obj = compile(module_body, logging_name, "exec")
    exec(code_obj, exec_ctx, exec_ctx)


def get_execution_context():
    """
    :return: The execution context needed to execute the generated function.  This includes all the imports
    needed to execute the function.
    """
    exec_ctx = {}
    # import required modules to the execution context in order to build the function
    import_list = [ast.Import(names=[
        ast.alias('numpy', 'numpy'),
        ast.alias('numba', 'numba'),
        ast.alias('logging', 'logging'),
        ast.alias('pyxloptimizer.excel_functions.mathematical', 'mathematical'),
        ast.alias('pyxloptimizer.excel_functions.logical', 'logical'),
        ast.alias('pyxloptimizer.excel_functions.statistical', 'statistical'),
        ast.alias('pyxloptimizer.excel_functions.text', 'text'),
        ast.alias('pyxloptimizer.excel_functions.lookup', 'lookup'),
        ast.alias('pyxloptimizer.excel_functions.special', 'special'),
        ast.alias('pyxloptimizer.excel_functions.user_functions', 'user_functions'),
        ast.alias('scipy', 'scipy'),
        ast.alias('builtins', 'builtins')
    ])]

    import_mod = ast.Module(import_list)
    ast.fix_missing_locations(import_mod)
    exec(compile(import_mod, '<string>', 'exec'), exec_ctx, exec_ctx)
    return exec_ctx
