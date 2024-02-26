from pyxloptimizer import Compiler

if __name__ == '__main__':
    ctx = Compiler("tests/fixtures/basic")
    ctx.add_input('Raw', 'A1')
    ctx.add_output('Adjusted', 'B1')
    fn = ctx.compile()

    adjusted = fn(Raw=3.0)
