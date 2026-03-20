import random

class Interpreter:
    def __init__(self):
        self.env = {}

    def run(self, ast):
        for stmt in ast:
            self.execute(stmt)

    def execute(self, node):
        node_type = node[0]

        if node_type == 'ASSIGN':
            _, name, expr = node
            value = self.eval(expr)
            self.env[name] = value

        elif node_type == 'IF':
            _, condition, body = node
            cond_value = self.eval(condition)
            if cond_value:
                for stmt in body:
                    self.execute(stmt)

        elif node_type == 'PRINT':
            _, expr = node
            value = self.eval(expr)
            print(value)

        elif node_type == 'BUFFER_ALLOC':
            _, name, size_expr = node
            size = self.eval(size_expr)
            self.env[name] = [0] * size

        elif node_type == 'SEND':
            _, buffer_node = node
            buf = self.eval(buffer_node)
            if not isinstance(buf, list):
                raise Exception("SEND expects a buffer")
            print(f"Sending: {buf}")

        elif node_type == 'RECV':
            _, size_node = node
            size = self.eval(size_node)
            if size <= 0:
                raise Exception("RECV size must be positive")
            buf = [random.randint(0, 255) for _ in range(size)]
            return buf

        elif node_type == 'LOOP':
            _, condition, body = node
            while self.eval(condition):
                for stmt in body:
                    self.execute(stmt)

        elif node_type == 'INDEX_ASSIGN':
            _, name, index_expr, value_expr = node

            if name not in self.env:
                raise Exception(f"Undefined buffer: {name}")

            index = self.eval(index_expr)
            value = self.eval(value_expr)

            if index < 0 or index >= len(self.env[name]):
                raise Exception(f"Buffer index out of bounds: {index}")
            
            if value < 0 or value > 255:
                raise Exception(f"Buffer value must be 0-255, got {value}")
            
            self.env[name][index] = value

        else:
            raise Exception(f"Unknown statement: {node}")

    def eval(self, node):
        node_type = node[0]

        if node_type == 'INDEX':
            _, name, index_expr = node

            if name not in self.env:
                raise Exception(f"Undefined buffer: {name}")
            
            index = self.eval(index_expr)
            if index < 0 or index >= len(self.env[name]):
                raise Exception(f"Buffer index out of bounds: {index}")
            return self.env[name][index]

        if node_type == 'NUMBER':
            return node[1]

        if node_type == 'VAR':
            name = node[1]
            if name not in self.env:
                raise Exception(f"Undefined variable: {name}")
            return self.env[name]

        if node_type == 'RECV':
            _, size_node = node
            size = self.eval(size_node)
            if size <= 0:
                raise Exception("RECV size must be positive")
            buf = [random.randint(0, 255) for _ in range(size)]
            return buf

        if node_type == 'SEND':
            _, buffer_node = node
            buf = self.eval(buffer_node)
            if not isinstance(buf, list):
                raise Exception("SEND expects a buffer")
            print(f"Sending: {buf}")
            return None

        if node_type == 'BINOP':
            _, op, left, right = node
            l = self.eval(left)
            r = self.eval(right)

            if op == '+': return l + r
            if op == '-': return l - r
            if op == '*': return l * r
            if op == '/': return l // r  # integer division

            # comparison operators
            if op == '==': return int(l == r)
            if op == '!=': return int(l != r)
            if op == '<': return int(l < r)
            if op == '>': return int(l > r)
            if op == '<=': return int(l <= r)
            if op == '>=': return int(l >= r)

        raise Exception(f"Unknown expression: {node}")