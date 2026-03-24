# N
*It's just N*

**Overview**
**N** is a minimalistic scripting language designed for buffer manipulation and simple networking.
It supports **TCP/UDP** connections, sending/receiving raw byte buffers, basic contro flow, and printing.

---

## Features (v0.1)
- **Buffers:** Allocate and manipulate arrays of bytes.
- **TCP & UDP:** Connect, send, and receive data.
- **Control Flow:** `if` statements and `loop` loops.
- **Operators:** `+ - * / == != < > <= >=`
- **Printing:** Output variables or strings.

---

### Syntax
**Buffers**
```n
buf = buffer 4
buf[0] = 10
buf[1] = 20
```

**TCP & UDP**
```n
connect "127.0.0.1" 9998
send buf
tcp_echo = recv 4

udp_connect "127.0.0.1" 9999
send buf
udp_echo = recv 4
```

**Control Flow**
```n
if buf[0] == 10
        print "Buffer starts with 10"

i = 0
loop i < 5
        send buf
        i = i + 1
```

**Printing**
```n
print "Hello, N!"
print buf[0]
```

**Running Scripts**
```bash
python3 main.py your_script.n
```

**Roadmap**

- v0.1 - Basic language + networking + buffers
- v0.2 - Functions, more operators, better error messages
- v0.3 - File I/O, modules