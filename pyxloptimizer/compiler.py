import ast

import astor
import openpyxl

from .ast import numba_decorator, ast_function_body, ast_arguments
from .compiler_frame import CompilerReference, CompilerFrame, NestedCompilerFrame, FunctionCompilerFrame, \
    create_compiler_frame
from .excel_functions import find_function_details
from .excel_reference import ExcelReference
from .execution import evaluate, get_execution_context
from .logger import logger
from .nodes import Node, Graph, FunctionOpNode, wrap_output, wrap_input
from .optimizations import optimize_graph
from .special_functions import SPECIAL_FUNCTION_MAP

FNC_NAME = "compiled_function"


class Compiler:
    """
    Main entry poit for pyxloptimizer controls the compilation inner loop.
    """

    def __init__(self, file):
        """
        :param file: Either a file name or an openpyxl workbook, workbook must not be readonly.

        Readonly limitation is due to how openpxyl handles the files, array formulas are only available in non-readonly
        mode.  If opened in writable mode the values will be presented instead.
        """
        if isinstance(file, openpyxl.Workbook):
            if file.read_only:
                raise AttributeError("Workbook must be editable for array formulae to be populated by open pyxl")
            self.wb = file
        else:
            self.wb = openpyxl.load_workbook(file, keep_vba=False, keep_links=False, rich_text=True)
        self._outputs = {}
        self._output_cells = {}
        self._inputs = {}
        self._input_cells = {}

    def add_output(self, name: str, cell_ref: str):
        """
        Identify one of the expected outputs of the compiled function on the sheet.  Outputs must either be a formula
        or range in cell list.

        :param name:     Output variable name to use.
        :param cell_ref: Reference to the cell in the Excel sheet.
        """
        output = ExcelReference(self.wb, cell_ref)
        self._outputs[name] = output
        self._output_cells[output] = name
        return self

    def add_input(self, name: str, cell_ref: str):
        """
        Identify one of the expected inputs from the compiled function.  Input not identified will be assumed
        to be fixed value for the calculation.

        :param name: Variable name for this input
        :param cell_ref: Reference to a cell or range of cells that the input would fill.  
        """
        input_ref = ExcelReference(self.wb, cell_ref)
        self._inputs[name] = input_ref
        self._input_cells[input_ref] = name
        return self

    def generate_code(self, disable_numba=False, disable_optimizations=False):
        """
        Generate source code as a string that represents this function.

        :param disable_numba: Disable all numba decorator on the function.
        :param disable_optimizations: Set to True to disable all optimizations or a list of optimizations specifically
        to disable
        :return: Source code to generated function.
        """
        fn = self._gen_ast(disable_numba, disable_optimizations)
        code = astor.to_source(fn)
        logger.debug(code)
        return code

    def compile(self, disable_numba=False, disable_optimizations=False):
        """
        Return a compiled function which equates to the evaluated worksheet.

        :param disable_numba: Disable all numba decorator on the function.
        :param disable_optimizations: Set to True to disable all optimizations or a list of optimizations specifically
        to disable.
        :return: a compiled function.
        """
        fn = self._gen_ast(disable_numba, disable_optimizations)

        exec_ctx = get_execution_context()
        evaluate([fn], exec_ctx, "CORE")
        return exec_ctx[FNC_NAME]

    def _gen_ast(self, disable_numba: bool, disable_optimizations: bool):
        if len(self._outputs) == 0 or len(self._inputs) == 0:
            raise AttributeError("Must have at least one output and one input for compilation")

        # all input nodes are automatically references overriding any formulas that may be in those cells.
        references: dict[CompilerReference, Node] = {}
        for name, ref in self._inputs.items():
            compiler_ref = CompilerReference(mode=CompilerReference.Mode.range, active_cell=ref)
            references[compiler_ref] = wrap_input(ref, name)

        # start the algorithm based on all the output cells.
        stack: list[CompilerFrame] = []
        for ref in self._outputs.values():
            compiler_ref = CompilerReference(mode=CompilerReference.Mode.range, active_cell=ref)
            stack.append(create_compiler_frame(compiler_ref))

        #########################################################
        # MAIN LOOP
        ##########################################################
        _compiler_loop(references, stack)

        # build the outputs based on the generated graph.
        graph = Graph()
        for name, ref in self._outputs.items():
            compiler_ref = CompilerReference(mode=CompilerReference.Mode.range, active_cell=ref)
            output_node = wrap_output(name, references[compiler_ref], ref.shape)
            graph.append((ref, output_node))

        optimize_graph(graph, disable_optimizations)

        if disable_numba:
            disable_numba_recursive(x[1] for x in graph)

        # build function body
        function_body = ast.FunctionDef(
            name=FNC_NAME,
            args=ast_arguments(self._inputs),
            body=ast_function_body(graph, self._output_cells),
            decorator_list=numba_decorator() if not disable_numba else []
        )

        return function_body


