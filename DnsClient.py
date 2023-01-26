import argparse
import sys


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
        print(argv)
        print(argv.name)
        print(argv.server)
    except argparse.ArgumentError:
        print(
            "The input query form is not correct. \n should use: python DnsClient.py [-t timeout] [-r max-retries] [-p port] [-mx|-ns] @server name")


if __name__ == "__main__":
    read_input()
