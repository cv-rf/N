from interpreter import Interpreter
import lexer
from parser import Parser

code = """
s = "Hello, N!"
print s
"""

tokens = lexer.tokenize(code)

parser = Parser(tokens)
ast = parser.parse()

interpreter = Interpreter()
interpreter.run(ast)
