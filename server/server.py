import socket
import threading
from email.utils import formatdate, parsedate
import os
import datetime
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

global connected

def GET(client, resource):
    content_type = mimetypes.guess_type(resource)[0]
    print(content_type)
    if content_type is None:
        print(['ERROR contenttype not found, using text/html'])
        content_type = 'text/html'
    try:
        Func = open(resource, 'r') if "text" in content_type else open(resource, 'rb')
        content = Func.read()
        Func.close()
        send_status_code(client, 'OK', content, content_type)
    except:
        send_status_code(client,'NOT FOUND')


def HEAD(client, resource):

    content_type = mimetypes.guess_type(resource)[0]
    print(content_type)
    if content_type is None:
        print(['ERROR contenttype not found, using text/html'])
        content_type = 'text/html'
    try:
        Func = open(resource, 'r') if "text" in content_type else open(resource, 'rb')
        content = Func.read()
        Func.close()
        send_status_code(client, 'OKHeader', content, content_type)
    except:
        send_status_code(client, 'NOT FOUND')


def PUT(client,resource, length,content_type):
    try:
        message = b''
        while length > 0:
            if length > 1024:
                part = client.recv(1024)
            else:
                part = client.recv(length)
            length -= len(part)
            message += part
        Func = open(resource,'w')
        Func.write(message.decode(FORMAT))
        Func.close()
        send_status_code(client, 'CREATED',"",content_type)
    except:
        send_status_code(client, 'SERVER ERROR')


def POST(client, resource, length, content_type):

    try:
        message = b''
        while length > 0:
            if length > 1024:
                part = client.recv(1024)
            else:
                part = client.recv(length)
            length -= len(part)
            message += part
        Func = open(resource,'a')
        Func.write(message.decode(FORMAT))
        Func.close()
        send_status_code(client, 'CREATED',"",content_type)
    except:
        send_status_code(client, 'SERVER ERROR')

def send_status_code(client, ID, content ="", content_type = "text/html"):
    global connected

    if ID == 'BAD_REQUEST':
        print('[ERROR] Bad Request')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 400 Bad Request\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.sendall(response)
        client.close()
        connected = False
    elif ID == 'SERVER ERROR':
        print('[ERROR] Server Error')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 500 Server Error\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.sendall(response)
        client.close()
        connected = False
    elif ID == 'NOT FOUND':
        print('[ERROR] Resource not found')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 404 Not Found\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.sendall(response)
        client.close()
        connected = False
    elif ID == 'NOT MODIFIED':
        print('[ERROR] Resource not modified since specified date')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 304 Not Modified \r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.sendall(response)
        client.close()
        connected = False
    elif ID == 'OK':
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 200 OK\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.send(response)
        if isinstance(content,str):
            client.sendall(content.encode())
        elif isinstance(content,bytes):
            client.sendall(content)
    elif ID == 'OKHeader':
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 200 OK\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.send(response)
    elif ID == 'CREATED':
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 201 CREATED\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
        print(response)
        client.send(response)

def handle_client(clientsocket, addr):  # Thread friendly way of handling one individual client
    #try:
    print(f"[NEW CONNECTION] {addr[0]} connected")
    global connected
    connected = True
    clientsocket.settimeout(5)
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
            break
        command = first_line.split()[0]
        resource = first_line.split()[1]
        if resource == '/':
            resource = 'server.html'
        elif resource[0] == '/':
            resource = resource[1:]
        HTTPVersion = first_line.split()[2]
        if HTTPVersion != 'HTTP/1.1':
            send_status_code(clientsocket, 'BAD_REQUEST')
            break
        host_header_found = False
        if_modified_header = None
        content_length_header = None
        content_type_header = None
        for elem in lines[1:]:
            if elem == '':
                break
            if len(elem.split(": ")) != 2:
                send_status_code(clientsocket, 'BAD_REQUEST')
                break
            if 'Host: ' in elem:
                host_header_found = True
                if elem.split()[1] != f'{local_ip}:{PORT}':
                    send_status_code(clientsocket, 'BAD_REQUEST')
                    break
            elif 'If-Modified-Since' in elem:
                if_modified_header = elem
            elif 'Content-Length' in elem:
                content_length_header = elem
            elif 'Content-Type' in elem:
                content_type_header = elem

        if not host_header_found:
            send_status_code(clientsocket, 'BAD_REQUEST')
            break
        if "GET" == command:
            if if_modified_header is not None:
                try:
                    parsed_date = parsedate(if_modified_header.split(': ')[1])
                    date_to_check = datetime.datetime(parsed_date[0],parsed_date[1],parsed_date[2],parsed_date[3],parsed_date[4],parsed_date[5],0).timestamp()
                    last_modified_date = os.path.getmtime(resource)
                    print(date_to_check)
                    print(last_modified_date)
                    if date_to_check > last_modified_date:
                        send_status_code(clientsocket, 'NOT MODIFIED')
                        break

                except:
                    send_status_code(clientsocket, 'BAD_REQUEST')
                    break

            GET(clientsocket, resource)
            if not connected:                   #eigenlijk onnodig
                break
        elif "HEAD" == command:
            if if_modified_header is not None:
                try:
                    parsed_date = parsedate(if_modified_header.split(': ')[1])
                    date_to_check = datetime.datetime(parsed_date[0],parsed_date[1],parsed_date[2],parsed_date[3],parsed_date[4],parsed_date[5],0).timestamp()
                    last_modified_date = os.path.getmtime(resource)
                    print(date_to_check)
                    print(last_modified_date)
                    if date_to_check > last_modified_date:
                        send_status_code(clientsocket, 'NOT MODIFIED')
                        break

                except:
                    send_status_code(clientsocket, 'BAD_REQUEST')
                    break
            HEAD(clientsocket,resource)
            if not connected:
                break
        elif "PUT" == command:
            if content_length_header is None:
                send_status_code(clientsocket, 'BAD REQUEST')
                break
            length = int(content_length_header.split(": ")[1])
            if content_type_header is None:
                send_status_code(clientsocket, 'BAD REQUEST')
                break
            content_type = content_type_header.split(': ')[1]
            PUT(clientsocket, resource, length, content_type)
            if not connected:
                break
        elif "POST" == command:
            if content_length_header is None:
                send_status_code(clientsocket, 'BAD REQUEST')
                break
            length = int(content_length_header.split(": ")[1])
            if content_type_header is None:
                send_status_code(clientsocket, 'BAD REQUEST')
                break
            content_type = content_type_header.split(': ')[1]
            POST(clientsocket, resource, length, content_type)
            if not connected:
                break
        else:
            send_status_code(clientsocket,'BAD_REQUEST')

    print(f"[CLOSE CONNECTION] {addr[0]} disconnected")
    clientsocket.close()
    #except:
    #    send_status_code(clientsocket,'SERVER ERROR')


# Start our server -- Handle new clients, and distribute over threads
def start():
    global connected
    server.listen()  # Server should be listening for clients
    while True:
        clientsocket, addr = server.accept()  # Accept clients (Blocking method, TODO: Threading)
        thread = threading.Thread(target=handle_client, args=(clientsocket, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")  # Amount of clients = Amount of threads - start


print("[STARTING] Server is starting...")
start()
