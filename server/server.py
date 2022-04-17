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

FORMAT = 'iso-8859-1'
DISCONNECT_MESSAGE = "DISCONNECT"


def GET(client, resource):
    content_type = mimetypes.guess_type(resource)[0]
    print(content_type)

    try:
        Func = open(resource, 'r') if "text" in content_type else open(resource, 'rb')
        content = Func.read()
        Func.close()
    except:
        send_status_code('NOT FOUND')
    send_status_code(client, 'OK', content)
def HEAD(client, resource):
    pass


def PUT(msg):
    pass


def POST(msg):
    pass

def send_status_code(client, ID, content ='', content_type = 'text/html'):
    if ID == 'BAD_REQUEST':
        print('[ERROR] Bad Request')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 400 Bad Request\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.sendall(response)
        client.close()
    elif ID == 'SERVER ERROR':
        print('[ERROR] Server Error')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 500 Server Error\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.sendall(response)
        client.close()
    elif ID == 'NOT FOUND':
        print('[ERROR] Resource not found')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 404 Not Found\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.sendall(response)
        client.close()
    elif ID == 'OK':
        print('Request OK')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 200 OK\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        client.send(response)
        client.send(content.encode())

def handle_result(result):
    pass

def handle_client(clientsocket, addr):  # Thread friendly way of handling one individual client
    try:
        print(f"[NEW CONNECTION] {addr[0]} connected")
        connected = True
        #clientsocket.settimeout(5)
        while connected:
            msg = b''
            while b'\r\n\r\n' not in msg:
                msg = msg + clientsocket.recv(1)
            raw_msg = msg[:-4].decode(FORMAT)   # recv() is a Blocking method, converts message into bytes -- decode() reconverts bytes to string
            print(f"[{addr[0]}] {msg}")
            clientsocket.send(bytes(connected))
            lines = raw_msg.splitlines()
            first_line = lines[0]
            if len(first_line.split()) != 3:
                send_status_code(clientsocket, 'BAD_REQUEST')
            command = first_line.split()[0]
            resource = first_line.split()[1]
            if resource == '/':
                resource = 'server.html'
            elif resource[0] =='/':
                resource = resource[1:]
            HTTPVersion = first_line.split()[2]
            if HTTPVersion != 'HTTP/1.1':
                send_status_code(clientsocket, 'BAD_REQUEST')
            second_line = lines[1]
            if second_line.split()[0] != 'Host:':
                send_status_code(clientsocket, 'BAD_REQUEST')
            elif second_line.split()[1] != f'{local_ip}:{PORT}':
                send_status_code(clientsocket, 'BAD_REQUEST')
            if "GET" == command:
                result = GET(clientsocket, resource)
            elif "HEAD" == command:
                result = HEAD(clientsocket,resource)
            elif "PUT" == command:

                result = PUT(clientsocket,resource)
            elif "POST" == command:

                result = POST(raw_msg)
            else:
                print('Wrong command')
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
