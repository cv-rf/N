from interpreter import Interpreter
import lexer
from parser import Parser

code = """udp_connect "127.0.0.1" 9999
b = buffer 4
b[0] = 10
send b
r = recv 4
print r[0]
"""

tokens = lexer.tokenize(code)

parser = Parser(tokens)
ast = parser.parse()

interpreter = Interpreter()
interpreter.run(ast)
