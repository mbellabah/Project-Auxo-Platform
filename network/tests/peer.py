import time
import random
import threading

import zmq
import sys

from typing import Dict
from lib.zhelpers import ZMQMonitor


class Peer(object):
    REQUEST_TIMEOUT = 2500      # 2.5 seconds

    def __init__(self, peer_name: str, peers: dict):
        self.peer_name: bytes = peer_name.encode("utf8")
        self.peers: Dict[bytes, str] = peers
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

    def recv_thread(self, peer_endpoint: str):
        """ Receives information in a loop """
        self.recv_socket.connect(peer_endpoint)
        self.recv_socket.linger = 0

        while True:

            try:
                items = dict(self.poller.poll(self.REQUEST_TIMEOUT))
            except KeyboardInterrupt:
                break

            if items and self.recv_socket in items:
                request = self.recv_socket.recv_multipart()
                print(self.peer_name, ":Request received:", request)

                origin_peer = request.pop(0)
                self.send_reply(origin_peer)

            if items and self.send_socket in items:
                reply = self.send_socket.recv_multipart()
                print(self.peer_name, ":Received ack!:", reply)

    def recv(self, peer_endpoint: str):
        thread = threading.Thread(target=self.recv_thread, args=(peer_endpoint,))
        thread.setDaemon(True)
        thread.start()

    def send(self, endpoint: str, peer_ident: bytes, payload: bytes):
        # bind the send socket
        self.send_socket.bind(endpoint)

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
    # # peername other_peer_name other_peer_endpoint send
    # args = sys.argv
    #
    #
    # [peer_name, other_peer_name, other_peer_endpoint, send] = args[1:]
    # peers = {other_peer_name: other_peer_endpoint}
    # peer = Peer(peer_name=peer_name, peers=peers)
    #
    # if send:
    #     peer.send(peers['peer0'], peer_ident=b'peer0')

    _peers0 = {'peer1': 'ipc://routing.ipc'}
    _peers1 = {'peer0': 'ipc://routing.ipc'}

    peer0 = Peer(peer_name='peer0', peers=_peers0)
    peer1 = Peer(peer_name='peer1', peers=_peers1)

    for i in range(10):     # FIXME: Fix the slow joiner issue, where the first message is dropped
        payload: bytes = f'request {i}'.encode('utf8')
        peer1.send(endpoint=_peers1['peer0'], peer_ident=b'peer0', payload=payload)
        time.sleep(0.5)





