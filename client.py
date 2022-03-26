import socket
from bs4 import BeautifulSoup

SERVER = None
PORT = None
ADDR = None
FORMAT = 'iso-8859-1'
HEADER = 1024
req_msg = 'GET / HTTP/1.1' + '\r\nHost:' + str(SERVER) + '\r\n\r\n'

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def send_request(command, URL):
    SERVER = URL
    print("[SENT]")
    print(('GET / HTTP/1.1 \r\nHost:' + str(SERVER) + '\r\n\r\n').encode(FORMAT))
    request = bytes(('GET / HTTP/1.1 \r\nHost:' + str(SERVER) + '\r\n\r\n').encode(FORMAT))
    sent = 0
    while sent < len(req_msg):
        sent = sent + client.send(request[sent:])
    header = bytes()
    while b'\r\n\r\n' not in header:
        header = header + client.recv(1)
    raw_header = header[:-4].decode()
    print("[RECEIVED]")
    print(raw_header)

    lines = raw_header.splitlines()
    index_headertype = len(lines) - 1
    headertype = lines[index_headertype]

    if command == 'GET':
        if 'Transfer-Encoding' in headertype:
            body = b''
            while True:
                data = b''
                first = True
                while b'\r\n' not in data:
                    test = client.recv(1)
                    if first and test == b'\r':
                        client.recv(1)
                    else:
                        data += test
                    first = False
                chunk_length = int(data, 16)  # hexadecimal omzetten naar int
                if chunk_length == 0:
                    break
                remaining = chunk_length
                while remaining > 0:
                    if remaining > 1024:
                        part = client.recv(1024)
                        remaining -= len(part)
                        body+=part
                    else:
                        part = client.recv(remaining)
                        remaining -= len(part)
                        body+=part


        elif 'Content-Length' in headertype:
            remaining = int(headertype.split()[1])
            body = b''
            while remaining > 0:
                if remaining > 1024:
                    body += client.recv(1024)
                    remaining -= 1024
                else:
                    body += client.recv(remaining)
                    remaining = 0
        else:
            print("Something went wrong with the headertype")

        Func = open("Assignment-CN.html","wb")
        Func.write(body)
        Func.close()
        client.close()
        print("Client terminating. Server terminated connection to this client")

    elif command == 'HEAD':
        request = "HEAD / HTTP/1.1\r\nHost: {}\r\n\r\n".format(SERVER)
        client.send(request.encode(FORMAT))
        client.close()
        print("Client terminating. Server terminated connection to this client")

    elif command == 'POST':
        msg = input("Give POST input: ")
        request = "POST / HTTP/1.1\r\nHost: {}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {}\r\n\r\n{}\r\n".format(SERVER,len(msg),msg)
        client.send(request.encode(FORMAT))
        client.close()
        print("Client terminating. Server terminated connection to this client")

    elif command == 'PUT':
        msg = input("Give PUT input: ")
        request = "PUT  HTTP/1.1\r\nHost: {}\r\nContent-Type: text/html\r\nContent-Length: {}\r\n\r\n{}\r\n".format(SERVER, len(msg), msg)
        client.send(request.encode(FORMAT))
        client.close()
        print("Client terminating. Server terminated connection to this client")

while True:
    command = input("Enter the command you wish to execute: ")
    server = input("Enter the URL to which you want to execute the command: ")
    port = int(input("Enter the port of the server, if you don't know this, use 'None': "))
    if ADDR != (server,port):
        SERVER = server
        PORT = port
        ADDR = (SERVER, PORT)
        client.connect(ADDR)
    send_request(command, server)