def disable_numba_recursive(outputs):
    """
    Search graph for function nodes and mark those nodes as disabled for Numba optimizations.
    """
    stack = list(outputs)
    visited = set()
    while stack:
        top = stack.pop()

        if top in visited:
            continue

        visited.add(top)
        if isinstance(top, FunctionOpNode):
            top.disable_numba = True
        stack.extend(top.children)


def _compiler_loop(references: {CompilerReference, Node}, stack: list[CompilerFrame]):
    """
    Main compilation function which generates the overall AST graph for the Excel sheet.

    Input stack is expected to countain the final outputs to start processing.

    This function is the core of the algorithm and functions as a recursive stack evaluating the next range in the
    Excel sheet.  Uses a stack instead of recurssion  as sheets can have a very large amount of dependencies
    which would result in exceeding the recurusion depth for Python.

    The stack contains a statemachine made up of:
         * "CompilerFrames" which are used to snapshot the state of processing a specific cell or sub-cell.
         * "CompilerReferences" which are used to reference a section of logic in Excel.

    CompilerFrames are responsible for the logic of turning a CompilerReference into a Node which in trun  can be
    converted to a Python AST graph.  The CompilerReferences are cached within the reference dictionary, so
    repeated usage of the same cell - or even same function/nested logic can be reused.


    The best way to think of this is that  each Frame is a recursive call, with each reference being a
    single iteration of handling the expression within that call.
    """
    while stack:
        frame = stack[-1]
        next_reference = frame.next_reference()

        if next_reference is None:
            # no more work to do on this frame; generate the outout reference object.
            node = frame.finalize()
            logger.debug(f"Creating reference for {frame.referenced_object}")
            references[frame.referenced_object] = node
            stack.pop()
        elif next_reference in references:
            # Compilerframe requesting link to node that has already been computed; push that result back into
            # the frame as an input.
            frame.push_node(references[next_reference])
        else:
            # This is a reference we haven't seen before; so we need to determine how to handle it
            # in most cases this will create a new Compiler Reference Frame.
            new_obj = _process_next_reference(frame, next_reference)
            # special case. This object is the result of the special funciton the next iteration of the loop
            # will pick it up and return it to parent context.
            if isinstance(new_obj, Node):
                references[next_reference] = new_obj
            else:
                stack.append(new_obj)


def _process_next_reference(frame: CompilerFrame, next_reference: CompilerReference) -> Node | CompilerFrame:
    """
    Depending on the mode for the next reference different actions need to be taken. This function determines the
    correct next action and then produces either a "node" if the next action can be converted to a node or a
    CompilerReferenceFrame if further expansion of variables is required prior to this node being able to be handled.

    :param frame:  Current frame being processed
    :param next_reference: Next reference we are returning.
    :return:  The next object or frame to be evaluated.
    """
    match next_reference.mode:
        case CompilerReference.Mode.range:
            # Compiler frame looking for a new range that has not been previously compiled, we need to find the frame
            # and push the link back to current frame.
            result = create_compiler_frame(next_reference)
        case CompilerReference.Mode.function:
            fn_name_full = next_reference.func_data.name
            args = next_reference.func_data.args

            # token includes opening bracket so drop last character, as well as new xl namespace XLFN
            fn_name = fn_name_full[:-1].upper().replace("_XLFN.", "").replace(".", "_x_")
            if fn_name in SPECIAL_FUNCTION_MAP:
                logger.debug(f"Special function {frame.active_cell} with name {fn_name} and values {args}")
                result = SPECIAL_FUNCTION_MAP[fn_name](frame, args)
            else:
                logger.debug(f"Creating function for {frame.active_cell} with name {fn_name} and values {args}")
                fn_details = find_function_details(fn_name)
                result = FunctionCompilerFrame(next_reference, frame, fn_name, fn_details)
        case CompilerReference.Mode.paren:
            result = NestedCompilerFrame(next_reference, frame)
        case _:
            raise NotImplementedError()
    return result
