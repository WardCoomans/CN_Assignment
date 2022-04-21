import socket
import threading
from email.utils import formatdate, parsedate
import os
import datetime
from datetime import datetime
import mimetypes

hostname = socket.gethostname()  # Get hostname = Name of Computer
local_ip = socket.gethostbyname(hostname)  # Get IP-address of machine
print(local_ip)

SERVER = local_ip  # Dynamic IP grab (not hardcoded)
PORT = 8080  # High port number

# Create socket for the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Identifies clients by their ipv4 address (AF_INET) /
# SOCK.STREAM (How data will be communicated)

# Bind the socket with our IP-address and port
ADDR = (SERVER, PORT)
server.bind(ADDR)  # Bind the two together: Anything that connects to the IP and PORT will hit the server socket

FORMAT = 'iso-8859-1'

global connected


def GET(client, resource):
    content_type = mimetypes.guess_type(resource)[0]    # Guess content type, e.g. text/html or image/jpeg
    print(content_type)
    if content_type is None:
        print(['ERROR contenttype not found, using text/html'])  # Use text/html as default
        content_type = 'text/html'
    try:
        Func = open(resource, 'rb')
        content = Func.read()
        Func.close()
        send_status_code(client, 'OK', content, content_type, resource)  # Everything went well, send OK status including the body content to be sent
    except:
        send_status_code(client, 'NOT FOUND')


def HEAD(client, resource):
    content_type = mimetypes.guess_type(resource)[0]
    print(content_type)
    if content_type is None:
        print(['ERROR contenttype not found, using text/html'])
        content_type = 'text/html'
    try:
        Func = open(resource, 'rb') if "text" in content_type else open(resource, 'rb')
        content = Func.read()
        Func.close()
        send_status_code(client, 'OKHeader', content, content_type)     # Everything went well, send OK Status including the header content to be sent
    except:
        send_status_code(client, 'NOT FOUND')


def PUT(client, resource, length, content_type):
    try:
        message = b''   # Message from client is received as a byte string
        while length > 0:
            if length > 1024:
                part = client.recv(1024)    # Receive client message per ~kilobyte (same principle as with client.py)
            else:
                part = client.recv(length)
            length -= len(part)
            message += part
        Func = open(resource, 'w')          # Create a file to write in, with resource as its path (filename)
        Func.write(message.decode(FORMAT))  # Write the message to the file
        Func.close()
        send_status_code(client, 'CREATED', b'', content_type)  # Send status code that the file was created
    except:
        send_status_code(client, 'SERVER ERROR')


def POST(client, resource, length, content_type):
    try:
        message = b''   # Message from client is received as a byte string
        while length > 0:
            if length > 1024:
                part = client.recv(1024)    # Same principle as PUT
            else:
                part = client.recv(length)
            length -= len(part)
            message += part
        Func = open(resource, 'a')          # Append to a file that already exists, with resource as its path (filename)
        Func.write(message.decode(FORMAT))  # Write the message to append to the file
        Func.close()
        send_status_code(client, 'CREATED', b'', content_type)  # Send status code that text was successfully appended
    except:
        send_status_code(client, 'SERVER ERROR')


def send_status_code(client, ID, content=b'', content_type="text/html", resource='/'):
    global connected    # content and content_type only needed in case of OK Status code

    # Bad response
    if ID == 'BAD REQUEST':     # If anything is wrong with the request given by the client, send this response
        print('[ERROR] Bad Request')
        date = formatdate(timeval=None, localtime=False, usegmt=True)   # Send the date at which the error occured
        response = f"HTTP/1.1 400 Bad Request\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode(FORMAT)
        print(response)
        client.sendall(response)
        client.close()
        connected = False

    elif ID == 'SERVER ERROR':  # If the server can't handle any of the given requests (PUT or POST)
        print('[ERROR] Server Error')   # or the handle_client function fails, send this response
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 500 Server Error\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode(FORMAT)
        print(response)
        client.sendall(response)
        client.close()
        connected = False

    elif ID == 'NOT FOUND':     # If the server can't find the contenttype needed (for GET or HEAD), send this response
        print('[ERROR] Resource not found')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 404 Not Found\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode(FORMAT)
        print(response)
        client.sendall(response)
        client.close()
        connected = False

    elif ID == 'NOT MODIFIED':
        print('[ERROR] Resource not modified since specified date')
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 304 Not Modified \r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode(FORMAT)
        print(response)
        client.sendall(response)
        client.close()
        connected = False

    # Good response
    elif ID == 'OK':    # In case of GET
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 200 OK\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {str(len(content))}\r\n\r\n".encode(FORMAT, errors='ignore')
        if isinstance(content, str):    # Check if content is in string format
            content = content.encode(FORMAT, errors='ignore')   # Encode the content as bytes to be streamed to client
        response += content     # Add body content (in byte format) to the response to be sent
        response += b'\r\n'     # Add endlines (CRLF)
        print(response)
        client.sendall(response)      # Send the content of the body

    elif ID == 'OKHeader':
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 200 OK\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode(FORMAT)
        print(response)         # Only header needs to be sent (includes length of content)
        client.send(response)

    elif ID == 'CREATED':
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        response = f"HTTP/1.1 201 CREATED\r\nDate: {date}\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode(FORMAT)
        print(response)
        client.send(response)


