import sys

from lexer import tokenize
from parser import Parser
from interpreter import Interpreter

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <script.n>")
        sys.exit(1)

    script_path = sys.argv[1]

    try:
        with open(script_path, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {script_path}")
        sys.exit(1)

    try:
        tokens = tokenize(code)
    except SyntaxError as e:
        print(f"Lexing error: {e}")
        sys.exit(1)
    
    parser = Parser(tokens)
    try:
        ast = parser.parse()
    except SyntaxError as e:
        print(f"Parsing error: {e}")
        sys.exit(1)

    interpreter = Interpreter()
    try:
        interpreter.run(ast)
    except Exception as e:
        print(f"Runtime error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass