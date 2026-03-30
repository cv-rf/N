import re

TOKEN_SPEC = [
    ('NUMBER',   r'\d+'),
    ('STRING',   r'"(?:\\.|[^"\\\n])*"'),

    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('COMMA',    r','),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('COLON',    r':'),
    ('DOT',      r'\.'),

    ('IDENT',    r'[A-Za-z_][A-Za-z0-9_]*'),
    ('OP',       r'==|!=|<=|>=|\+=|-=|\*=|/=|//|\*\*|&&|\|\||[%!|&]|<|>|\+|\-|\*|/|='),
    ('COMMENT',  r'\#.*'),
    ('SKIP',     r'[ \t]+'),
]

TOKEN_SPEC = [(name, re.compile(pattern)) for name, pattern in TOKEN_SPEC]

def tokenize(code):
    tokens = []
    indent_stack = [0]
    lines = code.split('\n')

    for line_no, line in enumerate(lines, start=1):

        if line.strip() == "":
            continue

        stripped = line.lstrip(' ')
        indent = len(line) - len(stripped)
        pos = 0

        if indent % 8 != 0:
            raise SyntaxError(f"Line {line_no}: indent must be multiple of 8 spaces")

        if indent > indent_stack[-1]:
            indent_stack.append(indent)
            tokens.append(('INDENT', '', line_no, 0))

        while indent < indent_stack[-1]:
            indent_stack.pop()
            tokens.append(('DEDENT', '', line_no, 0))

        if indent != indent_stack[-1]:
            raise SyntaxError(f"Line {line_no}: invalid indentation level")

        pos = indent

        while pos < len(line):
            match = None

            for tok_type, regex in TOKEN_SPEC:
                match = regex.match(line, pos)
                if not match:
                    continue

                text = match.group(0)

                if tok_type in ('SKIP', 'COMMENT'):
                    pos = match.end()
                    break

                tokens.append((tok_type, text, line_no, pos))
                pos = match.end()
                break

            if not match:
                raise SyntaxError(
                    f"Line {line_no}, col {pos}: unexpected '{line[pos]}'"
                )

        tokens.append(('NEWLINE', '\n', line_no, len(line)))

    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(('DEDENT', '', len(lines), 0))

    return tokens