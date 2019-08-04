"""
Uses an Router/Router socket but just one thread
"""

import sys
import zmq
from utils.zhelpers import dump


def main():
    verbose = '-v' in sys.argv

    ctx = zmq.Context()

    # Prepare socket with predictable identity
    bind_endpoint = "tcp://*:5555"
    connect_endpoint = "tcp://localhost:5555"
    server = ctx.socket(zmq.ROUTER)
    server.identity = connect_endpoint
    server.bind(bind_endpoint)
    print("I: service is ready at", bind_endpoint)

    while True:
        try:
            request = server.recv_multipart()
        except:
            break       # Interrupted

        # Frame 0: identity of client
        # Frame 1: Ping, or client control frame
        # Frame 2: Request body
        addr, control = request[:2]
        reply = [addr, control]

        if control == "PING":
            reply[1] = b"PONG"
        else:
            reply.append("OK")
        if verbose:
            dump(reply)
        server.send_multipart(reply)
    print("W: interrupted")


if __name__ == '__main__':
    main()