import socket

SERVER = "192.168.1.103"
PORT = 5055

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ADDR = (SERVER,PORT)

server.bind(ADDR)

HEADER = 64 #nog kijken naar specifieke grootte voor HTTP
FORMAT = 'utf-8'  #werkt niet voor images, ander format nog zoeken
DISCONNECT_MESSAGE = "DISCONNECT!"

def start():
    server.listen()
    while True:
        conn, addr = server.accept()
        print("[NEW CONNECTION]", addr[0], "connected.")
        connected = True
        while connected:
            msg = conn.recv(HEADER).decode(FORMAT).rstrip()
            print("[MESSAGE]",msg)
            if msg == DISCONNECT_MESSAGE:
                connected = False
            conn.send(bytes(connected))
        print("[CLOSE CONNECTION", addr[0], "disconnected.")
        conn.close()

print("[STARTING] server is starting...")
start()