from typing import List

import socket
import logging
import threading
import hashlib
import random
import json
import time


class Peer(threading.Thread):
    def __init__(self, ip: str, port, callback):
        super(Peer, self).__init__()

        self.terminate_flag = threading.Event()
        self.ip: str = ip
        self.port: int = port
        self.callback = callback
        self.socket = None

        self.peers_in: List[PeerConnection] = []      # Peers connected to us P -> (US) -> P
        self.peers_out: List[PeerConnection] = []     # Peers we are connected to (US) -> P

        # Create unique id for each peer
        _id = hashlib.md5()
        _t = f"{self.ip}{self.port}{random.randint(1,99999999)}"
        _id.update(_t.encode('ascii'))
        self.id = _id.hexdigest()

        self.init_server()

        self.msg_count_send = 0
        self.msg_count_recv = 0
        self.debug = False

    # Getters
    def get_msg_count_send(self):
        return self.msg_count_send

    def get_msg_count_recv(self):
        return self.msg_count_recv

    def get_inbound_peers(self):
        return self.peers_in

    def get_outbound_peers(self):
        return self.peers_out

    def get_ip(self):
        return self.ip

    def get_id(self):
        return self.id

    def get_port(self):
        return self.port

    def print_connections(self):
        logging.info(f"Connection status: # peers connected with us: {len(self.peers_in)}, # peers connected to: {len(self.peers_out)}")

    def enable_debug(self):
        self.debug = True

    def dprint(self, msg):
        if self.debug:
            print("DPRINT:", msg)

    def init_server(self):
        logging.info(f"Init on port: {self.port}, on peer: {self.id}")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', self.port))
        self.socket.settimeout(10.0)
        self.socket.listen(1)

    def remove_stale_connections(self):
        for peer in self.peers_in:
            if peer.terminate_flag.is_set():
                pass

    def create_message(self, data):
        self.msg_count_send += 1
        data['_mcs'] = self.msg_count_send
        data['_mcr'] = self.get_msg_count_recv()

        return data

    def send_to_peers(self, data, exclude=[]):
        for peer in self.peers_in:
            if peer in exclude:
                self.dprint(f"send_to_peers: Excluding peer in message")
            else:
                self.send_to_peer(peer, data)

        for peer in self.peers_out:
            if peer in exclude:
                self.dprint(f"send_to_peers: Excluding peer in message")
            else:
                self.send_to_peer(peer, data)

    def send_to_peer(self, peer, data):
        self.remove_stale_connections()
        if peer in self.peers_in or self.peers_out:
            try:
                peer.send(self.create_message(data))

            except Exception as e:
                self.dprint(f"Error while sending data to peer: {e}")

        else:
            self.dprint("Could not send the data, peer is not found")

    def connect_with_peer(self, host, port):
        logging.info(f"Connect_with_peer: {host}, {port}")
        if host == self.ip and port == self.port:
            logging.info("Cannot connect with self")
            return

        # Check if connection already exists
        for peer in self.peers_out:
            if peer.get_ip() == host and peer.get_port == port:
                logging.info("Already connected with the peer")
                return True

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.dprint(f"Connecting to {host} port {port}")
            s.connect((host, port))

            thread_client = self.create_new_connection(s, (host, port), self.callback)
            thread_client.start()
            self.peers_out.append(thread_client)

            if self.callback is not None:
                self.callback("CONNECTEDWITHPEER", self, thread_client, {})

            self.print_connections()

        except Exception as e:
            self.dprint(f"Could not connect with peer {e}")

    def disconnect_with_peer(self, peer):
        if peer in self.peers_out:
            peer.send(self.create_message({"type": "message", "message": "Terminate connection"}))
            peer.stop()
            peer.join()
            del self.peers_out[self.peers_out.index(peer)]

    def stop(self):
        self.terminate_flag.set()

    def create_new_connection(self, connection, client_address, callback):
        return PeerConnection(self, connection, client_address, callback)

    def run(self):
        while not self.terminate_flag.is_set():
            try:
                self.dprint("Wait for incoming connection")
                client_conn, client_addr = self.socket.accept()

                thread_client = self.create_new_connection(client_conn, client_addr, self.callback)
                thread_client.start()
                self.peers_in.append(thread_client)

                if self.callback is not None:
                    self.callback("PEERCONNECTED", self, thread_client, {})

            except socket.timeout:
                pass

            except:
                raise

            time.sleep(0.01)

        logging.info("Stopping...")
        for thread in self.peers_in:
            thread.join()

        for thread in self.peers_out:
            thread.join()

        self.socket.close()
        self.socket = None
        logging.info("Peer stopped")


class PeerConnection(threading.Thread):
    def __init__(self, peer_server, sock, client_addr: tuple, callback):
        super(PeerConnection, self).__init__()

        self.host, self.port = client_addr
        self.peer_server = peer_server
        self.socket = sock
        self.client_addr = client_addr
        self.callback = callback
        self.terminate_flag = threading.Event()

        # To parse incoming json messages
        self.buffer = ""

        _id = hashlib.md5()
        _t = f"{self.ip}{self.port}{random.randint(1, 99999999)}"
        _id.update(_t.encode('ascii'))
        self.id = _id.hexdigest()

        self.peer_server.dprint(f"PeerConnection.send: Started with client {self.id}, {self.host}:{self.port}")

    def get_host(self):
        return self.host

    def get_port(self):
        return self.port

    def get_id(self):
        return self.id

    def send(self, data):
        try:
            msg = json.dumps(data, separators=(',', ':')) + "-TSN"
            self.socket.sendall(msg.encode('utf-8'))

        except:
            self.peer_server.drpint("Unexpected error")
            self.terminate_flag.set()

    def check_msg(self, data):
        return True


    def stop(self):
        self.terminate_flag.set()

    def run(self):
        self.socket.settimeout(10.0)

        while not self.terminate_flag.is_set():
            line = ""
            try:
                line = self.socket.recv(4096)       # line ends with -TSN\n
                line = line.encode('utf-8')

            except socket.timeout:
                pass

            except:
                self.terminate_flag.set()
                self.peer_server.dprint(f"PeerConnection: Socket has been terminated {line}")

            if line != "":
                try:
                    self.buffer += str(line.decode('utf-8'))
                except:
                    logging.info("PeerConnection: Decoding line error")

                index = self.buffer.find("-TSN")
                while index > 0:
                    message = self.buffer[0: index]
                    self.buffer = self.buffer[index+4::]

                    try:
                        data = json.loads(message)
                    except Exception as e:
                        logging.error(f"PeerConnection: Data could not be parsed {line}, {e}")

                    if self.check_msg(data):
                        self.peer_server.msg_count_recv += 1

                        if self.callback is not None:
                            self.callback("PEERMESSAGE", self.peer_server, self, data)

                    index = self.buffer.find("-TSN")
            time.sleep(0.01)

        self.socket.settimeout(None)
        self.socket.close()
        self.socket = None
        self.peer_server.dprint("PeerConnection: Stopped")


if __name__ == '__main__':

    def callbackPeerEvent(event, peer, other, data):
        print(f"Event Peer 1 ({peer.id}): {event}: {data}")
        peer.send_to_peers({"thank": "you"})

    peer = Peer('localhost', 10000, callbackPeerEvent)
    peer.enable_debug()
    peer.start()
    peer.connect_with_peer('localhost', 10003)

    t_end = time.time() + 5
    while time.time() < t_end:
        pass

    peer.stop()
    peer.join()

    print("Stopped!")




