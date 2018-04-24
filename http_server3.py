#!/usr/bin/python
import socket
import select
import fcntl
import os.path
import os
import sys
import http_server1


def get_request_complete(socket, buffers, inputs):  # Read the HTTP request from the client
    req = ''
    while True:
        try:
            data = socket.recv(2048)
            req += data  # store request message
            if req[-4:] == "\r\n\r\n":  # get request complete
                break
        except IOError:
            buffers[socket][0] += req
            return False
    buffers[socket][0] += req
    inputs.remove(socket)
    return True


def load_file(fd, inputs, buffers, fd_sock, outputs):  # if loading file is complete, write response message
    # and put socket into outputs
    try:
        fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)  # set non-blocking IO
        buffers[fd_sock[fd]][1] += os.read(fd, os.fstat(fd).st_size)
        if os.lseek(fd, 0, os.SEEK_CUR) == os.fstat(fd).st_size:  # read complete
            if fd in inputs:
                inputs.remove(fd)
            body = buffers[fd_sock[fd]][1]  # response body
            buffers[fd_sock[fd]][2] += '200 OK\r\nConnection: close\r\nContent-Length: ' \
                                            + str(len(body))
            buffers[fd_sock[fd]][2] += '\r\nContent-Type: text/html\r\n\r\n'
            buffers[fd_sock[fd]][2] += body  # response message complete
            outputs.append(fd_sock[fd])
            del fd_sock[fd]
            os.close(fd)  # close file
            return
    except IOError:
        if fd not in inputs:
            inputs.append(fd)
        return


def connect(port):
    accept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    accept_socket.setblocking(0)  # No blocking for TCP handshake request
    accept_socket.bind(('', port))
    accept_socket.listen(5)
    print 'The server is ready to receive.'
    # Lists provided for select() syscall
    inputs = [accept_socket]  # Sockets and file descriptors from which we expect to read
    outputs = []  # Sockets to which we expect to write
    buffers = {}  # Buffers for read and write
    fd_sock = {}  # dict = {fd : socket}

    # Main loop
    while inputs:
        # print '\nwaiting for the next event'
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        for s in readable:
            if s is accept_socket:
                connection_socket, addr = s.accept()  # addr is the address /
                # bound to the socket on the other end of the connection
                # print 'new connection from' + str(addr)
                connection_socket.setblocking(0)
                inputs.append(connection_socket)
                buffers[connection_socket] = ['', '', '', 0]  # [0] for request, [1] for file, /
                # [2] for response, [3] for total_sent
            else:
                if type(s) != int:  # s is connection socket
                    if not get_request_complete(s, buffers, inputs):
                        continue
                    if buffers[s][0]:  # s has the whole request message
                        path = http_server1.parse(buffers[s][0])
                        buffers[s][2] += 'HTTP/1.0 '
                        if os.path.exists(path):
                            if path.split('.')[-1] == 'html' or path.split('.')[-1] == 'htm':  # we need to read a file
                                fd = os.open(path, os.O_RDONLY)  # get fd
                                fd_sock[fd] = s  # map fd to current socket
                                load_file(fd, inputs, buffers, fd_sock, outputs)
                            else:
                                buffers[s][2] += '403 Forbidden\r\nConnection: close\r\n\r\n'
                                outputs.append(s)
                        else:
                            buffers[s][2] += '404 Not Found\r\nConnection: close\r\n\r\n'
                            outputs.append(s)
                    else:
                        # Interpret empty result as closed connection
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()
                else:  # s is a file descriptor
                    load_file(s, inputs, buffers, fd_sock, outputs)
        for s in writable:
            total_sent = buffers[s][3]
            sent = 0
            while total_sent < len(buffers[s][2]):
                print (len(buffers[s][2]))
                try:
                    sent = s.send(buffers[s][2][total_sent:])  # returns how many bytes are sent
                  #  buffers[s][2] = buffers[s][2][total_sent:]  # docs.python.org/2/howto/sockets.html#socket-howto
                  #   print 'send OK = ' + str(s) + str(sent)
                    print "OK sent = " + str(sent)
                    total_sent += sent
                    print "OK total sent = " + str(total_sent)
                except IOError:
                    # print "IO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                    # print 'send bu ok = ' + str(s) + str(sent)
                    total_sent += sent
                    print "sent = " + str(sent)
                    print "total sent = " + str(total_sent)
                    #buffers[s][2] = buffers[s][2][total_sent:]
                    buffers[s][3] = total_sent
                    break
            # send complete
            if total_sent == len(buffers[s][2]):
                del buffers[s]
                outputs.remove(s)
                s.close()
        for s in exceptional:
            # Stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()


connect(int(sys.argv[1]))
