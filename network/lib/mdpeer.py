import time
import json
import threading
from queue import Queue
from typing import Dict, Any, List

import MDP
import zmq
from zhelpers import line, strip_of_bytes

# TODO: Fix the slow joiner issue, where the first message appears to be dropped


class Peer(object):
    REQUEST_TIMEOUT = 2500      # 2.5 seconds
    BIND_WAIT = 0.15     # secs

    def __init__(self, endpoint: str, peer_name: str, peers: dict, verbose=True):
        self.endpoint = endpoint
        self.peer_name: bytes = peer_name.encode("utf8")        # format: A01.echo.peer
        self.peers: Dict[bytes, str] = peers        # format: {b'A02.sumnums.peers': str}
        self.state_space: Dict[str, Any] = {'other_peer_data': {}}

        self.request_queue = Queue()
        self.verbose = verbose

        self.poller = zmq.Poller()

        self.send_socket = zmq.Context().socket(zmq.ROUTER)

        self.recv_socket = zmq.Context().socket(zmq.DEALER)
        self.recv_socket.identity = self.peer_name          # format: A01.echo.peer

        # initialize poller set
        self.poller.register(self.recv_socket, zmq.POLLIN)
        self.poller.register(self.send_socket, zmq.POLLIN)

        self.process_queue()

        try:
            self.send_socket.bind(self.endpoint)
        except zmq.error.ZMQError:
            pass
        finally:
            # wait to bind
            time.sleep(self.BIND_WAIT)      # FIXME: Think of a better way to not get the first message dropped

        print(f"Initialized {self.peer_name}")
        print(f"{self.peer_name} has peers: {self.peers}")
        line()
        line()

    def tie_to_peers(self):
        # Tie this peer to all of the peers inside its peers dict
        # Connect recv socket to peers? For now internal process
        for peer_endpoint in self.peers.values():
            self.recv(peer_endpoint)

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
        thread = threading.Thread(target=self.process_queue_thread, name='Thread-request-queue')
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
                    print(self.peer_name, ": Msg received:", request)

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
        thread = threading.Thread(target=self.recv_thread, args=(peer_endpoint,), name='Thread-recv')
        thread.setDaemon(False)
        thread.start()

    def send(self, peer_ident: bytes, payload: bytes):
        """

        :param peer_ident: the identity (bytes) of the peer we're sending to
        :param payload:
        :return:
        """
        # basic request
        # Frame 0: origin, self identity
        # Frame 1: msg
        msg = [self.peer_name, payload]
        msg = [peer_ident] + msg

        num_send: int = 1
        for _ in range(num_send):
            self.send_socket.send_multipart(msg)

    def send_reply(self, peer):
        # Frame 0: other peer identity
        # Frame 1: self identity
        # Frame 2: ack message
        self.recv_socket.send_multipart([peer, b'ACK'])

    def stop(self):
        """ Destroy context and close the socket """
        # FIXME: Destroy the peer object/port cleanly
        self.state_space = {'other_peer_data': {}}
        pass


class PeerPort(Peer):
    def __init__(self, endpoint: str, peer_name: str, peers: dict, verbose=True):
        super(PeerPort, self).__init__(endpoint, peer_name, peers, verbose)

    # override process_queue
    def process_queue_thread(self):
        # Only for debugging
        while True:
            if not self.request_queue.empty():
                if self.verbose:
                    print(self.peer_name, "Queue:", list(self.request_queue.queue))
                msg: Any = self.request_queue.get()[0]

                try:
                    msg: dict = json.loads(msg)
                except Exception as e:
                    print("Failed", repr(e))

                command: bytes = msg['command'].encode('utf8')
                self.command_handler(msg, command)

            time.sleep(0.5)

    def command_handler(self, msg, command):
        peer_identity: bytes = msg['origin'].encode('utf8')

        if command == MDP.W_REQUEST:
            # I've been requested -- send reply with info
            request_state: str = msg['request_state']
            reply_state: Any or None = self.state_space.get(request_state, None)

            payload: dict = {'origin': self.peer_name, 'command': MDP.W_REPLY, 'request_state': request_state, 'request_data': reply_state}
            payload: dict = strip_of_bytes(payload)
            jsonified_payload: bytes = json.dumps(payload).encode('utf8')

            self.send(peer_ident=peer_identity, payload=jsonified_payload)

        elif command == MDP.W_REPLY:
            # Only ever really get other peers' data if self is the leader peer-port
            requested_state: str = msg['request_state']
            requested_state_data: str = msg['request_data']
            self.state_space['other_peer_data'][peer_identity.decode('utf8')] = {requested_state: requested_state_data}

    def get_request_queue(self) -> Queue:
        return self.request_queue
