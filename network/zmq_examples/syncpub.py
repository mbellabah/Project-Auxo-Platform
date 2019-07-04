import zmq

# Wait for 10 subscribers
SUBSCRIBERS_EXPECTED = 3


def main():
    context = zmq.Context()

    # Socket to talk to clients
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5561")

    # Socket to receive sync signals
    syncservice = context.socket(zmq.REP)
    syncservice.bind("tcp://*:5562")

    subscribers = 0
    while subscribers < SUBSCRIBERS_EXPECTED:
        # wait for synchronization request
        msg = syncservice.recv()
        syncservice.send(b"")
        subscribers += 1
        print("+1 subscriber")

    for i in range(1000000):
        publisher.send(b"Grapes")

    publisher.send(b"END")


if __name__ == '__main__':
    main()