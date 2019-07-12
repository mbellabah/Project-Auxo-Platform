import logging
import sys
import time
import json
import argparse
from collections import deque
from binascii import hexlify, unhexlify

import zmq

# Local
import MDP
from zhelpers import dump, ensure_is_bytes

# TODO: Connect this platform to the GUI, allow a spot to enter text
#       For the GUI, implement a separate screen (navigate via menu or tabs?) that allows one to see the broker
#       interface!


class Service(object):
    """ A single Service """
    name = None
    requests = None     # Queue of client requests
    waiting = None      # Queue of waiting workers

    def __init__(self, name):
        self.name = name
        self.requests = deque()
        self.waiting = deque()


class Worker(object):
    """ A Worker, idle or active """
    identity = None     # hex Identity of the worker
    address = None      # address to route to
    service = None      # owning service if known
    expiry = None       # expires at this point, unless a heartbeat comes through

    def __init__(self, identity, address, lifetime, physical_address, agent_name):
        self.identity = identity
        self.agent_name = agent_name
        self.address = address
        self.expiry = time.time() + 1e-3*lifetime
        self.physical_address = physical_address


class MajorDomoBroker(object):
    """ Majordomo protocol broker"""
    INTERNAL_SERVICE_PREFIX = b"mmi."
    HEARTBEAT_LIVENESS = 4
    HEARTBEAT_INTERVAL = 2500       # msecs
    HEARTBEAT_EXPIRY = HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS

    ctx = None  # context
    socket = None   # Sockets for clients and workers
    poller = None

    heartbeat_at = None     # when to send heartbeat
    services = None     # known services
    workers = None      # known workers
    waiting = None      # idle workers

    verbose = False

    def __init__(self, verbose=False):
        """ Initialize the broker state """
        self.verbose = verbose

        self.services = {}
        self.workers = {}
        self.waiting = []
        self.heartbeat_at = time.time() + 1e-3*self.HEARTBEAT_INTERVAL
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.ROUTER)
        self.socket.linger = 0
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.physical_addresses: dict = {}      # stores all the physical locations of the workers as seen from broker
        logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)

    def mediate(self):
        """ Main broker work happens here -- mediates between the client and the worker socket """
        while True:
            print("DEBUG DEBUG - physical", self.physical_addresses)          # FIXME: Remove
            try:
                items = self.poller.poll(self.HEARTBEAT_INTERVAL)
            except KeyboardInterrupt:
                break
            if items:
                msg = self.socket.recv_multipart()
                if self.verbose:
                    logging.info("I: received message:")
                    dump(msg)

                sender = msg.pop(0)
                empty = msg.pop(0)
                assert empty == b""
                header = msg.pop(0)

                if MDP.C_CLIENT == header:
                    self.process_client(sender, msg)
                elif MDP.W_WORKER == header:
                    self.process_worker(sender, msg)
                else:
                    logging.error("E: invalid message:")
                    dump(msg)

            self.purge_workers()
            self.send_heartbeats()

    def destroy(self):
        """ Disconnect all workers, destroy context """
        while self.workers:
            self.delete_worker(self.workers.values()[0], True)
        self.ctx.destroy(0)

    def process_client(self, sender, msg):
        """ Process a request coming from a client """
        assert len(msg) >= 2        # Service_name + body
        sender_name = msg.pop(0)
        service = msg.pop(0)

        # Set reply return address to client sender
        msg = [sender, ""] + msg
        if service.startswith(self.INTERNAL_SERVICE_PREFIX):
            self.service_internal(service, msg)
        else:
            self.dispatch(self.require_service(service), msg)

    def process_worker(self, sender, msg):
        """ Process message sent to us by a worker """
        assert len(msg) >= 1        # at least, command
        # worker_name = msg.pop(0)      # FIXME: Remove
        command = msg.pop(0)

        worker_ready = hexlify(sender) in self.workers
        worker = self.require_worker(sender)

        if MDP.W_READY == command:
            assert len(msg) >= 1
            service = msg.pop(0)
            if worker_ready or service.startswith(self.INTERNAL_SERVICE_PREFIX):
                self.delete_worker(worker, True)
            else:
                # Attach worker to service and mark as idle
                worker.service = self.require_service(service)
                self.worker_waiting(worker)

        elif MDP.W_REPLY == command:
            if worker_ready:
                # Remove and save client return envelope and insert the protocol header and service name, then rewrap
                client = msg.pop(0)
                empty = msg.pop(0)

                msg = [client, b"", MDP.C_CLIENT, worker.service.name] + msg
                msg = ensure_is_bytes(msg)

                self.socket.send_multipart(msg)
                self.worker_waiting(worker)
            else:
                self.delete_worker(worker, True)

        elif MDP.W_HEARTBEAT == command:
            if worker_ready:
                worker.expiry = time.time() + 1e-3*self.HEARTBEAT_EXPIRY
            else:
                self.delete_worker(worker, True)

        elif MDP.W_DISCONNECT == command:
            self.delete_worker(worker, False)

        else:
            logging.error("E: invalid message:")
            dump(msg)

    def delete_worker(self, worker, disconnect):
        """ Deletes the worker from all data structures and deletes worker """
        logging.info("DELETE_WORKER_DEBUG: Delete worker")
        assert worker is not None
        if disconnect:
            self.send_to_worker(worker, MDP.W_DISCONNECT, None, None)

        if worker.service is not None:
            worker.service.waiting.remove(worker)

        self.workers.pop(worker.identity)
        self.physical_addresses.pop(worker.agent_name)

    def require_worker(self, address):
        """ Finds the worker (creates if necessary) """
        assert address is not None
        identity = hexlify(address)
        worker_agent_name: bytes = unhexlify(identity).split(b".")[0]  # format of A01

        worker = self.workers.get(identity)
        if worker is None:
            print("DEBUG DEBUG require_worker", self.socket)
            worker_physical_address = self.socket.getsockopt(zmq.LAST_ENDPOINT)
            worker = Worker(identity, address, self.HEARTBEAT_EXPIRY, physical_address=worker_physical_address, agent_name=worker_agent_name)
            self.workers[identity] = worker
            self.physical_addresses[worker_agent_name] = worker_physical_address
            if self.verbose:
                logging.info(f"I: registering new worker:{unhexlify(identity)}")

        return worker

    def require_service(self, name):
        """ Locates the service (creates if necessary) """
        assert name is not None
        service = self.services.get(name)
        if service is None:
            service = Service(name)
            self.services[name] = service

        return service

    def bind(self, endpoint):
        """ Bind broker to endpoint, can call this multiple times """
        self.socket.bind(endpoint)
        logging.info(f"I: MDP  broker/0.1.1 is active at {endpoint}")

    def service_internal(self, service, msg):
        """ Handle internal service according to spec """
        returncode = "501"
        if "mmi.service" == service:
            name = msg[-1]
            returncode = "200" if name in self.services else "404"
        msg[-1] = returncode

        # Insert the protocol header and service name after the routing envelope
        msg = msg[:2] + [MDP.C_CLIENT, service] + msg[2:]
        msg = msg[:2] + [MDP.C_CLIENT, service] + msg[2:]
        msg = ensure_is_bytes(msg)
        self.socket.send_multipart(msg)

    def send_heartbeats(self):
        """ Send heartbeats to idle worker if it's time """
        if time.time() > self.heartbeat_at:
            for worker in self.waiting:
                # TODO: Send the worker's physical address here??
                # worker.physical_address is where the worker is connecting from as seen by the broker
                self.send_to_worker(worker, MDP.W_HEARTBEAT, None, msg=worker.physical_address)

            self.heartbeat_at = time.time() + 1e-3*self.HEARTBEAT_INTERVAL

    def purge_workers(self):
        if self.waiting:
            self.waiting = sorted(self.waiting, key=lambda worker: worker.expiry)

        while self.waiting:
            w = self.waiting[0]
            if w.expiry < time.time():
                logging.info(f"I: deleting expired worker: {w.identity}")
                self.delete_worker(w, False)
                self.waiting.pop(0)
            else:
                break

    def worker_waiting(self, worker):
        """ This worker is now waiting for work """
        # Queue to broker and service waiting lists
        self.waiting.append(worker)
        worker.service.waiting.append(worker)
        worker.expiry = time.time() + 1e-3*self.HEARTBEAT_EXPIRY
        self.dispatch(worker.service, None)

    def dispatch(self, service, msg):
        """ Dispatch requests to waiting workers as possible """
        assert service is not None
        if msg is not None:
            service.requests.append(msg)
        self.purge_workers()

        while service.waiting and service.requests:
            msg = service.requests.popleft()
            worker = service.waiting.popleft()
            self.waiting.remove(worker)
            self.send_to_worker(worker, MDP.W_REQUEST, None, msg)

    def send_to_worker(self, worker, command, option, msg=None):
        """ Send message to worker. If message is provided, sends that message """
        if msg is None:
            msg = []
        elif not isinstance(msg, list):
            msg = [msg]

        if option is not None:
            msg = [option] + msg
        msg = [worker.address, b"", MDP.W_WORKER, command] + msg
        msg = ensure_is_bytes(msg)     # Try to make everything a byte

        if self.verbose:
            logging.info(f"I: sending {command} to worker")
            dump(msg)

        self.socket.send_multipart(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-port', default=5555, type=int, help='port to listen through')
    parser.add_argument("-v", default=False, type=bool, help='verbose output')

    args = parser.parse_args()

    port = args.port
    verbose = args.v

    print(args)

    """ Create and start new broker """
    broker = MajorDomoBroker(verbose)
    broker.bind(f"tcp://*:{port}")
    broker.mediate()


if __name__ == '__main__':
    main()
