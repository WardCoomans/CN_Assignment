import socket
import threading
from email.utils import formatdate, parsedate
from http import HTTPStatus
import mimetypes
import traceback

hostname = socket.gethostname()  # Get hostname = Name of Computer
local_ip = socket.gethostbyname(hostname)  # Get IP-address of machine
print(local_ip)

SERVER = local_ip  # Dynamic IP grab (not hardcoded)
PORT = 5050  # High port number

# Create socket for the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Identifies clients by their ipv4 address (AF_INET) /
# SOCK.STREAM (How data will be communicated)

# Bind the socket with our IP-address and port
ADDR = (SERVER, PORT)
server.bind(ADDR)  # Bind the two together: Anything that connects to the IP and PORT will hit the server socket

FORMAT = 'iso-8859-1'  # Only translates bytes to text, not compatible for images (TODO: find different format)
DISCONNECT_MESSAGE = "DISCONNECT"


def GET(msg):
    pass


def HEAD(msg):
    pass


def PUT(msg):
    pass


def POST(msg):
    pass

def send_status_code(client, ID):
    if ID == 'BAD_REQUEST':
        print('[ERROR] Bad Request')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 400 Bad Request\r\nDate: {date}\r\nContent-Type: text/html\r\nContent-Length: 0\r\n\r\n".encode()
        print(response)
        client.sendall(response)
        client.close()
    elif ID == 'SERVER ERROR':
        print('[ERROR] Server Error')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 500 Server Error\r\nDate: {date}\r\nContent-Type: text/html\r\nContent-Length: 0\r\n\r\n".encode()
        print(response)
        client.sendall(response)
        client.close()
def handle_result(result):
    pass

def handle_client(clientsocket, addr):  # Thread friendly way of handling one individual client
    try:
        print(f"[NEW CONNECTION] {addr[0]} connected")
        connected = True
        clientsocket.settimeout(5)
        while connected:
            msg = b''
            while b'\r\n\r\n' not in msg:
                msg = msg + clientsocket.recv(1)
            raw_msg = msg[:-4].decode(FORMAT)   # recv() is a Blocking method, converts message into bytes -- decode() reconverts bytes to string
            print(f"[{addr[0]}] {msg}")
            clientsocket.send(bytes(connected))
            if "GET" in raw_msg:
                result = GET(raw_msg)
            elif "HEAD" in raw_msg:
                result = HEAD(raw_msg)
            elif "PUT" in raw_msg:
                result = PUT(raw_msg)
            elif "POST" in raw_msg:
                result = POST(raw_msg)
            else:
                print('GOT TESTING CASE')
                send_status_code(clientsocket,'BAD_REQUEST')
                break
            handle_result(result)
        print(f"[CLOSE CONNECTION] {addr[0]} disconnected")
        clientsocket.close()
    except:
        send_status_code(clientsocket,'SERVER ERROR')


# Start our server -- Handle new clients, and distribute over threads
def start():
    server.listen()  # Server should be listening for clients
    while True:
        clientsocket, addr = server.accept()  # Accept clients (Blocking method, TODO: Threading)
        thread = threading.Thread(target=handle_client, args=(clientsocket, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")  # Amount of clients = Amount of threads - start


print("[STARTING] Server is starting...")
start()
