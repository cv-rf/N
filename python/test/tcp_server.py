import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 9999))
server.listen(1)
print("Listening on 127.0.0.1:9999...")

conn, addr = server.accept()
print(f"Connection from {addr}")
while True:
    data = conn.recv(1024)
    if not data:
        break
    print("Received:", list(data))
    # Echo back the data
    conn.sendall(data)
