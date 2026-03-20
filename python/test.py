from interpreter import Interpreter
import lexer
from parser import Parser

code = """connect "127.0.0.1" 9999
b = buffer 4
b[0] = 10
b[1] = 20
send b
r = recv 4
print r[0]
print r[1]
"""

tokens = lexer.tokenize(code)

parser = Parser(tokens)
ast = parser.parse()

interpreter = Interpreter()
interpreter.run(ast)