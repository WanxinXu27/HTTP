#!/usr/bin/python
import socket
import os.path
import sys


def get_request(socket):  # Receive the request from the client
    rqst = ''
    while True:
        data = socket.recv(2048)
        if not data:
            break
        rqst += data
        if rqst[-4:] == "\r\n\r\n":
            break
    return rqst


def load_file(file_path):  # extract file content
    f = open(file_path, 'r')
    res = ''
    for line in f:
        res += line
    f.close()
    return res


def response(file_path):  # generate http response message
    res = 'HTTP/1.0 '
    if os.path.exists(file_path):
        if file_path.split('.')[-1] == 'html' or file_path.split('.')[-1] == 'htm':
            body = load_file(file_path)
            res += '200 OK\r\nConnection: close\r\nContent-Length: ' + str(len(body))
            res += '\r\nContent-Type: text/html\r\n\r\n'
            res += body
            return res
        else:
            res += '403 Forbidden\r\nConnection: close\r\n\r\n'
            return res
    else:
        res += '404 Not Found\r\nConnection: close\r\n\r\n'
        return res


def parse(sentence):  # parse http request and return file path
    path = sentence.split('\r\n')[0].split(' ')[1].split('/', 1)[1]
    return path


def connect(port):
    accept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    accept_socket.bind(('', port))
    accept_socket.listen(5)
    print 'The server is ready to receive.'
    while True:
        connection_socket, addr = accept_socket.accept()
        rqst = get_request(connection_socket)
        if rqst != '':  # If rqst is null, the client connection is closed.
            path = parse(rqst)
            res = response(path)
            connection_socket.send(res)
        connection_socket.close()
        print 'connection closed.'


if __name__ == '__main__':
    connect(int(sys.argv[1]))
