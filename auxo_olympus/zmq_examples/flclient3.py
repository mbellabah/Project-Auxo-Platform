import time

from zmq_examples.flcliapi import FreelanceClient


def main():
    # Create new freelance client object
    client = FreelanceClient()

    # Connect to several endpoints
    client.connect("tcp://localhost:5555")
    client.connect("tcp://localhost:5556")
    client.connect("tcp://localhost:5557")

    # Send a bunch of name resolution requests
    requests = 10000
    start = time.time()
    for i in range(requests):
        request = ["random name"]
        reply = client.request(request)
        if not reply:
            print("E: name service not available, aborting")
            return

    print("Average round trip:", (1e6*(time.time() - start))/requests)


if __name__ == '__main__':
    main()
