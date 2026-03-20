from interpreter import Interpreter
import lexer
from parser import Parser

code = """b = buffer 4
b[0] = 10
b[4] = 20
b[0] = 300

i = 0
loop i < 5
        b[i] = i
        i = i + 1
"""

tokens = lexer.tokenize(code)

parser = Parser(tokens)
ast = parser.parse()

interpreter = Interpreter()
interpreter.run(ast)