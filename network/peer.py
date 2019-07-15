import zmq
import uuid
import time
from zmq_examples import utils
import threading


class Peer(object):
    def __init__(self, identity: bytes, broker_host="127.0.0.1", broker_router_port=5580, broker_dealer_port=5581):
        self.host = broker_host
        self.dealer_port = broker_dealer_port
        self.router_port = broker_router_port

        self.id = uuid.uuid4()
        self.my_ip = utils.get_ip()
        self.active_threads = []
        self.identity = identity

        self.worker_socket = None       # Receives requests, and can send replies
        self.client_socket = None       # Sends requests, receives replies

    def connect_to_worker(self):
        context = zmq.Context.instance()
        self.worker_socket = context.socket(zmq.REP)

        try:
            self.worker_socket.connect(f"tcp://{self.host}:{self.dealer_port}")
            self.worker_socket.setsockopt(zmq.IDENTITY, self.identity)
        except Exception as e:
            print("Failed to connect socket:", e)
            self.worker_socket.close()
            self.worker_socket = None

            return

    def bind_client_socket(self):
        context = zmq.Context.instance()
        self.client_socket = context.socket(zmq.REQ)

        try:
            self.client_socket.bind(f"tcp://{self.host}:{self.router_port}")
        except Exception as e:
            print("Failed to bind socket:", e)

            self.client_socket.close()
            self.client_socket = None

            return

    def send(self, identity: bytes, msg, iter_times: int = 1):
        # Send a request, and expect a reply back
        assert self.client_socket is not None, "Socket is not bound"
        assert type(msg) == bytes, "Did not pass bytes"

        for _ in range(iter_times):
            self.client_socket.send_multipart([identity, msg])

        # self.client_socket.send_multipart([identity, b'END'])

    def receive_thread(self):
        assert self.worker_socket is not None, "Socket is not connected"

        while True:
            request = self.worker_socket.recv()
            if request == b"END":
                print(f"{self.identity}: Received request", request)

    def receive(self):
        recv_thread = threading.Thread(target=self.receive_thread)
        self.active_threads.append(recv_thread)
        recv_thread.start()

        time.sleep(1)      # allow thread to stabilize

    def run_a(self):
        self.connect_to_worker()
        self.bind_client_socket()

        for request in range(1, 11):
            self.send(identity=b"B", msg=b"Here's your work")
        # self.stop()

        self.send(identity=b"B", msg=b"END")

    def run_b(self):
        # Will act as the listener
        self.connect_to_worker()
        self.bind_client_socket()

        try:
            self.receive_thread()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        try:
            self.worker_socket.close()
        except Exception as e:
            print("Failed to close worker socket:", e)
        finally:
            self.worker_socket = None

        try:
            self.client_socket.close()
        except Exception as e:
            print("Failed to close client socket:", e)
        finally:
            self.client_socket = None

        if self.active_threads:
            for thread in self.active_threads:
                thread.join()
            self.active_threads = []


if __name__ == '__main__':
    peer_a = Peer(b"A")
    peer_b = Peer(b"B")

    # peer_b.run_b()
    time.sleep(1)
    peer_a.run_a()


