#!/usr/bin/python
import socket
import select
import sys
import http_server1


def connect(port):
    accept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    accept_socket.setblocking(0)  # Non-blocking
    accept_socket.bind(('', port))
    accept_socket.listen(5)
    print 'The server is ready to receive.'
    inputs = [accept_socket]  # Sockets from which we expect to read
    # Main loop
    while inputs:
        print '\nwaiting for the next event.'
        readable, writable, exceptional = select.select(inputs, [], inputs)
        for s in readable:
            if s is accept_socket:
                connection_socket, addr = s.accept()  # addr is the address /
                # bound to the socket on the other end of the connection
                connection_socket.setblocking(1)  # reset connect_socket to allow blocking
                inputs.append(connection_socket)
            else:  # s is a connection socket
                rqst = http_server1.get_request(s)
                if rqst:
                    path = http_server1.parse(rqst)
                    res = http_server1.response(path)
                    s.send(res)
                    print 'Response sent.'
                s.close()
                print 'Socket closed.'
                inputs.remove(s)
        for s in exceptional:
            # Stop listening for input on the connection
            inputs.remove(s)
            s.close()


connect(int(sys.argv[1]))
