import socket
from bs4 import BeautifulSoup

SERVER = None
PORT = None
ADDR = None
FORMAT = 'iso-8859-1'
HEADER = 1024
req_msg = 'GET / HTTP/1.1' + '\r\nHost:' + str(SERVER) + '\r\n\r\n'


def get_header_and_content_type():
    header = bytes()
    while b'\r\n\r\n' not in header:    # As long as the CLRF is not found, receive until end of header
        header = header + client.recv(1)
    raw_header = header[:-4].decode(FORMAT)   # Everyting except the newlines at the end of the header is the actual header
    print("[RECEIVED]")
    print(raw_header)
    info = raw_header.splitlines()  # \n in raw text header splitted, for easier reading in console
    for elem in info:
        if 'Transfer-Encoding' in elem:
            contenttype = 'Transfer-Encoding'
            length = 0
            return contenttype, length
        elif 'Content-Length' in elem:
            contenttype = 'Content-Length'
            length = int(elem.split()[1])
            return contenttype, length


def get_body(contenttype,length):
    if 'Transfer-Encoding' in contenttype:
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
                    body += part
                else:
                    part = client.recv(remaining)
                    remaining -= len(part)
                    body += part


    elif 'Content-Length' in contenttype:
        remaining = length
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
    return body

def send_request(command, ADDR, resource):
    client.connect(ADDR)
    print("[SENT]")
    request = f'GET /{resource} HTTP/1.1\r\nHost: {ADDR[0]}:{ADDR[1]} \r\n\r\n'.encode(FORMAT)  # Put request as bytes
    print(request)
    client.sendall(request)
    contenttype, length = get_header_and_content_type()


    if command == 'GET':
        body = get_body(contenttype,length)
        bs = BeautifulSoup(body, 'html.parser')
        images = bs.findAll('img')
        internal_images = []
        external_images = []

        for elem in images:
            if elem.get('src') == None:
                pass
            elif ':' in elem:
                external_images.append(elem.get('src'))
            else:
                internal_images.append(elem.get('src'))
                request = f'GET /{elem.get("src")} HTTP/1.1\r\nHost: {ADDR[0]}:{ADDR[1]} \r\n\r\n'.encode(FORMAT)
                print(request)
                client.sendall(request)
                contenttype, length = get_header_and_content_type()
                image = get_body(contenttype,length)
                Func = open(str(elem.get('src').split('/')[-1]),'wb')
                Func.write(image)
                Func.close
            new_source = elem['src'].split("/")[-1]
            elem['src']= new_source
        print(images)
        print(len(images))
        print(external_images)
        print(internal_images)
        print(len(internal_images))
        for elem in external_images:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as imagesocket:
                host = elem.split("//")[1].split("/")[0]
                resource = elem.split("//")[1].split("/")[1:]
                ADDR = (host,80)
                imagesocket.connect(ADDR)
                request = f'GET /{resource} HTTP/1.1\r\nHost: {ADDR[0]}:{ADDR[1]} \r\n\r\n'.encode(FORMAT)
                imagesocket.sendall(request)
                contenttype,length = get_header_and_content_type()
                image = get_body(contenttype,length)
                Func = open(str(elem.get('src').split('/')[-1]),'wb')
                Func.write(image)
                Func.close()
                imagesocket.close()

        Func = open("Assignment-CN.html", "wb", encoding ='iso-8859-1')
        Func.write(str(bs))
        #Func.write(body)
        Func.close()
        client.close()
        print("Client terminating. Server terminated connection to this client")

    elif command == 'HEAD':
        request = "HEAD / HTTP/1.1\r\nHost: {}\r\n\r\n".format(SERVER)      # TODO: ipv .format(...) kan je f-strings gebruiken (korter)
        client.send(request.encode(FORMAT))
        client.close()
        print("Client terminating. Server terminated connection to this client")

    elif command == 'POST':
        msg = input("Give POST input: ")
        request = "POST / HTTP/1.1\r\nHost: {}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {}\r\n\r\n{}\r\n".format(
            SERVER, len(msg), msg)
        client.send(request.encode(FORMAT))
        client.close()
        print("Client terminating. Server terminated connection to this client")

    elif command == 'PUT':
        msg = input("Give PUT input: ")
        request = "PUT  HTTP/1.1\r\nHost: {}\r\nContent-Type: text/html\r\nContent-Length: {}\r\n\r\n{}\r\n".format(
            SERVER, len(msg), msg)
        client.send(request.encode(FORMAT))
        client.close()
        print("Client terminating. Server terminated connection to this client")


while True:  # Keep checking for new commands (after the last connection has ended)
    command = input("Enter the command you wish to execute: ")
    URI = input("Enter the URI to which you want to execute the command: ")
    port = int(input("Enter the port of the server, if you don't know this, use 'None': "))
    resource ='/'.join(URI.split("/")[1:])
    host = URI.split('/')[0]
    print(host)
    print(resource)
    ADDR = (host,port)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_request(command, ADDR, resource)  # Send the command and corresponding URL to the function
