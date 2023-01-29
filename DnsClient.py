import argparse
import random
import secrets
import sys
import time

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
        parsed_args = parser.parse_args()
    except argparse.ArgumentError:
        print(
            "The input query form is not correct. \n should use: python DnsClient.py [-t timeout] [-r max-retries] [-p port] [-mx|-ns] @server name")
    return parsed_args


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
    server_name = args.server[1:]
    server_port = args.port

    print("DNS sending request for " + args.name)
    print("Server: " + args.server)
    if args.mx:
        print("Request type: MX")
    elif args.ns:
        print("Request type: NS")
    else:
        print("Request type: A")

    # for req in request:
    #     print(req)
    # print(request)

    length = len(request)
    # print(length)

    # print(args.timeout, args.retry, args.mx, args.ns)
    #
    # print(server_name, server_port)

    client_socket = socket(AF_INET, SOCK_DGRAM)

    client_socket.settimeout(args.timeout)
    try:
        start = time.time()
        client_socket.sendto(request, (server_name, server_port))
        received_message, server_address = client_socket.recvfrom(2048)
        end = time.time()
        used_time = end - start
        print("Response received after {} seconds ({} retries)".format(used_time, retried_time - 1))
        output_result(received_message, length)
        client_socket.close()
    except timeout:
        if retried_time > args.retry:
            print("No response received after {} retries.".format(retried_time - 1))
            return
        else:
            send_query(retried_time + 1, request, args)


def read_record(response, pos, auth, count, ans_num):
    if count > ans_num:
        return pos
    answer_part = response[pos:]
    # print(answer_part)
    # b_list = []
    for byte in answer_part:
        pos += 1
        if byte == 0:
            break
        # b_list.append(bytes([byte]))
    # r_name = b''.join(b_list)
    # print(r_name)
    # # print(answer_part)
    type_byte = response[pos]
    # print(type_byte)
    if type_byte == 1:
        r_type = "A"
    elif type_byte == 2:
        r_type = "NS"
    elif type_byte == 5:
        r_type = "CNAME"
    elif type_byte == 15:
        r_type = "MX"
    else:
        r_type = "ERROR"
    # print(r_type)
    pos += 1
    prev_byte = response[pos]
    pos += 1
    class_byte = response[pos]
    # print(class_byte)
    if not (prev_byte == 0 and class_byte == 1):
        print("ERROR")
    pos += 1
    ttl_bytes = response[pos:pos + 4]
    # print(ttl_bytes)
    exp = 6
    ttl = 0
    for byte in ttl_bytes:
        ttl += byte * 10 ** exp
        exp -= 2
    # print(ttl)
    pos += 4
    data_length_bytes = response[pos:pos + 2]
    # print(data_length_bytes)
    data_length = 0
    exp = 2
    for byte in data_length_bytes:
        data_length += byte * 16 ** exp
        exp -= 2
    # print(data_length)
    pos += 2
    data_bytes = response[pos:pos + data_length]
    pos += data_length
    # print(data_bytes)

    if r_type == "A":
        address = ""
        for byte in data_bytes:
            address += str(byte) + "."
        address = address[0:len(address) - 1]
        if auth:
            print("IP\t{}\t{}\tauth".format(address, ttl))
        else:
            print("IP\t{}\t{}\tnonauth".format(address, ttl))

    elif r_type == "CNAME":
        alias = resolve_alias(response, data_bytes)
        if auth:
            print("CNAME\t{}\t{}\tauth".format(alias, ttl))
        else:
            print("CNAME\t{}\t{}\tnonauth".format(alias, ttl))

    elif r_type == "MX":
        preference_bytes = data_bytes[:2]
        preference_num = preference_bytes[0] * 16 + preference_bytes[1]
        exchange_bytes = data_bytes[2:]
        exchange_name = resolve_alias(response, exchange_bytes)
        if auth:
            print("MX\t{}\t{}\t{}\tauth".format(exchange_name, preference_num, ttl))
        else:
            print("MX\t{}\t{}\t{}\tnonauth".format(exchange_name, preference_num, ttl))

    elif r_type == "NS":
        s_name = resolve_alias(response, data_bytes)
        if auth:
            print("NS\t{}\t{}\tauth".format(s_name, ttl))
        else:
            print("NS\t{}\t{}\tnonauth".format(s_name, ttl))

    else:
        print("Cannot handle response type")

    read_record(response, pos, auth, count + 1, ans_num)


def resolve_alias(response, data):
    # print(data)
    alias = ""
    count = 0
    for byte in data:
        if byte == 0:
            break
        if byte >= 192:
            pointer1 = bin(byte - 192)
            pointer2 = bin(data[count + 1])
            offset_num = int(pointer1, 2) * 16 + int(pointer2, 2)
            alias += seek_pointer(offset_num, response)
        elif byte <= 32:
            alias = alias + "."
        else:
            alias = alias + chr(byte)
        count += 1
    return alias[1:len(alias) - 1]


def seek_pointer(offset, response):
    data = response[offset:]
    # print(data)
    alias = ""
    count = offset
    for byte in data:
        if byte == 0:
            break
        if byte >= 192:
            pointer1 = bin(byte - 192)
            pointer2 = bin(data[count + 1])
            offset_num = int(pointer1, 2) * 16 + int(pointer2, 2)
            alias += seek_pointer(offset_num, response)
        elif byte <= 32:
            alias = alias + "."
        else:
            alias = alias + chr(byte)
        count += 1
    return alias


def output_result(response, request_length):
    # print(response)
    auth_bytes = response[2]
    # print(auth_bytes)
    if auth_bytes & 4:
        auth = True
    else:
        auth = False
    an_count = response[6:8]
    an_count_num = an_count[0] * 16 + an_count[1]
    print("*** Answer Section ( {} records) ***".format(an_count_num))
    if an_count_num == 0:
        print("NOT FOUND")
    answer_pos = read_record(response, request_length, auth, 1, an_count_num)
    ar_count = response[10:12]
    ar_count_num = ar_count[0] * 16 + ar_count[1]
    print("*** Additional Section ( {} records) ***".format(ar_count_num))
    if ar_count_num == 0:
        print("NOT FOUND")
    read_record(response, answer_pos, auth, 1, ar_count_num)


if __name__ == "__main__":
    argv = read_input()
    message = format_query(argv)
    send_query(1, message, argv)
