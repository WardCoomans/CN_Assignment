import socket
from bs4 import BeautifulSoup
from email.utils import formatdate
SERVER = None
PORT = None
ADDR = None
FORMAT = 'iso-8859-1'


def get_header_and_content_type(client):
    header = bytes()
    while b'\r\n\r\n' not in header:    # As long as the CRLF (control characters) is not found, receive until end of header
        header = header + client.recv(1)
    raw_header = header[:-4].decode(FORMAT)   # Everyting except the newlines at the end of the header is the actual header
    print("[RECEIVED]")
    print(raw_header)   # Contains: HTTP-version, Status code, Date, Server type, Length of content and Content-Type

    info = raw_header.splitlines()  # \n in raw text header splitted, for easier reading in console (list of strings)
    for elem in info:
        if 'Transfer-Encoding' in elem:     # Handles chunked T.E. (better use of persistent TCP connections)
            contenttype = 'Transfer-Encoding'   # Chunked allows for streaming within a single request/response
            length = 0
            return contenttype, length
        elif 'Content-Length' in elem:
            contenttype = 'Content-Length'
            length = int(elem.split()[1])   # Grab the int (length) after Content-length: ...
            return contenttype, length


def get_body(contenttype, length, client):
    if 'Transfer-Encoding' in contenttype:      # Body will be received as chunks (Transfer Encoded)
        body = b''                              # Keep the entire body as a byte string
        while True:

            data = b''                          # Figure out length of first chunk
            first = True
            while b'\r\n' not in data:          # Chunk has a specific header, containing length of chunk (hex value)
                test = client.recv(1)           # Receive one byte of body
                if first and test == b'\r':     # Remove trailing CRLF (not part of the chunk data)
                    client.recv(1)
                else:
                    data += test
                first = False

            chunk_length = int(data, 16)        # Length (hex value) casted to int value
            if chunk_length == 0:               # Last chunk: end of body
                break
            remaining = chunk_length
            while remaining > 0:                # Same principle as with Content-Length below
                if remaining > 1024:
                    part = client.recv(1024)
                    remaining -= len(part)
                    body += part
                else:
                    part = client.recv(remaining)
                    remaining -= len(part)
                    body += part

    elif 'Content-Length' in contenttype:       # Body is content-Length: length bytes long
        remaining = length
        body = b''                          # Keep the entire body as a byte string
        while remaining > 0:                # Keep receiving until remaining length of body has been completely parsed
            if remaining > 1024:
                part = client.recv(1024)    # Receive per ~kilobyte
                remaining -= len(part)
                body += part
            else:
                part = client.recv(remaining)   # Less than a kilobyte left, receive what is remaining
                remaining -= len(part)
                body += part

    else:           # In case of error with the header, return empty body
        print("Something went wrong with the headertype")
        body = ''
    return body


