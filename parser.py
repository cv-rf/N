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
            if tok[1] == 'import':
                return self.import_statement()

            if tok[1] == 'if':
                return self.if_statement()

            if tok[1] == 'loop':
                return self.loop_statement()
            
            if tok[1] == 'func':
                return self.func_def()

            if tok[1] == 'return':
                self.eat('IDENT')
                if self.current() and self.current()[0] not in ('NEWLINE', 'DEDENT'):
                    return ('RETURN', self.expression())
                return ('RETURN', None)
            
            if tok[1] == 'break':
                self.eat('IDENT')
                return ('BREAK',)
            
            if tok[1] == 'continue':
                self.eat('IDENT')
                return ('CONTINUE',)

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

    def import_statement(self):
        self.eat('IDENT')
        module = self.eat('STRING')[1]
        module = module.strip('"').strip("'")
        return ('IMPORT', module)

    def if_statement(self):
        self.eat("IDENT")
        condition = self.expression()

        if_body = self.parse_block()

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
                else_body = self.parse_block()

        return ("IF", condition, if_body, else_body)

    def loop_statement(self):
        self.eat("IDENT")
        condition = self.expression()

        body = self.parse_block()

        return ("LOOP", condition, body)

    def ident_statement(self):
        name = self.eat('IDENT')[1]
        tok = self.current()

        if tok and tok[0] == 'LBRACKET':
            return self.index_assignment(name)

        if tok and tok[0] == 'OP' and tok[1] == '=':
            self.eat('OP')
            return ('ASSIGN', name, self.expression())

        if tok and tok[0] == 'LPAREN':
            return ('EXPR', ('CALL', name, self.func_args()))
        
        if tok and tok[0] not in ('NEWLINE', 'DEDENT'):
            args = [self.expression()]

            while self.current() and self.current()[0] == 'COMMA':
                self.eat('COMMA')
                args.append(self.expression())

            return ('EXPR', ('CALL', name, args))

        raise SyntaxError(f"Invalid IDENT usage: {name}")

    def parse_block(self):
        self.eat_newlines()
        self.eat("INDENT")

        body = []
        while self.current() and self.current()[0] != "DEDENT":
            body.append(self.statement())
            self.eat_newlines()
        
        self.eat("DEDENT")
        return body
    
    def func_def(self):
        self.eat("IDENT")

        name = self.eat("IDENT")[1]

        self.eat("LPAREN")
        params = []

        if self.current() and self.current()[0] != "RPAREN":
            params.append(self.eat("IDENT")[1])
            while self.current() and self.current()[0] == "COMMA":
                self.eat("COMMA")
                params.append(self.eat("IDENT")[1])
        
        self.eat("RPAREN")

        body = self.parse_block()

        return ("FUNC_DEF", name, params, body)

    def index_assignment(self, name):
        self.eat('LBRACKET')
        index = self.expression()
        self.eat('RBRACKET')
        self.eat('OP')
        value = self.expression()
        return ('INDEX_ASSIGN', name, index, value)

    def expression(self):
        return self.logic_or()

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

    def logic_or(self):
        left = self.logic_and()

        while self.current() and self.current()[0] == 'OP' and self.current()[1] == '||':
            self.eat('OP')
            right = self.logic_and()
            left = ('BINOP', '||', left, right)
        
        return left
    
    def logic_and(self):
        left = self.comparison()

        while self.current() and self.current()[0] == 'OP' and self.current()[1] == '&&':
            self.eat('OP')
            right = self.comparison()
            left = ('BINOP', '&&', left, right)
            
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
        
        if tok[0] == 'OP' and tok[1] == '!':
            self.eat('OP')
            return ('UNOP', '!', self.factor())

        if tok[0] == 'LPAREN':
            self.eat('LPAREN')
            expr = self.expression()
            self.eat('RPAREN')
            return expr

        if tok[0] == 'NUMBER':
            return ('NUMBER', int(self.eat('NUMBER')[1]))

        if tok[0] == 'STRING':
            return ('STRING', self._strip_string(self.eat('STRING')[1]))

        if tok[0] == 'LBRACKET':
            return self.list_expr()

        if tok[0] == 'LBRACE':
            return self.map_expr()

        if tok[0] == 'IDENT':
            node = self.eat('IDENT')
            name = node[1]
            left = ('VAR', name)

            while self.current() and self.current()[0] == 'DOT':
                self.eat('DOT')
                attr = self.eat('IDENT')[1]
                left = ('GETATTR', left, attr)

            if self.current() and self.current()[0] == 'LBRACKET':
                self.eat('LBRACKET')
                index = self.expression()
                self.eat('RBRACKET')
                return ('INDEX', left, index)

            if self.current() and self.current()[0] == 'LPAREN':
                return ('EXPR', ('CALL', left, self.func_args()))

            return left

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
