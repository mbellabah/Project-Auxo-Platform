import time
import threading
from queue import Queue
from typing import Dict

import zmq


# TODO: Prove that the peers can connect to another peer given only the tcp endpoint
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
                if self.verbose:
                    print("DEBUG Poller", items)
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


if __name__ == '__main__':
    # # peer name other_peer_name other_peer_endpoint send
    # args = sys.argv
    #
    #
    # [peer_name, other_peer_name, other_peer_endpoint, send] = args[1:]
    # peers = {other_peer_name: other_peer_endpoint}
    # peer = Peer(peer_name=peer_name, peers=peers)
    #
    # if send:
    #     peer.send(peers['peer0'], peer_ident=b'peer0')

    # MARK: Testing between bbb-df1f.local and localhost!

    _peers0 = {'peer1': 'tcp://192.168.0.101:5555'}
    _peers1 = {'peer0': 'tcp://192.168.0.104:5555'}

    # localhost
    peer0 = Peer(endpoint='tcp://192.168.0.104:5555', peer_name='peer0', peers=_peers0, verbose=True)

    # Running on BBB-df1f.local
    # peer1 = Peer(endpoint='tcp://192.168.0.101:5555', peer_name='peer1', peers=_peers1, verbose=True)

    try:
        for i in range(10):
            payload: bytes = f'request {i}'.encode('utf8')
            peer1.send(peer_ident=b'peer0', payload=payload)

            time.sleep(0.5)
    except NameError:
        pass






