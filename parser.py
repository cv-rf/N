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
            while self.current() and self.current()[0] == 'NEWLINE':
                self.eat('NEWLINE')

            if self.current() is None:
                break

            stmt = self.statement()
            statements.append(stmt)

            if self.current() and self.current()[0] == 'NEWLINE':
                self.eat('NEWLINE')
        return statements

    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None

    def statement(self):
        tok = self.current()

        if tok[0] == 'IDENT':
            # Index assignment
            if self.peek() and self.peek()[0] == 'LBRACKET' and self.peek(2) and self.peek(2)[0] == 'OP' and self.peek(2)[1] == '=':
                node = self.index_assignment()
            # Function call
            elif self.peek() and self.peek()[0] == 'LPAREN':
                node = self.factor()  # returns FUNC_CALL
            # Simple assignment
            elif self.peek() and self.peek()[0] == 'OP' and self.peek()[1] == '=':
                node = self.assignment()
            else:
                raise SyntaxError(f"Unexpected IDENT usage: {tok}")
            if self.current() and self.current()[0] == 'NEWLINE':
                self.eat('NEWLINE')
            return node

        elif tok[0] in ('FUNC', 'BREAK', 'CONTINUE', 'RETURN', 'IF', 'LOOP', 'PRINT', 'SEND', 'RECV', 'CONNECT', 'UDP_CONNECT'):
            if tok[0] == 'FUNC':
                node = self.func_def()
            elif tok[0] == 'BREAK':
                self.eat('BREAK')
                node = ('BREAK',)
            elif tok[0] == 'CONTINUE':
                self.eat('CONTINUE')
                node = ('CONTINUE',)
            elif tok[0] == 'RETURN':
                self.eat('RETURN')
                expr = self.expression()
                node = ('RETURN', expr)
            elif tok[0] in ('CONNECT', 'UDP_CONNECT'):
                kw = self.eat(tok[0])[0]
                host_tok = self.eat('STRING')
                host_node = ('STRING', host_tok[1][1:-1])
                port_tok = self.eat('NUMBER')
                port_node = ('NUMBER', int(port_tok[1]))
                node = (kw, host_node, port_node)
            elif tok[0] == 'PRINT':
                node = self.print_stmt()
            elif tok[0] == 'SEND':
                self.eat('SEND')
                arg = self.factor()
                node = ('SEND', arg)
            elif tok[0] == 'RECV':
                self.eat('RECV')
                arg = self.expression()
                node = ('RECV', arg)
            elif tok[0] == 'IF':
                node = self.if_stmt()
            elif tok[0] == 'LOOP':
                node = self.loop_stmt()
            else:
                raise SyntaxError(f"Unhandled keyword: {tok}")

            if self.current() and self.current()[0] == 'NEWLINE':
                self.eat('NEWLINE')
            return node

        elif tok[0] == 'STRING':
            text = self.eat('STRING')[1]
            if self.current() and self.current()[0] == 'NEWLINE':
                self.eat('NEWLINE')
            return ('STRING', text[1:-1])

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
        return self.comparison()

    def comparison(self):
        left = self.add_sub()
        while self.current() and self.current()[0] == 'OP' and self.current()[1] in ('==', '!=', '<', '>', '<=', '>='):
            op = self.eat('OP')[1]
            right = self.add_sub()
            left = ('BINOP', op, left, right)
        return left

    def add_sub(self):
        left = self.mul_div()
        while self.current() and self.current()[0] == 'OP' and self.current()[1] in ('+', '-'):
            op = self.eat('OP')[1]
            right = self.mul_div()
            left = ('BINOP', op, left, right)
        return left

    def mul_div(self):
        left = self.exponent()
        while self.current() and self.current()[0] == 'OP' and self.current()[1] in ('*', '/', '//'):
            op = self.eat('OP')[1]
            right = self.exponent()
            left = ('BINOP', op, left, right)
        return left

    def exponent(self):
        left = self.factor()
        while self.current() and self.current()[0] == 'OP' and self.current()[1] == '**':
            self.eat('OP')
            right = self.factor()
            left = ('BINOP', '**', left, right)
        return left

    def factor(self):
        tok = self.current()

        # Unary minus
        if tok[0] == 'OP' and tok[1] == '-':
            self.eat('OP')
            node = self.factor()
            return ('BINOP', '-', ('NUMBER', 0), node)

        # Parentheses
        if tok[0] == 'LPAREN':
            self.eat('LPAREN')
            expr = self.expression()
            self.eat('RPAREN')
            return expr

        # Number literal
        if tok[0] == 'NUMBER':
            return ('NUMBER', int(self.eat('NUMBER')[1]))

        # Boolean literals
        if tok[0] == 'TRUE':
            self.eat('TRUE')
            return ('NUMBER', 1)
        if tok[0] == 'FALSE':
            self.eat('FALSE')
            return ('NUMBER', 0)

        # String literal with escapes
        if tok[0] == 'STRING':
            text = self.eat('STRING')[1]
            text = text[1:-1]
            text = bytes(text, "utf-8").decode("unicode_escape")
            return ('STRING', text)

        # List
        if tok[0] == 'LBRACKET':
            self.eat('LBRACKET')
            elements = []
            if self.current() and self.current()[0] != 'RBRACKET':
                elements.append(self.expression())
                while self.current() and self.current()[0] == 'COMMA':
                    self.eat('COMMA')
                    elements.append(self.expression())
            self.eat('RBRACKET')
            return ('LIST', elements)

        # Map
        if tok[0] == 'LBRACE':
            self.eat('LBRACE')
            pairs = []
            if self.current() and self.current()[0] != 'RBRACE':
                key = self.expression()
                self.eat('COLON')
                value = self.expression()
                pairs.append((key, value))
                while self.current() and self.current()[0] == 'COMMA':
                    self.eat('COMMA')
                    key = self.expression()
                    self.eat('COLON')
                    value = self.expression()
                    pairs.append((key, value))
            self.eat('RBRACE')
            return ('MAP', pairs)

        # Variable or function call
        if tok[0] == 'IDENT':
            name = self.eat('IDENT')[1]
            if self.current() and self.current()[0] == 'LBRACKET':
                self.eat('LBRACKET')
                index = self.expression()
                self.eat('RBRACKET')
                return ('INDEX', name, index)
            if self.current() and self.current()[0] == 'LPAREN':
                self.eat('LPAREN')
                args = []
                while self.current() and self.current()[0] != 'RPAREN':
                    args.append(self.expression())
                    if self.current() and self.current()[0] == 'COMMA':
                        self.eat('COMMA')
                self.eat('RPAREN')
                return ('FUNC_CALL', name, args)
            return ('VAR', name)

        # SEND / RECV
        if tok[0] in ('SEND', 'RECV'):
            func_name = self.eat(tok[0])[0].lower()
            arg = self.factor()
            return (func_name.upper(), arg)

        raise SyntaxError(f"Unexpected token: {tok}")
