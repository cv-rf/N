from interpreter import Interpreter
import lexer
from parser import Parser

code = """b = buffer 4
send b
r = recv 4
print r[0]
"""

tokens = lexer.tokenize(code)

parser = Parser(tokens)
ast = parser.parse()

interpreter = Interpreter()
interpreter.run(ast)