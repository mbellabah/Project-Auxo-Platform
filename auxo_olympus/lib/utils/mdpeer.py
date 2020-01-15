import zmq
import time
import json
import pickle 
import threading
from queue import Queue
from typing import Dict, Any

from abc import ABCMeta, abstractmethod

import auxo_olympus.lib.utils.MDP as MDP
from auxo_olympus.lib.utils.zhelpers import line, strip_of_bytes


class Peer(object, metaclass=ABCMeta):
    REQUEST_TIMEOUT = 2500      # 2.5 seconds
    BIND_WAIT = 0.15     # secs
    URL_INDEPENDENT_PEER_PORTS = "inproc://independent_peer_ports"

    def __init__(self, endpoint: str, peer_name: str, peers: dict, verbose=True):
        self.endpoint = endpoint
        self.peer_name: bytes = peer_name.encode("utf8")        # format: A01.echo.peer
        self.peers: Dict[bytes, str] = peers        # format: {b'A02.sumnums.peer': str}
        self.state_space: Dict[str, Any] = {'other_peer_data': {}}
        self.shutdown_flag: bool = False

        self.verbose = verbose

        context = zmq.Context.instance()

        self.send_socket = context.socket(zmq.ROUTER)

        self.recv_socket = context.socket(zmq.DEALER)
        self.recv_socket.identity = self.peer_name          # format: A01.echo.peer

        try:
            self.send_socket.bind(self.endpoint)
            self.recv_socket.bind(self.URL_INDEPENDENT_PEER_PORTS)
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

        self.start_proxy()

    def proxy_thread(self):
        zmq.proxy(self.send_socket, self.recv_socket)

    def start_proxy(self):
        threading.Thread(target=self.proxy_thread).start()

    def recv_thread(self, peer_endpoint: str, context=None):
        """
        recv thread, receives information in a loop
        :param peer_endpoint: the other peer's endpoint i.e. tcp://*:*
        :return:
        """
        context = context or zmq.Context.instance()
        inproc_socket = context.socket(zmq.REP)
        inproc_socket.connect(self.URL_INDEPENDENT_PEER_PORTS)

        while True:
            msg = inproc_socket.recv_multipart()[0]
            if self.verbose: 
                print(self.peer_name, "received request:", msg)

            self.process_request(inproc_socket, peer_endpoint.encode('utf8'), msg)

    @abstractmethod
    def process_request(self, socket: zmq.Socket, peer_endpoint: bytes, msg: Any):
        self.send(socket, peer_endpoint, msg)

    def recv(self, peer_endpoint: str):
        """
        runs the recv thread defined above
        :param peer_endpoint: the other peer's endpoint i.e. tcp://*:*
        :return:
        """
        thread = threading.Thread(target=self.recv_thread, args=(peer_endpoint,), name='Thread-recv')
        thread.setDaemon(True)
        thread.start()

    def send(self, socket: zmq.Socket, peer_identity: bytes, payload: bytes):
        """

        :param peer_ident: the identity (bytes) of the peer we're sending to
        :param payload:
        :return:
        """
        # basic request
        # Frame 0: origin, self identity
        # Frame 1: msg
        msg = [self.peer_name, payload]
        msg = [peer_identity] + msg

        socket.send_multipart(msg)

    def stop(self):
        """ Destroy context and close the socket """
        # FIXME: Destroy the peer object/port cleanly
        self.shutdown_flag = True
        self.state_space = {'other_peer_data': {}}


class PeerPort(Peer):
    def __init__(self, endpoint: str, peer_name: str, peers: dict, verbose=True):
        super(PeerPort, self).__init__(endpoint, peer_name, peers, verbose)

        self.leader_force_alive = True

    # override process_request in base Peer class 
    def process_request(self, socket: zmq.Socket, peer_endpoint: bytes, msg: Any):
        try: 
            msg: dict = json.loads(msg)
        except UnicodeDecodeError:
            # issue is probably because not JSON serializable, so use pickle to load 
            msg: dict = pickle.loads(msg)

        if self.verbose: 
            print("\n\nI've been asked for something", msg)

        command: bytes = msg['command'].encode('utf8')
        payload = self.command_handler(msg, command)
        
        if payload: 
            if self.verbose: 
                print("\n\n\nSending", peer_endpoint, payload)
            self.send(socket, peer_endpoint, payload)

    def process_reply(self, msg):   
        """
        frame 0: self address
        frame 1: origin name 
        frame 2: payload 
        """
        payload = msg[2]

        try:
            payload: dict = json.loads(payload)
        except UnicodeDecodeError:
            # issue is probably because not JSON serializable, so use pickle to load
            payload: dict = pickle.loads(payload)

        if self.verbose: 
            print("\n\nReceived this", payload) 

        command: bytes = payload['command'].encode('utf8')
        self.command_handler(payload, command)

    def command_handler(self, payload, command) -> bytes or None:
        peer_identity: bytes = payload['origin'].encode('utf8')

        if command == MDP.W_REQUEST:
            # I've been requested -- send reply with info
            request_state: str = payload['request_state']
            reply_state: Any or None = self.state_space.get(request_state, None)

            payload: dict = {'origin': self.peer_name, 'command': MDP.W_REPLY, 'request_state': request_state, 'request_data': reply_state}
            payload: dict = strip_of_bytes(payload)

            try:
                jsonified_payload: bytes = json.dumps(payload).encode('utf8')
            except TypeError:
                # object of type "Custom Object" is not JSON serializable, use pickle 
                jsonified_payload: bytes = pickle.dumps(payload) # jsonpickle.encode(payload)

            return jsonified_payload
            # self.send(peer_ident=peer_identity, payload=jsonified_payload)

        elif command == MDP.W_REPLY:
            # Only ever really get other peers' data if self is the leader peer-port
            requested_state: str = payload['request_state']
            requested_state_data: str = payload['request_data']
            self.state_space['other_peer_data'][peer_identity.decode('utf8')] = {requested_state: requested_state_data}
            return None 

        elif command == MDP.W_DISCONNECT:
            info: str = payload['info']
            self.leader_force_alive = False
            if info == 'DONE':
                self.stop()