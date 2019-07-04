"""
Pubsub envelope publisher
"""

import time
import zmq


def main():
    context = zmq.Context(1)
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5563")

    while True:
        publisher.send_multipart([b"A", b"We don't want to see this"])
        publisher.send_multipart([b"B", b"We would like to see this"])
        time.sleep(1)

    publisher.close()
    context.term()


if __name__ == '__main__':
    main()