def handle_client(clientsocket, addr):  # Thread friendly way of handling one individual client
    try:            # Put everything in a try, so that the server doesn't crash when an error occurs
        print(f"[NEW CONNECTION] {addr[0]} connected \r\n")
        global connected
        connected = True
        clientsocket.settimeout(20)     # Set a connection timeout for the socket after 20 seconds

        while connected:    # Main loop for the client
            msg = b''
            while b'\r\n\r\n' not in msg:   # Receive the header (from client message)
                msg = msg + clientsocket.recv(1)  # recv() is a Blocking method, converts message into bytes --
            raw_msg = msg[:-4].decode(FORMAT)  # -- decode() reconverts bytes to string

            print(f"[{addr[0]}] {msg}")

            # Weed out the bad requests
            lines = raw_msg.splitlines()
            if len(lines) < 1:  # Header must have at least one line, else it's a bad request
                send_status_code(clientsocket, 'BAD REQUEST')
                break

            first_line = lines[0]   # Contains Command[0], Resource[1] and HTTP-Version[2]
            if len(first_line.split()) != 3:    # If does not contain these 3 elements, bad request
                send_status_code(clientsocket, 'BAD REQUEST')
                break

            command = first_line.split()[0]     # GET, HEAD, PUT or POST
            resource = first_line.split()[1]    # Everything after and including '/'

            if resource == '/':     # Index page requested
                resource = 'server.html'

            elif resource[0] == '/':    # Specific resource of server requested
                resource = resource[1:]     # Grab everything after the '/'

            HTTPVersion = first_line.split()[2]     # Check HTTP-Version, if not HTTP/1.1: Bad request
            if HTTPVersion != 'HTTP/1.1':
                send_status_code(clientsocket, 'BAD REQUEST')
                break

            host_header_found = False   # Set False, will be set to True if found in loop below
            if_modified_header = None
            content_length_header = None
            content_type_header = None
            connection_header = None

            for elem in lines[1:]:  #
                if elem == '':  # Done, header is parsed
                    break

                if len(elem.split(": ")) != 2:      # Header-type: Value (e.g. Content-Length: length)
                    send_status_code(clientsocket, 'BAD REQUEST')   # If does not contain 2 elements, bad request
                    break

                if 'Host: ' in elem:    # We check the Host: IP-address: PORT
                    host_header_found = True
                    if elem.split()[1] != f'{local_ip}:{PORT}':  # Check if actual connection corresponds to request
                        send_status_code(clientsocket, 'BAD REQUEST')
                        break

                elif 'If-Modified-Since' in elem:  # Check if these headers are present, if so assign them to a variable
                    if_modified_header = elem
                elif 'Content-Length' in elem:
                    content_length_header = elem
                elif 'Content-Type' in elem:
                    content_type_header = elem
                elif 'Connection: ' in elem:
                    connection_header = elem

            if not host_header_found:   # If the host header is still not found, request is bad
                send_status_code(clientsocket, 'BAD REQUEST')
                break

            # Begin the actual command handling
            if "GET" == command:
                if if_modified_header is not None:  # If if-modified header is present,
                    try:  # Analyse the time since modification
                        parsed_date = parsedate(if_modified_header.split(': ')[1])
                        date_to_check = datetime.datetime(parsed_date[0], parsed_date[1], parsed_date[2], parsed_date[3],
                                                          parsed_date[4], parsed_date[5], 0).timestamp()
                        last_modified_date = os.path.getmtime(resource)  # Check last modified of resource we're checking
                        print(date_to_check)
                        print(last_modified_date)
                        if date_to_check > last_modified_date:
                            send_status_code(clientsocket, 'NOT MODIFIED')
                            break
                    except:
                        send_status_code(clientsocket, 'BAD REQUEST')
                        break

                GET(clientsocket, resource)  # Perform GET
                if not connected:  # eigenlijk onnodig
                    break

            elif "HEAD" == command:     # Same as GET
                if if_modified_header is not None:
                    try:
                        parsed_date = parsedate(if_modified_header.split(': ')[1])
                        date_to_check = datetime.datetime(parsed_date[0], parsed_date[1], parsed_date[2], parsed_date[3],
                                                          parsed_date[4], parsed_date[5], 0).timestamp()
                        last_modified_date = os.path.getmtime(resource)
                        print(date_to_check)
                        print(last_modified_date)
                        if date_to_check > last_modified_date:
                            send_status_code(clientsocket, 'NOT MODIFIED')
                            break

                    except:
                        send_status_code(clientsocket, 'BAD REQUEST')
                        break
                HEAD(clientsocket, resource)
                if not connected:
                    break

            elif "PUT" == command:
                if content_length_header is None:   # Check if Content Length info is available, else bad request
                    send_status_code(clientsocket, 'BAD REQUEST')
                    break
                length = int(content_length_header.split(": ")[1])  # Grab the length of the content
                if content_type_header is None:     # Check if Content type info is available, else bad request
                    send_status_code(clientsocket, 'BAD REQUEST')
                    break
                content_type = content_type_header.split(': ')[1]   # Assign the content type to a variable (TE. or CL.)
                PUT(clientsocket, resource, length, content_type)
                if not connected:
                    break

            elif "POST" == command:  # Same principle as PUT
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

            else:   # Command is invalid -- Bad request
                send_status_code(clientsocket, 'BAD REQUEST')
            if connection_header is not None and 'close' in connection_header.split(': ')[1]:
                print(f"[CLOSE CONNECTION] {addr[0]} disconnected")
                clientsocket.close()
                break

    except:
        send_status_code(clientsocket, 'SERVER ERROR')  # Catch any possible server errors, and close the client socket


# Start our server -- Handle new clients, and distribute over threads
def start():
    server.listen()  # Server should be listening for clients
    while True:
        clientsocket, addr = server.accept()  # Accept clients (Blocking method -- Fixed with threading)
        thread = threading.Thread(target=handle_client, args=(clientsocket, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")  # Amount of clients = Amount of threads - start


print("[STARTING] Server is starting...")
start()