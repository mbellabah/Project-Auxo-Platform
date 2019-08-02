""" Custom routing between Router and Dealer"""

import time
import random
import threading

import zmq


def worker_a(context=None):
    context = context or zmq.Context.instance()
    worker = context.socket(zmq.DEALER)
    worker.identity = b'A'
    worker.connect("ipc://routing.ipc")

    total = 0
    while True:
        request = worker.recv()
        finished = request == b"END"
        if finished:
            print("A received:", total)
            break
        total += 1


def worker_b(context=None):
    context = context or zmq.Context.instance()
    worker = context.socket(zmq.DEALER)
    worker.identity = b'B'
    worker.connect("ipc://routing.ipc")

    total = 0
    while True:
        request = worker.recv()
        finished = request == b"END"
        if finished:
            print("B received:", total)
            break
        total += 1


if __name__ == '__main__':
    context = zmq.Context.instance()
    client = context.socket(zmq.ROUTER)
    client.bind("ipc://routing.ipc")

    threading.Thread(target=worker_a).start()
    threading.Thread(target=worker_b).start()

    time.sleep(1)

    for _ in range(10):
        ident = random.choice([b'A', b'A', b'B'])
        work = b'This is some work!'
        client.send_multipart([ident, work])

    client.send_multipart([b'A', b'END'])
    client.send_multipart([b'B', b'END'])
