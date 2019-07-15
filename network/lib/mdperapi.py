import time
import threading
from queue import Queue
from typing import Dict

import zmq

# TODO: Fix the slow joiner issue, where the first message appears to be dropped


class Peer(object):
    REQUEST_TIMEOUT = 2500      # 2.5 seconds

    def __init__(self, endpoint, peer_name: str, peers: dict, verbose=True):
        self.endpoint = endpoint
        self.peer_name: bytes = peer_name.encode("utf8")
        self.peers: Dict[bytes, str] = peers
        self.request_queue = Queue()
        self.verbose = verbose

        self.poller = zmq.Poller()

        self.send_socket = zmq.Context().socket(zmq.ROUTER)

        self.recv_socket = zmq.Context().socket(zmq.DEALER)
        self.recv_socket.identity = self.peer_name

        # initialize poller set
        self.poller.register(self.recv_socket, zmq.POLLIN)
        self.poller.register(self.send_socket, zmq.POLLIN)

        # Connect recv socket to peers? For now internal process
        for peer_endpoint in self.peers.values():
            self.recv(peer_endpoint)

        self.process_queue()
        print(f"Initialized {self.peer_name}")

    def process_queue_thread(self):
        """ Process the entry in the queue """

        while True:
            if not self.request_queue.empty():
                if self.verbose:
                    print(self.peer_name, "Queue:", list(self.request_queue.queue))
                current_request = self.request_queue.get()

                # Do some processing on current_request
                time.sleep(0.1)

            time.sleep(1)

    def process_queue(self):
        thread = threading.Thread(target=self.process_queue_thread)
        thread.setDaemon(False)
        thread.start()

    def recv_thread(self, peer_endpoint: str):
        """
        recv thread, receives information in a loop
        :param peer_endpoint: the other peer's endpoint i.e. tcp://*:*
        :return:
        """
        self.recv_socket.connect(peer_endpoint)
        self.recv_socket.linger = 0

        while True:

            try:
                items = dict(self.poller.poll(self.REQUEST_TIMEOUT))
            except KeyboardInterrupt:
                break

            if items and self.recv_socket in items:
                request = self.recv_socket.recv_multipart()
                self.request_queue.put(request)     # add to the queue
                if self.verbose:
                    print(self.peer_name, ": Request received:", request)

                origin_peer = request.pop(0)
                self.send_reply(origin_peer)

            if items and self.send_socket in items:
                reply = self.send_socket.recv_multipart()
                if self.verbose:
                    print(self.peer_name, ": Received ack!:", reply)

    def recv(self, peer_endpoint: str):
        """
        runs the recv thread defined above
        :param peer_endpoint: the other peer's endpoint i.e. tcp://*:*
        :return:
        """
        thread = threading.Thread(target=self.recv_thread, args=(peer_endpoint,))
        thread.setDaemon(False)
        thread.start()

    def send(self, peer_ident: bytes, payload: bytes):
        """

        :param peer_ident: the identity (bytes) of the peer we're sending to
        :param payload:
        :return:
        """
        try:
            self.send_socket.bind(self.endpoint)        # FIXME: I'm sure there is an issue here!!
        except zmq.error.ZMQError:
            pass

        # basic request
        for _ in range(1):
            # Frame 0: origin, self identity
            # Frame 1: msg
            msg = [self.peer_name, payload]
            msg = [peer_ident] + msg
            self.send_socket.send_multipart(msg)

    def send_reply(self, peer):
        # Frame 0: other peer identity
        # Frame 1: self identity
        # Frame 2: ack message
        self.recv_socket.send_multipart([peer, b'ACK'])

    def stop(self):
        """ Destroy context and close the socket """
        pass
