import time
import zmq

def main():
    context = zmq.Context()

    # Connect to subscribe socket
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5561")
    subscriber.setsockopt(zmq.SUBSCRIBE, b"")

    time.sleep(1)

    # Second, synchronize with publisher
    syncclient = context.socket(zmq.REQ)
    syncclient.connect("tcp://localhost:5562")

    # Send a synchronization request
    syncclient.send(b"")
    syncclient.recv()

    nbr = 0
    while True:
        msg = subscriber.recv()
        if msg == b'END':
            break
        nbr += 1

    print(f"Received {nbr} updates!")


if __name__ == '__main__':
    main()