def send_request(command, ADDR, resource):      # Main function communicating with the host
    client.connect(ADDR)

    if command == 'GET':
        #   Sending the request
        print("[SENT]")
        request = f'GET /{resource} HTTP/1.1\r\nHost: {ADDR[0]}:{ADDR[1]} \r\n\r\n'.encode(FORMAT)  # Put request as bytes
        print(request)
        client.sendall(request)         # Send the request to the Host (in byte format) via the socket object

        contenttype, length = get_header_and_content_type(client)   # Returns body size type (TE. or CL.) + length of body
        body = get_body(contenttype, length, client)                # Returns entire body (as bytestring) of the HTML webpage
        bs = BeautifulSoup(body.decode(encoding=FORMAT), 'lxml')    # Decode the body of the html webpage

        #   Creating the parsed webpage
        hostname = URI.split('.')[1]
        file = open(f"{hostname}.html", "wb")   # Save the webpage as an html "Writing bytes" file
        file.write(bs.prettify('iso-8859-1'))   # Write the bs body (body in html code format) to the file
        file.close()

        #   Images
        images = bs.findAll('img')  # Find all images using the HTML 'img' tag - Returns list of <img/>
        internal_images = []
        external_images = []

        for elem in images:
            if elem.get('src') is None:     # Not an image (no path after src=)
                pass
            elif ':' in elem.get('src'):    # colon means external image (http: or www. or https:)
                external_images.append(elem.get('src'))
            else:                           # internal image
                internal_images.append(elem.get('src'))
                request = f'GET /{elem.get("src")} HTTP/1.1\r\nHost: {ADDR[0]}:{ADDR[1]} \r\n\r\n'.encode(FORMAT)
                print('[SENT]')
                print(request)
                client.sendall(request)     # Send request for the image from the host server
                contenttype, length = get_header_and_content_type(client)
                image = get_body(contenttype, length, client)
                imgFile = open(str(elem.get('src').split('/')[-1]), 'wb')    # Save name of image from image src (only last part of the absolute path)
                imgFile.write(image)
                imgFile.close()
            new_source = elem['src'].split("/")[-1]
            elem['src'] = new_source
        print(images)
        print("Amount of all images: " + str(len(images)))
        print("Amount of external images: " + str(len(external_images)))
        print(f"External images: {external_images}")
        print("Amount of internal images: " + str(len(internal_images)))
        print(f"Internal images:{internal_images}")

        for elem in external_images:    # Grab the external images using a seperate socket object
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as imagesocket:
                imghost = elem.split("//")[1].split("/")[0]
                imgresource = '/'.join(elem.split("//")[1].split("/")[1:])
                imgADDR = (imghost, 80)
                imagesocket.connect(ADDR)
                request = f'GET /{imgresource} HTTP/1.1\r\nHost: {imgADDR[0]}:{imgADDR[1]} \r\nConnection: closed\r\n\r\n'.encode(FORMAT)
                print('[SENT]')
                print(request)
                imagesocket.sendall(request)
                contenttype, length = get_header_and_content_type(imagesocket)
                image = get_body(contenttype, length, imagesocket)
                imgFile = open(str(elem.split('/')[-1]), 'wb')
                imgFile.write(image)
                imgFile.close()
                imagesocket.close()

        # Save everything in the parsed webpage
        file = open(f"{hostname}.html", "wb")
        file.write(bs.prettify('iso-8859-1'))
        file.close()
        print("Client disconnecting. Server terminated connection to this client")

    elif command == 'HEAD':     # Cfr. with GET but only the header is posted to the terminal
        print('[SENT]')
        request = f'HEAD /{resource} HTTP/1.1\r\nHost: {ADDR[0]}:{ADDR[1]} \r\n\r\n'.encode(FORMAT)
        print(request)
        client.sendall(request)
        header = get_header_and_content_type(client)
        print(header)
        client.close()
        print("Client disconnecting. Server terminated connection to this client")

    elif command == 'PUT':
        msg = input("Give PUT input: ")     # Store this msg into a newly created file (through /resource given by user) when connected to server.py
        request = f"PUT /{resource} HTTP/1.1\r\nHost: {ADDR[0]}:{ADDR[1]}\r\nContent-Type: text/html\r\nContent-Length: {len(msg)}\r\n\r\n{msg}\r\n".encode(FORMAT)
        client.sendall(request)
        header, content_type = get_header_and_content_type(client)
        print(header)
        client.close()
        print("Client disconnecting. Server terminated connection to this client")

    elif command == 'POST':
        msg = input("Give POST input: ")    # Store an extra msg into an existing file (through /resource given by user) when connected to server.py
        request = f"POST /{resource} HTTP/1.1\r\nHost: {ADDR[0]}:{ADDR[1]}\r\nContent-Type: text/html\r\nContent-Length: {len(msg)}\r\n\r\n{msg}\r\n".encode(FORMAT)
        client.sendall(request)     # Content-Type: ... is used when POSTing non-binary or small-sized data (one query-string)
        header, content_type = get_header_and_content_type(client)
        print(header)
        client.close()
        print("Client disconnecting. Server terminated connection to this client")

    else:
        # for testing purposes
        print("IN TESTING CASE")
        request = f"POR / HTTP/1.1\r\nHost: {ADDR[0]}:{ADDR[1]}\r\n\r\n".encode(FORMAT)
        print(request)
        client.sendall(request)
        response = client.recv(1024)
        print(response)
        client.close()


while True:  # Keep checking for new commands (after the last connection has ended)
    command = input("Enter the command you wish to execute: ")
    URI = input("Enter the URI to which you want to execute the command: ")
    port = int(input("Enter the port of the server, if you don't know this, use 'None': "))
    resource = '/'.join(URI.split("/")[1:])     # Everything from the '/' is the resource of the host page
    host = URI.split('/')[0]                    # Everything before the '/' is the host page
    print(host)
    print(resource)
    ADDR = (host,port)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create client socket object
    send_request(command, ADDR, resource)  # Send the command and corresponding address en resource to the function
