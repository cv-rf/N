import re

TOKEN_SPEC = [
    ('NUMBER',   r'\d+'),
    ('IDENT',    r'[A-Za-z_][A-Za-z0-9_]*'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('OP',       r'[+\-*/=]'),
    ('NEWLINE',  r'\n'),
    ('SKIP',     r'[ \t]+'),
]

KEYWORDS = {'print', 'buffer', 'send', 'recv'}

def tokenize(code):
    tokens = []
    lines = code.split('\n')

    indent_stack = [0]

    for line in lines:
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(' '))

        if indent % 8 != 0:
            raise SyntaxError("Indent must be multiple of 8 spaces")

        indent_level = indent // 8

        if indent_level > indent_stack[-1]:
            tokens.append(('INDENT', indent_level))
            indent_stack.append(indent_level)

        while indent_level < indent_stack[-1]:
            indent_stack.pop()
            tokens.append(('DEDENT', indent_level))

        pos = indent
        while pos < len(line):
            match = None
            for tok_type, pattern in TOKEN_SPEC:
                regex = re.compile(pattern)
                match = regex.match(line, pos)
                if match:
                    text = match.group(0)

                    if tok_type == 'IDENT' and text in KEYWORDS:
                        tok_type = text.upper()

                    if tok_type != 'SKIP':
                        tokens.append((tok_type, text))

                    pos = match.end(0)
                    break

            if not match:
                raise SyntaxError(f"Unexpected character: {line[pos]}")

        tokens.append(('NEWLINE', '\n'))

    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(('DEDENT', 0))

    return tokens