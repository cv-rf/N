class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def eat(self, token_type=None):
        tok = self.current()
        if tok is None:
            raise SyntaxError("Unexpected EOF")

        if token_type and tok[0] != token_type:
            raise SyntaxError(f"Expected {token_type}, got {tok}")

        self.pos += 1
        return tok

    def eat_newlines(self):
        while self.current() and self.current()[0] == 'NEWLINE':
            self.eat('NEWLINE')

    def parse(self):
        self.eat_newlines()
        statements = []
        while self.current():
            statements.append(self.statement())
            self.eat_newlines()
        return statements

    def statement(self):
        tok = self.current()

        if not tok:
            raise SyntaxError("Unexpected EOF")

        if tok[0] == 'IDENT':
            if tok[1] == 'if':
                return self.if_statement()

            if tok[1] == 'else':
                return SyntaxError("else without if")
            

            return self.ident_statement()

        if tok[0] == 'RETURN':
            self.eat('RETURN')
            return ('RETURN', self.expression())

        if tok[0] == 'BREAK':
            self.eat('BREAK')
            return ('BREAK',)

        if tok[0] == 'CONTINUE':
            self.eat('CONTINUE')
            return ('CONTINUE',)

        raise SyntaxError(f"Unexpected token in statement: {tok}")

    def if_statement(self):
        self.eat("IDENT")
        condition = self.expression()

        self.eat_newlines()
        self.eat("INDENT")

        if_body = []
        while self.current() and self.current()[0] != "DEDENT":
            if_body.append(self.statement())
            self.eat_newlines()

        self.eat("DEDENT")

        else_body = None

        if (
            self.current()
            and self.current()[0] == "IDENT"
            and self.current()[1] == "else"
        ):
            self.eat("IDENT")

            if (
                self.current()
                and self.current()[0] == "IDENT"
                and self.current()[1] == "if"
            ):
                else_body = [self.if_statement()]
            else:
                self.eat_newlines()
                self.eat("INDENT")

                else_body = []
                while self.current() and self.current()[0] != "DEDENT":
                    else_body.append(self.statement())
                    self.eat_newlines()

                self.eat("DEDENT")

        return ("IF", condition, if_body, else_body)

    def ident_statement(self):
        name = self.eat('IDENT')[1]
        tok = self.current()

        if tok and tok[0] == 'LBRACKET':
            return self.index_assignment(name)

        if tok and tok[0] == 'OP' and tok[1] == '=':
            self.eat('OP')
            return ('ASSIGN', name, self.expression())

        if tok and tok[0] == 'LPAREN':
            return ('CALL', name, self.func_args())
        
        if tok and tok[0] not in ('NEWLINE', 'DEDENT'):
            args = [self.expression()]

            while self.current() and self.current()[0] == 'COMMA':
                self.eat('COMMA')
                args.append(self.expression())

            return ('CALL', name, args)

        raise SyntaxError(f"Invalid IDENT usage: {name}")

    def index_assignment(self, name):
        self.eat('LBRACKET')
        index = self.expression()
        self.eat('RBRACKET')
        self.eat('OP')
        value = self.expression()
        return ('INDEX_ASSIGN', name, index, value)

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

        if tok is None:
            raise SyntaxError("Unexpected EOF")

        if tok[0] == 'OP' and tok[1] == '-':
            self.eat('OP')
            return ('BINOP', '-', ('NUMBER', 0), self.factor())

        if tok[0] == 'LPAREN':
            self.eat('LPAREN')
            expr = self.expression()
            self.eat('RPAREN')
            return expr

        if tok[0] == 'NUMBER':
            return ('NUMBER', int(self.eat('NUMBER')[1]))

        if tok[0] == 'TRUE':
            self.eat('TRUE')
            return ('BOOL', True)

        if tok[0] == 'FALSE':
            self.eat('FALSE')
            return ('BOOL', False)

        if tok[0] == 'STRING':
            return ('STRING', self._strip_string(self.eat('STRING')[1]))

        if tok[0] == 'LBRACKET':
            return self.list_expr()

        if tok[0] == 'LBRACE':
            return self.map_expr()

        if tok[0] == 'IDENT':
            name = self.eat('IDENT')[1]

            if self.current() and self.current()[0] == 'LBRACKET':
                self.eat('LBRACKET')
                index = self.expression()
                self.eat('RBRACKET')
                return ('INDEX', name, index)

            if self.current() and self.current()[0] == 'LPAREN':
                return ('CALL', name, self.func_args())

            return ('VAR', name)

        raise SyntaxError(f"Unexpected token in expression: {tok}")

    def func_args(self):
        self.eat('LPAREN')
        args = []

        while self.current() and self.current()[0] != 'RPAREN':
            args.append(self.expression())
            if self.current() and self.current()[0] == 'COMMA':
                self.eat('COMMA')

        self.eat('RPAREN')
        return args

    def list_expr(self):
        self.eat('LBRACKET')
        items = []

        if self.current() and self.current()[0] != 'RBRACKET':
            items.append(self.expression())
            while self.current() and self.current()[0] == 'COMMA':
                self.eat('COMMA')
                items.append(self.expression())

        self.eat('RBRACKET')
        return ('LIST', items)

    def map_expr(self):
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

    def _strip_string(self, s):
        return s[1:-1] if s.startswith('"') else s
