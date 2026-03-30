import socket

from lexer import tokenize
from parser import Parser

class Runtime:
    def __init__(self):
        self.state = {
            "tcp": None,
            "udp": None,
            "active": None,
            "udp_addr": None
        }


def std_print(rt, args):
    values = args
    print(*values)
    return None


def std_connect(rt, args):
    host, port = args

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    rt.state["tcp"] = sock
    rt.state["active"] = sock
    return None


def std_udp_connect(rt, args):
    host, port = args

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    rt.state["udp"] = sock
    rt.state["active"] = sock
    rt.state["udp_addr"] = (host, port)
    return None


def std_send(rt, args):
    buf = args[0]

    if not isinstance(buf, list):
        raise Exception("SEND expects Buffer-like list")

    sock = rt.state["active"]
    if not sock:
        raise Exception("No active socket")

    data = bytes(buf)

    if sock == rt.state["udp"]:
        sock.sendto(data, rt.state["udp_addr"])
    else:
        sock.sendall(data)

    return None


def std_recv(rt, args):
    size = args[0]

    sock = rt.state["active"]
    if not sock:
        raise Exception("No active socket")

    sock.settimeout(0.1)

    try:
        if sock == rt.state["udp"]:
            data, _ = sock.recvfrom(size)
        else:
            data = sock.recv(size)
    except socket.timeout:
        return []

    return list(data)

def std_ord(rt, args):
    if len(args[0]) != 1:
        raise Exception("ord expects a single character")
    return ord(args[0])

def std_chr(rt, args):
    return chr(args[0])

def std_substr(rt, args):
    s, start, end = args
    return s[start:end]

def std_upper(rt, args):
    return args[0].upper()

def std_lower(rt, args):
    return args[0].lower()

def std_trim(rt, args):
    return args[0].strip()

def std_contains(rt, args):
    s, sub = args
    return sub in s

def std_replace(rt, args):
    s, old, new = args
    return s.replace(old, new)

def std_tostring(rt, args):
    return str(args[0])

def std_toint(rt, args):
    return int(args[0])

def std_len(rt, args):
    if len(args) != 1:
        raise Exception("len expects 1 argument")
    
    value = args[0]

    if isinstance(value, (str, list, dict)):
        return len(value)
    
    raise Exception("len: unsupported type")

def std_append(rt, args):
    lst, value = args

    if not isinstance(lst, list):
        raise Exception("append: first argument must be a list")

    lst.append(value)
    return lst

def std_read_file(rt, args):
    path = args[0]
    if '.' not in path.split('/')[-1]:
        path = path + '.n'
    with open(path, 'r') as f:
        return f.read()

def std_write_file(rt, args):
    path, content = args
    with open(path, 'w') as f:
        f.write(content)
    return None

def std_exit(rt, args):
    code = args[0] if args else 0
    import sys
    sys.exit(code)

STDLIB = {
    "print": std_print,
    "connect": std_connect,
    "udp_connect": std_udp_connect,
    "send": std_send,
    "recv": std_recv,
    "ord": std_ord,
    "chr": std_chr,
    "substr": std_substr,
    "upper": std_upper,
    "lower": std_lower,
    "trim": std_trim,
    "contains": std_contains,
    "replace": std_replace,
    "toString": std_tostring,
    "toInt": std_toint,
    "len": std_len,
    "append": std_append,
    "readFile": std_read_file,
    "writeFile": std_write_file,
    "exit": std_exit,
}
