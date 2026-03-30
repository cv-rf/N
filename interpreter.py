from stdlib import STDLIB, Runtime
from lexer import tokenize
from parser import Parser

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
        
        if hasattr(self, "builtins") and name in self.builtins:
            return self.builtins[name]
        
        raise Exception(f"Undefined variable: {name}")

    def set(self, name, value):
        self.vars[name] = value

class Frame:
    def __init__(self, env, name="<anon>"):
        self.env = env
        self.name = name
        self.return_value = None
        self.should_return = False


class Buffer:
    def __init__(self, size):
        self.data = [0] * size


class Interpreter:
    def __init__(self):
        self.global_env = Env()
        self.env = self.global_env
        self.frames = []
        self.runtime = Runtime()
        self.runtime.interpreter = self
        self.global_env.builtins = STDLIB.copy()
        self.modules = {}
    
    def push_frame(self, env):
        frame = {"env": env, "return": None, "should_return": False}
        self.frames.append(frame)
        self.env = env
    
    def pop_frame(self):
        frame = self.frames.pop()

        if self.frames:
            self.env = self.frames[-1]["env"]
        else:
            self.env = self.global_env
        
        return frame

    def run(self, ast):
        for stmt in ast:
            self.execute(stmt)

    def _import_module(self, module):
        if module in self.modules:
            self.global_env.set(module, self.modules[module])
            return

        path = module + ".n"

        with open(path, "r") as f:
            code = f.read()

        ast = Parser(tokenize(code)).parse()

        module_env = Env(self.global_env)

        old_env = self.env
        self.env = module_env

        try:
            for stmt in ast:
                self.execute(stmt)
        finally:
            self.env = old_env

        self.modules[module] = module_env
        self.global_env.set(module, module_env)

    def execute(self, node):
        t = node[0]

        if t == "ASSIGN":
            _, name, expr = node
            self.env.set(name, self.eval(expr))

        elif t == "IMPORT":
            _, module = node
            self._import_module(module)

        elif t == "IF":
            _, condition, if_body, else_body = node

            if self.is_truthy(self.eval(condition)):
                for stmt in if_body:
                    self.execute(stmt)
            elif else_body:
                for stmt in else_body:
                    self.execute(stmt)

        elif t == "FUNC_DEF":
            _, name, params, body = node
            self.env.set(name, ("FUNC", params, body, self.env))

        elif t == "LOOP":
            _, condition, body = node

            while self.is_truthy(self.eval(condition)):
                try:
                    for stmt in body:
                        self.execute(stmt)
                except ContinueException:
                    continue
                except BreakException:
                    break

        elif t == "RETURN":
            if not self.frames:
                raise Exception("Return outside function")
            
            _, expr = node
            value = self.eval(expr) if expr else None

            frame = self.frames[-1]
            frame["return"] = value
            frame["should_return"] = True

        elif t == "BREAK":
            raise BreakException()

        elif t == "CONTINUE":
            raise ContinueException()
        
        elif t == "EXPR":
            self.eval(node[1])

        else:
            raise Exception(f"Unknown statement: {node}")

    def eval(self, node):
        t = node[0]

        if t == "EXPR":
            return self.eval(node[1])

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
        
        if t == "UNOP":
            _, op, operand = node
            val = self.eval(operand)
            if op == "!":
                return not self.is_truthy(val)
        
        if t == "GETATTR":
            _, obj, name = node
            o = self.eval(obj)

            if isinstance(o, dict):
                return o[name]
            
            if isinstance(o, Env):
                return o.get(name)

            raise Exception("Invalid attribute access")

        if t == "MAP":
            return {
                self.eval(k): self.eval(v)
                for k, v in node[1]
            }

        if t == "INDEX":
            _, obj, idx_expr = node

            container = self.eval(obj)
            idx = self.eval(idx_expr)

            if isinstance(container, Buffer):
                return container.data[idx]

            if isinstance(container, list):
                return container[idx]

            if isinstance(container, dict):
                return container[idx]

            if isinstance(container, str):
                return str(container[idx])

            if isinstance(container, Env):
                return container.get(idx)

            raise Exception("Invalid indexing target")

        if t == "BINOP":
            _, op, l, r = node
            a = self.eval(l)
            b = self.eval(r)

            if op == "+":  return a + b
            if op == "-":  return a - b
            if op == "*":  return a * b
            if op == "%":  return a % b
            if op == "|":  return a | b
            if op == "&":  return a & b
            if op == "/":  return a / b
            if op == "//": return a // b
            if op == "**": return a ** b

            if op in [">", "<", ">=", "<=", "==", "!="]:
                if type(a) != type(b):
                    raise Exception(f"Type mismatch: {type(a)} vs {type(b)}")

                if op == "==": return a == b
                if op == "!=": return a != b
                if op == "<":  return a < b
                if op == ">":  return a > b
                if op == "<=": return a <= b
                if op == ">=": return a >= b

            if op == "&&":
                left = self.eval(l)
                if not self.is_truthy(left):
                    return left
                return self.eval(r)
            if op == "||":
                left = self.eval(l)
                if not self.is_truthy(left):
                    return left
                return self.eval(r)

        if t == "CALL":
            return self.call(node)

        raise Exception(f"Unknown expression: {node}")

    def call(self, node):
        _, name_node, args = node

        evaluated_args = [self.eval(a) for a in args]

        if isinstance(name_node, tuple):
            fn = self.eval(name_node)
        else:
            fn = self.env.get(name_node)

        if callable(fn):
            try:
                return fn(self.runtime, evaluated_args)
            except TypeError:
                return fn(*evaluated_args)

        if isinstance(fn, tuple) and fn[0] == "FUNC":
            _, params, body, closure_env = fn

            if len(params) != len(evaluated_args):
                raise Exception("Argument mismatch")

            frame_env = Env(closure_env)

            for p, a in zip(params, evaluated_args):
                frame_env.set(p, a)

            self.push_frame(frame_env)

            try:
                for stmt in body:
                    self.execute(stmt)

                    if self.frames[-1]["should_return"]:
                        break

            finally:
                frame = self.pop_frame()

            return frame["return"]

        raise Exception(f"{name_node} is not a function")

    def execute_with_env(self, node, env):
        old = self.env
        self.env = env

        try:
            return self.execute(node)
        finally:
            self.env = old

    def is_truthy(self, value):
        if value is False:
            return False
        if value is True:
            return True
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, list):
            return len(value) > 0
        if isinstance(value, dict):
            return len(value) > 0
        return True