from interpreter import Interpreter
import lexer
from parser import Parser

code = """b = buffer 4
i = 0
loop i < 3
        b[0] = i
        send b
        i = i + 1
"""

tokens = lexer.tokenize(code)

parser = Parser(tokens)
ast = parser.parse()

interpreter = Interpreter()
interpreter.run(ast)