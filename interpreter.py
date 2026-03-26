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

            if name in self.env and self.env[name][0] == 'FUNC':
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
            else:
                return self.eval(node)

        elif node_type == 'BREAK':
            raise BreakException()

        elif node_type == 'CONTINUE':
            raise ContinueException()

        # ---------------- SEND ----------------
        elif node_type == 'SEND':
            _, buffer_node = node
            buf = self.eval(buffer_node)

            if not (isinstance(buf, tuple) and buf[0] == 'BUFFER'):
                raise Exception("SEND expects a buffer")

            data = bytes(buf[1])

            if self.active_socket is None:
                raise Exception("No socket available for SEND")

            # UDP send
            if self.active_socket == self.udp_sock:
                self.udp_sock.sendto(data, self.udp_addr)
                print(f"Sent UDP: {list(data)}")
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
            self.env[name] = ('BUFFER', [0] * size)

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

            if isinstance(self.env[name], dict):
                key = self.eval(index_expr)
                value = self.eval(value_expr)

                if not isinstance(key, str):
                    raise Exception("Map key must be string")

                self.env[name][key] = value
                return

            if self.env[name][0] != 'BUFFER':
                raise Exception("Indexing only allowed on buffers")

            buffer = self.env[name][1]

            index = self.eval(index_expr)
            value = self.eval(value_expr)

            if not isinstance(index, int):
                raise Exception(f"Buffer index must be integer, got {index}")
            if index < 0 or index >= len(buffer):
                raise Exception(f"Buffer index out of bounds: {index}")

            if not isinstance(value, int):
                raise Exception(f"Buffer value must be integer, got {value}")
            if value < 0 or value > 255:
                raise Exception(f"Buffer value must be 0-255, got {value}")

            buffer[index] = value

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

        if node_type == 'TRUE':
            return 1

        if node_type == 'FALSE':
            return 0

        if node_type == 'LIST':
            _, elements = node
            return [self.eval(e) for e in elements]

        if node_type == 'MAP':
            _, pairs = node
            result = {}

            for key_node, value_node in pairs:
                key = self.eval(key_node)
                value = self.eval(value_node)

                if not isinstance(key, str):
                    raise Exception("Map keys must be strings")

                result[key] = value

            return result

        if node_type == 'INDEX':
            _, name, index_expr = node
            if name not in self.env:
                raise Exception(f"Undefined buffer: {name}")

            value = self.env[name]

            if isinstance(value, dict):
                key = self.eval(index_expr)

                if not isinstance(key, str):
                    raise Exception(f"Map key must be string, got {key}")

                if key not in value:
                    raise Exception(f"Key not found: {key}")

                return value[key]

            index = self.eval(index_expr)
            if not isinstance(index, int):
                raise Exception(f"Buffer index must be integer, got {index}")

            if isinstance(value, tuple) and value[0] == 'BUFFER':
                buf = value[1]
                if index < 0 or index >= len(buf):
                    raise Exception(f"Buffer index out of bounds: {index}")
                return buf[index]

            if isinstance(value, list):
                if index < 0 or index >= len(value):
                    raise Exception(f"List index out of bounds: {index}")
                return value[index]

            raise Exception("Indexing is only supported on buffers or lists")

        if node_type == 'BINOP':
            _, op, left, right = node
            l = self.eval(left)
            r = self.eval(right)

            if op == '+': return l + r
            if op == '-': return l - r
            if op == '*': return l * r
            if op == '/': return l / r
            if op == '//': return l // r
            if op == '**': return l ** r

            if op == '==': return int(l == r)
            if op == '!=': return int(l != r)
            if op == '<': return int(l < r)
            if op == '>': return int(l > r)
            if op == '<=': return int(l <= r)
            if op == '>=': return int(l >= r)

        # ------------------- function call -------------------
        if node_type == 'FUNC_CALL':
            _, func_name, arg_nodes = node

            # ---- Built-in append ----
            if func_name == 'append':
                if len(arg_nodes) != 2:
                    raise Exception("append(list_or_buffer, value) requires 2 arguments")

                container = self.eval(arg_nodes[0])
                val = self.eval(arg_nodes[1])

                if isinstance(container, list):
                    container.append(val)
                elif isinstance(container, tuple) and container[0] == 'BUFFER':
                    container[1].append(val)
                else:
                    raise Exception("append() first argument must be a list or buffer")
                return None

            # ---- Built-in pop ----
            if func_name == 'pop':
                if len(arg_nodes) != 1:
                    raise Exception("pop(list_or_buffer) requires 1 argument")

                container = self.eval(arg_nodes[0])

                if isinstance(container, list):
                    if not container:
                        raise Exception("pop() from empty list")
                    return container.pop()
                elif isinstance(container, tuple) and container[0] == 'BUFFER':
                    buf = container[1]
                    if not buf:
                        raise Exception("pop() from empty buffer")
                    return buf.pop()
                else:
                    raise Exception("pop() argument must be a list or buffer")

            # ---- Built-in len ----
            if func_name == 'len':
                if len(arg_nodes) != 1:
                    raise Exception("len() takes exactly 1 argument")
                value = self.eval(arg_nodes[0])

                if isinstance(value, list):
                    return len(value)
                elif isinstance(value, str):
                    return len(value)
                elif isinstance(value, tuple) and value[0] == 'BUFFER':
                    return len(value[1])
                else:
                    raise Exception("len() unsupported type")

            # ---- User-defined functions ----
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
