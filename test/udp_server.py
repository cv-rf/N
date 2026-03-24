import socket

HOST = '127.0.0.1'
PORT = 9999

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, PORT))
    print(f"UDP echo server listening on {HOST}:{PORT}")

    while True:
        data, addr = s.recvfrom(1024)
        print(f"UDP received from {addr}: {list(data)}")
        s.sendto(data, addr)