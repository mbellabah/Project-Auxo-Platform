import logging

import zmq

import auxo_olympus.lib.utils.MDP as MDP
from auxo_olympus.lib.utils.zhelpers import dump, ensure_is_bytes


class MajorDomoClient(object):
    """Majordomo Protocol Client API, Python version.
      Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.
    """
    broker = None
    ctx = None
    client = None
    poller = None
    timeout = 2500
    verbose = False

    def __init__(self, broker, verbose=False, client_name=MDP.C_CLIENT):
        self.broker = broker
        self.verbose = verbose
        if not isinstance(client_name, bytes):
            client_name = client_name.encode("utf8")
        self.client_name = client_name
        self.agent_type = MDP.C_CLIENT
        self.ctx = zmq.Context()
        self.poller = zmq.Poller()
        logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
        self.reconnect_to_broker()

    def reconnect_to_broker(self):
        """Connect or reconnect to broker"""
        if self.client:
            self.poller.unregister(self.client)
            self.client.close()
        self.client = self.ctx.socket(zmq.DEALER)
        self.client.linger = 0
        self.client.connect(self.broker)
        self.poller.register(self.client, zmq.POLLIN)
        if self.verbose:
            logging.info("I: connecting to broker at %s...", self.broker)

    def send(self, service: str, request: str):
        """Send request to broker
        """
        if not isinstance(request, list):
            request = [request.encode("utf8")]

        # Prefix request with protocol frames
        # Frame 0: empty (REQ emulation)
        # Frame 1: "MDPCxy" (six bytes, MDP/Client x.y)
        # Frame 2: Service name (printable string -- encode to bytes)

        request = [b"", MDP.C_CLIENT, self.client_name, service] + request
        request = ensure_is_bytes(request)
        if self.verbose:
            logging.warning("I: send request to '%s' service: ", service)
            dump(request)
        self.client.send_multipart(request)

    def recv(self):
        """Returns the reply message or None if there was no reply."""
        try:
            items = self.poller.poll(self.timeout)
        except KeyboardInterrupt:
            return    # interrupted

        if items:
            # if we got a reply, process it
            msg = self.client.recv_multipart()
            if self.verbose:
                logging.info("I: received reply:")
                dump(msg)

            # Don't try to handle errors, just assert noisily
            assert len(msg) >= 4

            _ = msg.pop(0)
            header = msg.pop(0)
            assert self.agent_type == header
            service = msg.pop(0)
            return msg
        else:
            logging.warning("W: permanent error, abandoning request")
