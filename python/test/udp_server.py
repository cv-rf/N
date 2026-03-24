import socket

HOST = "127.0.0.1"
PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print(f"UDP server listening on {HOST}:{PORT}")

while True:
    data, addr = sock.recvfrom(1024)  # buffer size
    print(f"Received from {addr}: {list(data)}")

    reply = bytes([x for x in data])
    sock.sendto(reply, addr)