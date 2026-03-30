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

STDLIB = {
    "print": std_print,
    "connect": std_connect,
    "udp_connect": std_udp_connect,
    "send": std_send,
    "recv": std_recv,
    "toString": std_tostring,
    "toInt": std_toint,
    "len": std_len,
    "append": std_append,
}
