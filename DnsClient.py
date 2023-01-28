import argparse
import random
import secrets
import sys

from socket import *


def read_input():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", type=int, dest="timeout", default="5", help="set query timeout")
    parser.add_argument("-r", type=int, dest="retry", default="3",
                        help="maximum number of times to retransmit an unanswered query before giving up")
    parser.add_argument("-p", type=int, dest="port", default="53", help="the UDP port number of the DNS server")
    query_type_group = parser.add_mutually_exclusive_group()
    query_type_group.add_argument("-mx", action="store_true")
    query_type_group.add_argument("-ns", action="store_true")
    parser.add_argument("server")
    parser.add_argument("name")
    try:
        argv = parser.parse_args()
    except argparse.ArgumentError:
        print(
            "The input query form is not correct. \n should use: python DnsClient.py [-t timeout] [-r max-retries] [-p port] [-mx|-ns] @server name")
    return argv


def format_query(arguments):
    bytes_list = []

    ID = secrets.token_bytes(2)
    # print(len(ID))
    bytes_list.append(ID)

    QR = bytes([1])
    bytes_list.append(QR)
    RA = bytes([0])
    bytes_list.append(RA)

    ZeroBytes = bytes([0])

    QDCOUNT = b''.join([ZeroBytes, bytes([1])])
    bytes_list.append(QDCOUNT)
    ANCOUNT = b''.join([ZeroBytes, bytes([0])])
    bytes_list.append(ANCOUNT)
    NSCOUNT = b''.join([ZeroBytes, bytes([0])])
    bytes_list.append(NSCOUNT)
    ARCOUNT = b''.join([ZeroBytes, bytes([0])])
    bytes_list.append(ARCOUNT)

    labels = arguments.name.split(".")

    for label in labels:
        length = bytes([len(label)])
        content = label.encode('utf-8')
        bytes_list.append(b''.join([length, content]))

    bytes_list.append(ZeroBytes)

    # print(labels)

    if arguments.mx:
        qtype = b''.join([ZeroBytes, bytes([15])])
    elif arguments.ns:
        qtype = b''.join([ZeroBytes, bytes([2])])
    else:
        qtype = b''.join([ZeroBytes, bytes([1])])

    bytes_list.append(qtype)

    qclass = b''.join([ZeroBytes, bytes([1])])

    bytes_list.append(qclass)

    query = b''.join(bytes_list)
    # print(encoded1)
    # print(encoded2)
    #
    # joined = bytes([145])

    # encoded2 = b''.join([id, encoded2]);

    # print(bytearray(message, "UTF-8"))

    return query


def send_query(retried_time, request, args):
    server_name = args.name
    server_port = args.port

    # for req in request:
    #     print(req)
    print(request)

    print(args.timeout, args.retry, args.mx, args.ns)

    print(server_name, server_port)

    client_socket = socket(AF_INET, SOCK_DGRAM)

    client_socket.settimeout(args.timeout)
    try:
        client_socket.sendto(request, (server_name, server_port))
        received_message, server_address = client_socket.recvfrom(4096)
        print(received_message.decode())
        client_socket.close()
    except timeout:
        if retried_time > args.retry:
            print("No response received after retries.")
            return
        else:
            send_query(retried_time + 1, request, args)


if __name__ == "__main__":
    argv = read_input()
    message = format_query(argv)
    send_query(1, message, argv)
