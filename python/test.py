from interpreter import Interpreter
import lexer
from parser import Parser

code = """r = recv 4
if r[0] >= 128
        send r
        print r[0]

"""

tokens = lexer.tokenize(code)

parser = Parser(tokens)
ast = parser.parse()

interpreter = Interpreter()
interpreter.run(ast)