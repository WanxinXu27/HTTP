#!/usr/bin/python
import socket
import sys


def curl(socket, res):  # generate a curl-like output
    global redir_cnt
    status_code = res.split('\r\n')[0].split(' ')[1]
    if int(status_code) >= 400:
        print_resbody(res, socket)
        sys.exit(1)
    if status_code == '301' or status_code == '302':
        redir_cnt += 1
        if redir_cnt > 10:
            socket.close()
            sys.exit(1)
        tmp = res.split('\r\n\r\n')[0].split('\r\n')
        for i in tmp:
            if i.split(': ')[0] == 'Location':
                redir = i.split(': ')[-1]
                break
        print >> sys.stderr, 'Redirected to: ' + redir + '\n'
        socket.close()
        http_client(redir)
    print_resbody(res, socket)
    socket.close()
    sys.exit()


def receive(socket):
    res = ''
    while True:
        data = socket.recv(2048)
        if not data:
            break
        res += data
    return res


def print_resbody(res, client):  # print HTTP response body if applicable
    for i in res.split('\r\n\r\n')[0].split('\r\n'):
        if i.split(' ')[1] == 'text/html;' or i.split(' ')[1] == 'text/html':
            html = res.split('\r\n\r\n')[1]
            print html
            client.close()
            return
    client.close()
    sys.exit(1)


def parse(website):  # Parse the URL
    if website.split('//')[0] == 'https:' or website[0:7] != 'http://':
        sys.exit(1)
    flag = 0
    for i in website.split('//')[1]:
        if i == '/':
            flag = 1
            break
    if flag:
        server_name = website.split('//')[1].split('/', 1)[0]
        path = '/' + website.split('//')[1].split('/', 1)[1]
    else:
        server_name = website.split('//')[1]
        path = '/'
    has_port = 0
    for i in server_name:
        if i == ':':
            has_port = 1
            break
    if has_port:
        server_port = int(server_name.split(':')[-1])
        server_name = server_name.split(':')[0]
    else:
        server_port = 80
    return path, server_name, server_port


def http_client(website):
    path, server_name, server_port = parse(website)
    rqst = 'GET ' + path + ' HTTP/1.0\r\n'
    rqst += 'Host: ' + server_name + '\r\n\r\n'
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_name, server_port))
    client.send(rqst)
    res = receive(client)  # HTTP response
    curl(client, res)


redir_cnt = 0  # count for redirection
http_client(sys.argv[1])
