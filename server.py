import socket
import threading

hostname = socket.gethostname()  # Get hostname = Name of Computer
local_ip = socket.gethostbyname(hostname)  # Get IP-address of machine
print(local_ip)

SERVER = local_ip  # Dynamic IP grab (not hardcoded)
PORT = 5055  # High port number

# Create socket for the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Identifies clients by their ipv4 address (AF_INET) /
# SOCK.STREAM (How data will be communicated)

# Bind the socket with our IP-address and port
ADDR = (SERVER, PORT)
server.bind(ADDR)  # Bind the two together: Anything that connects to the IP and PORT will hit the server socket

HEADER = 1024  # Size -- TODO: Check for specific size needed for HTTP
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


def handle_result(result):
    pass

def handle_client(clientsocket, addr):  # Thread friendly way of handling one individual client
    print(f"[NEW CONNECTION] {addr[0]} connected")
    connected = True
    while connected:
        msg = clientsocket.recv(HEADER).decode(FORMAT)  # Argument determines size of the client message
        # recv() is a Blocking method, converts message into bytes -- decode() reconverts bytes to string
        print(f"[{addr[0]}] {msg}")
        if msg == DISCONNECT_MESSAGE:
            connected = False
        clientsocket.send(bytes(connected))  # Send (True or False) reply to client after every message
        if "GET" in msg:
            result = GET(msg)
        elif "HEAD" in msg:
            result = HEAD(msg)
        elif "PUT" in msg:
            result = PUT(msg)
        elif "POST" in msg:
            result = POST(msg)
        else:
            pass
        #handle_result(result)
    print(f"[CLOSE CONNECTION] {addr[0]} disconnected")
    clientsocket.close()


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
