import socket

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

class Interpreter:
    def __init__(self):
        self.env = {}
        self.conn = None       # TCP socket
        self.udp_sock = None   # UDP socket
        self.active_socket = None
        self.udp_addr = None   # target for UDP

    def run(self, ast):
        for stmt in ast:
            self.execute(stmt)

    def execute(self, node):
        node_type = node[0]

        # ---------------- CONNECT / UDP ----------------
        if node_type == 'CONNECT':
            _, host_node, port_node = node
            host = self.eval(host_node)
            port = self.eval(port_node)

            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.conn.connect((host, port))
                self.active_socket = self.conn
                print(f"Connected TCP to {host}:{port}")
            except ConnectionRefusedError:
                raise Exception(f"Cannot connect to {host}:{port}")

        elif node_type == 'UDP_CONNECT':
            _, host_node, port_node = node
            host = self.eval(host_node)
            port = self.eval(port_node)

            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.active_socket = self.udp_sock
            self.udp_addr = (host, port)
            print(f"UDP socket ready for {host}:{port}")

        # ---------------- FUNC ----------------
        elif node_type == 'FUNC_DEF':
            _, name, params, body = node
            self.env[name] = ('FUNC', params, body)

        elif node_type == 'RETURN':
            _, expr = node
            value = self.eval(expr)
            raise ReturnException(value)

        elif node_type == 'FUNC_CALL':
            _, name, args = node
            if name not in self.env or self.env[name][0] != 'FUNC':
                raise Exception(f"Undefined function: {name}")

            _, params, body = self.env[name]
            if len(args) != len(params):
                raise Exception(f"Expected {len(params)} args, got {len(args)}")

            local_env = self.env.copy()
            for p, a in zip(params, args):
                local_env[p] = self.eval(a)

            try:
                self.run_function_body(body, local_env)
            except ReturnException as ret:
                return ret.value

        elif node_type == 'BREAK':
            raise BreakException()

        elif node_type == 'CONTINUE':
            raise ContinueException()

        # ---------------- SEND ----------------
        elif node_type == 'SEND':
            _, buffer_node = node
            buf = self.eval(buffer_node)
            if not isinstance(buf, list):
                raise Exception("SEND expects a buffer")

            data = bytes(buf)

            if self.active_socket is None:
                raise Exception("No socket available for SEND")

            # UDP send
            if self.active_socket == self.udp_sock:
                self.udp_sock.sendto(data, self.udp_addr)
                print(f"Sent UDP: {list(data)}")
            # TCP send
            else:
                self.conn.sendall(data)
                print(f"Sent TCP: {list(data)}")

        # ---------------- RECV ----------------
        elif node_type == 'RECV':
            _, size_node = node
            size = self.eval(size_node)
            if size <= 0:
                raise Exception("RECV size must be positive")

            if self.active_socket is None:
                raise Exception("No socket available for RECV")

            # UDP recv
            if self.active_socket == self.udp_sock:
                data, addr = self.udp_sock.recvfrom(size)
                buf = list(data)
                return buf
            # TCP recv
            else:
                data = self.conn.recv(size)
                buf = list(data)
                return buf

        # ---------------- ASSIGN / BUFFER / PRINT / IF / LOOP ----------------
        elif node_type == 'ASSIGN':
            _, name, expr = node
            value = self.eval(expr)
            self.env[name] = value

        elif node_type == 'BUFFER_ALLOC':
            _, name, size_expr = node
            size = self.eval(size_expr)
            self.env[name] = [0] * size

        elif node_type == 'PRINT':
            _, expr = node
            value = self.eval(expr)
            print(value)

        elif node_type == 'IF':
            _, condition, if_body, else_body = node

            if self.eval(condition):
                for stmt in if_body:
                    self.execute(stmt)
            else:
                for stmt in else_body:
                    self.execute(stmt)

        elif node_type == 'LOOP':
            _, condition, body = node
            while self.eval(condition):
                try:
                    for stmt in body:
                        self.execute(stmt)
                except ContinueException:
                    continue
                except BreakException:
                    break

        elif node_type == 'INDEX_ASSIGN':
            _, name, index_expr, value_expr = node
            if name not in self.env:
                raise Exception(f"Undefined buffer: {name}")

            index = self.eval(index_expr)
            value = self.eval(value_expr)

            if not isinstance(index, int):
                raise Exception(f"Buffer index must be integer, got {index}")
            if index < 0 or index >= len(self.env[name]):
                raise Exception(f"Buffer index out of bounds: {index}")

            if not isinstance(value, int):
                raise Exception(f"Buffer value must be integer, got {value}")
            if value < 0 or value > 255:
                raise Exception(f"Buffer value must be 0-255, got {value}")

            self.env[name][index] = value

        else:
            raise Exception(f"Unknown statement: {node}")

    # ---------------- EVAL ----------------
    def eval(self, node):
        node_type = node[0]

        if node_type == 'SEND':
            self.execute(node)
            return None

        if node_type == 'RECV':
            _, size_node = node
            size = self.eval(size_node)
            if size <= 0:
                raise Exception("RECV size must be positive")

            if self.active_socket is None:
                raise Exception("No socket available for RECV")

            if self.active_socket == self.udp_sock:
                data, addr = self.udp_sock.recvfrom(size)
                return list(data)
            else:
                data = self.conn.recv(size)
                return list(data)

        if node_type == 'NUMBER':
            return node[1]

        if node_type == 'STRING':
            return node[1]

        if node_type == 'VAR':
            name = node[1]
            if name not in self.env:
                raise Exception(f"Undefined variable: {name}")
            return self.env[name]

        if node_type == 'INDEX':
            _, name, index_expr = node
            if name not in self.env:
                raise Exception(f"Undefined buffer: {name}")
            index = self.eval(index_expr)
            if not isinstance(index, int):
                raise Exception(f"Buffer index must be integer, got {index}")
            if index < 0 or index >= len(self.env[name]):
                raise Exception(f"Buffer index out of bounds: {index}")
            return self.env[name][index]

        if node_type == 'BINOP':
            _, op, left, right = node
            l = self.eval(left)
            r = self.eval(right)

            if op == '+': return l + r
            if op == '-': return l - r
            if op == '*': return l * r
            if op == '/': return l // r

            if op == '==': return int(l == r)
            if op == '!=': return int(l != r)
            if op == '<': return int(l < r)
            if op == '>': return int(l > r)
            if op == '<=': return int(l <= r)
            if op == '>=': return int(l >= r)

        # ------------------- function call -------------------
        if node_type == 'FUNC_CALL':
            _, func_name, arg_nodes = node
            if func_name not in self.env or self.env[func_name][0] != 'FUNC':
                raise Exception(f"Undefined function: {func_name}")

            _, params, body = self.env[func_name]
            if len(arg_nodes) != len(params):
                raise Exception(f"{func_name} expected {len(params)} args, got {len(arg_nodes)}")

            local_env = self.env.copy()
            for param, arg_node in zip(params, arg_nodes):
                local_env[param] = self.eval(arg_node)

            try:
                self.run_function_body(body, local_env)
            except ReturnException as ret:
                return ret.value

        raise Exception(f"Unknown expression: {node}")

    def run_function_body(self, body, local_env):
        old_env = self.env
        self.env = local_env
        try:
            for stmt in body:
                self.execute(stmt)
        finally:
            self.env = old_env
