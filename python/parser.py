class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def index_assignment(self):
        name = self.eat('IDENT')[1]
        self.eat('LBRACKET')
        index = self.expression()
        self.eat('RBRACKET')
        self.eat('OP')  # =
        value = self.expression()
        self.eat('NEWLINE')

        return ('INDEX_ASSIGN', name, index, value)

    def eat(self, token_type=None):
        tok = self.current()
        if tok is None:
            return None

        if token_type and tok[0] != token_type:
            raise SyntaxError(f"Expected {token_type}, got {tok}")

        self.pos += 1
        return tok

    def parse(self):
        statements = []
        while self.current():
            if self.current()[0] == 'NEWLINE':
                self.eat('NEWLINE')
                continue
            statements.append(self.statement())
        return statements

    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None

    def statement(self):
        tok = self.current()

        if tok[0] == 'IDENT':
            if self.peek() and self.peek()[0] == 'LBRACKET':
                return self.index_assignment()
            return self.assignment()

        if tok[0] == 'CONNECT':
            self.eat('CONNECT')
            host_tok = self.eat('STRING')
            host_node = ('STRING', host_tok[1][1:-1])
            port_tok = self.eat('NUMBER')
            port_node = ('NUMBER', int(port_tok[1]))
            self.eat('NEWLINE')
            return ('CONNECT', host_node, port_node)

        if tok[0] == 'STRING':
            text = self.eat('STRING')[1]
            return ('STRING', text[1:-1])

        if tok[0] == 'IF':
            self.eat('IF')
            condition = self.expression() # eval as bool
            # body - One or more indented statements
            body = []

            if self.current()[0] != 'NEWLINE':
                raise SyntaxError("Expected newline after if condition")
            self.eat('NEWLINE')

            if self.current()[0] != 'INDENT':
                raise SyntaxError("Expected indented block after if")
            self.eat('INDENT')

            while self.current() and self.current()[0] != 'DEDENT':
                body.append(self.statement())

            self.eat('DEDENT')
            return ('IF', condition, body)

        if tok[0] == 'LOOP':
            self.eat('LOOP')
            condition = self.expression()

            if self.current()[0] != 'NEWLINE':
                raise SyntaxError("Expected newline after loop condition")
            self.eat('NEWLINE')

            if self.current()[0] != 'INDENT':
                raise SyntaxError("Expected indented block after loop")
            self.eat('INDENT')

            body = []
            while self.current() and self.current()[0] != 'DEDENT':
                body.append(self.statement())

            self.eat('DEDENT')
            return ('LOOP', condition, body)

        if tok[0] == 'SEND':
            self.eat('SEND')
            arg = self.factor()
            self.eat('NEWLINE')
            return ('SEND', arg)

        if tok[0] == 'RECV':
            self.eat('RECV')
            arg = self.expression()
            self.eat('NEWLINE')
            return ('RECV', arg)

        if tok[0] == 'PRINT':
            return self.print_stmt()

        raise SyntaxError(f"Unknown statement: {tok}")

    def assignment(self):
        name = self.eat('IDENT')[1]
        self.eat('OP')  # '='

        if self.current()[0] == 'BUFFER':
            self.eat('BUFFER')
            size = self.expression()
            self.eat('NEWLINE')
            return ('BUFFER_ALLOC', name, size)

        expr = self.expression()
        self.eat('NEWLINE')
        return ('ASSIGN', name, expr)

    def print_stmt(self):
        self.eat('PRINT')
        expr = self.expression()
        self.eat('NEWLINE')
        return ('PRINT', expr)

    def expression(self):
        left = self.term()

        while self.current() and self.current()[0] == 'OP' and self.current()[1] in ('==','!=','<','>','<=','>='):
            op = self.eat('OP')[1]
            right = self.term()
            left = ('BINOP', op, left, right)

        while self.current() and self.current()[0] == 'OP' and self.current()[1] in ('+','-'):
            op = self.eat('OP')[1]
            right = self.term()
            left = ('BINOP', op, left, right)

        return left

    def term(self):
        left = self.factor()

        while self.current() and self.current()[1] in ('*', '/'):
            op = self.eat('OP')[1]
            right = self.factor()
            left = ('BINOP', op, left, right)

        return left

    def factor(self):
        tok = self.current()

        if tok[0] == 'NUMBER':
            return ('NUMBER', int(self.eat('NUMBER')[1]))

        if tok[0] == 'IDENT':
            name = self.eat('IDENT')[1]

            if self.current() and self.current()[0] == 'LBRACKET':
                self.eat('LBRACKET')
                index = self.expression()
                self.eat('RBRACKET')
                return ('INDEX', name, index)

            return ('VAR', name)

        if tok[0] in ('SEND', 'RECV'):
            func_name = self.eat(tok[0])[0].lower()
            arg = self.factor()
            return (func_name.upper(), arg)

        raise SyntaxError(f"Unexpected token: {tok}")
