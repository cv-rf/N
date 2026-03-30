from stdlib import STDLIB, Runtime

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class Env:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise Exception(f"Undefined variable: {name}")

    def set(self, name, value):
        self.vars[name] = value


class Buffer:
    def __init__(self, size):
        self.data = [0] * size


class Interpreter:
    def __init__(self):
        self.global_env = Env()
        self.env = self.global_env
        self.runtime = Runtime()
        self.builtins = STDLIB

    def run(self, ast):
        for stmt in ast:
            self.execute(stmt)

    def execute(self, node):
        t = node[0]

        if t == "ASSIGN":
            _, name, expr = node
            self.env.set(name, self.eval(expr))

        elif t == "IF":
            _, condition, if_body, else_body = node

            if self.eval(condition):
                for stmt in if_body:
                    self.execute(stmt)
            elif else_body:
                for stmt in else_body:
                    self.execute(stmt)

        elif t == "LOOP":
            _, condition, body = node

            while self.eval(condition):
                try:
                    for stmt in body:
                        self.execute(stmt)
                except ContinueException:
                    continue
                except BreakException:
                    break

        elif t == "RETURN":
            _, expr = node
            raise ReturnException(self.eval(expr))

        elif t == "BREAK":
            raise BreakException()

        elif t == "CONTINUE":
            raise ContinueException()

        elif t == "CALL":
            self.eval(node)

        else:
            raise Exception(f"Unknown statement: {node}")

    def eval(self, node):
        t = node[0]

        if t == "NUMBER":
            return node[1]

        if t == "STRING":
            return node[1]

        if t == "BOOL":
            return node[1]

        if t == "VAR":
            return self.env.get(node[1])

        if t == "LIST":
            return [self.eval(x) for x in node[1]]

        if t == "MAP":
            return {self.eval(k): self.eval(v) for k, v in node[1]}

        if t == "INDEX":
            _, name, idx_expr = node
            container = self.env.get(name)
            idx = self.eval(idx_expr)

            if isinstance(container, Buffer):
                return container.data[idx]

            if isinstance(container, list):
                return container[idx]

            if isinstance(container, dict):
                return container[self.eval(idx_expr)]

            raise Exception("Invalid indexing target")

        if t == "BINOP":
            _, op, l, r = node
            a = self.eval(l)
            b = self.eval(r)

            if op == "+": return a + b
            if op == "-": return a - b
            if op == "*": return a * b
            if op == "/": return a / b
            if op == "//": return a // b
            if op == "**": return a ** b

            if op == "==": return int(a == b)
            if op == "!=": return int(a != b)
            if op == "<": return int(a < b)
            if op == ">": return int(a > b)
            if op == "<=": return int(a <= b)
            if op == ">=": return int(a >= b)

        if t == "CALL":
            return self.call(node)

        raise Exception(f"Unknown expression: {node}")

    def call(self, node):
        _, name, args = node

        evaluated_args = [self.eval(a) for a in args]

        if name in self.builtins:
            return self.builtins[name](self.runtime, evaluated_args)

        fn = self.env.get(name)

        if not isinstance(fn, tuple) or fn[0] != "FUNC":
            raise Exception(f"{name} is not a function")

        _, params, body = fn

        if len(params) != len(evaluated_args):
            raise Exception("Argument mismatch")

        child = Env(self.env)

        for p, a in zip(params, evaluated_args):
            child.set(p, a)

        old = self.env
        self.env = child

        try:
            for stmt in body:
                self.execute(stmt)
        except ReturnException as r:
            return r.value
        finally:
            self.env = old
