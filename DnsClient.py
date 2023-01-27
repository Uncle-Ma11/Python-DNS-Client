import argparse
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
    parser.add_argument("name")
    parser.add_argument("server")
    try:
        argv = parser.parse_args()
    except argparse.ArgumentError:
        print(
            "The input query form is not correct. \n should use: python DnsClient.py [-t timeout] [-r max-retries] [-p port] [-mx|-ns] @server name")
    print(argv)
    print(argv.name)
    print(argv.server)
    return argv


def send_query(argv):
    server_name = argv.name[1:]
    server_port = argv.port

    print(server_name, server_port)

    client_socket = socket(AF_INET, SOCK_DGRAM)

    message = ""

    client_socket.sendto(message.encode(), (server_name, server_port))
    received_message, server_address = client_socket.recvfrom(2048)
    print(received_message.decode())
    client_socket.close()


if __name__ == "__main__":
    send_query(read_input())
