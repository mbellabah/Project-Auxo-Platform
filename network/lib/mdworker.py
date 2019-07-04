import sys
from mdwrkapi import MajorDomoWorker


def main():
    verbose = '-v' in sys.argv
    worker = MajorDomoWorker("tcp://localhost:5555", "echo", verbose)
    reply = None
    while True:
        request = worker.recv(reply)
        if request is None:
            break
        reply = request     # simple echo


if __name__ == '__main__':
    main()
