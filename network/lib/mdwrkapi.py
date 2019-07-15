import logging
import time
import zmq

from zhelpers import dump, ensure_is_bytes, ZMQMonitor, EVENT_MAP, get_host_name_ip
from mdpeer import Peer
import MDP

# TODO: Implement ability for workers within agents to ask for the address of given neighbors!


class MajorDomoWorker(object):
    HEARTBEAT_LIVENESS = 3
    broker = None
    ctx = None
    service = None

    worker = None
    hearbeat_at = 0
    liveness = 0
    heartbeat = 2500
    reconnect = 2500

    expect_reply = False
    timeout = 2500
    verbose = False

    reply_to = None       # Return address if any

    def __init__(self, broker, service, verbose=False, worker_name=MDP.W_WORKER, broker_port=5555):
        self.broker = broker
        self.service = service
        self.verbose = verbose
        if not isinstance(worker_name, bytes):
            agent_name = worker_name.split(".")[0]
            agent_name = agent_name.encode("utf8")
            worker_name = worker_name.encode("utf8")
        else:
            agent_name = worker_name.split(b".")[0]
        self.worker_name: bytes = worker_name      # of format A01.service
        self.agent_name: bytes = agent_name        # of format A01

        self.ctx = zmq.Context()
        self.poller = zmq.Poller()

        self.monitor: ZMQMonitor = None

        # Inter-worker peer handling
        ip_addr = get_host_name_ip()
        self.endpoint = f"tcp://{ip_addr}:{broker_port}".encode('utf8')     # FIXME: Change the port number here?
        self.peers_endpoints: dict = {}    # tcp endpoints of peers for the given service
        self.peer: Peer = None
        if self.peers_endpoints:
            self.peer = None

        logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)

        self.reconnect_to_broker()

        # Monitoring
        event_filter: str = 'ALL' if self.verbose else EVENT_MAP[zmq.EVENT_ACCPETED]
        self.monitor.run(event=event_filter)

    def reconnect_to_broker(self):
        """Connect or reconnect to broker"""
        if self.worker:
            self.poller.unregister(self.worker)
            self.worker.close()

        self.worker = self.ctx.socket(zmq.DEALER)

        # Setup monitor
        self.monitor: ZMQMonitor = ZMQMonitor(self.worker)

        self.worker.identity = self.worker_name
        self.worker.linger = 0
        self.worker.connect(self.broker)
        self.poller.register(self.worker, zmq.POLLIN)
        if self.verbose:
            logging.info(f"I: connecting to broker at {self.broker}...")

        # Register service with broker
        self.send_to_broker(MDP.W_READY, self.service, [])

        # If liveness hits zero, queue is considered disconnected
        self.liveness = self.HEARTBEAT_LIVENESS
        self.heartbeat_at = time.time() + 1e-3 * self.heartbeat

    def send_to_broker(self, command, option=None, msg=None):
        """Send message to broker.
        If no msg is provided, creates one internally
        """
        if msg is None:
            msg = []
        elif not isinstance(msg, list):
            msg = [msg]

        if option:
            msg = [option] + msg

        msg = ['', MDP.W_WORKER, command] + msg
        msg = ensure_is_bytes(msg)     # ensure that the message is only bytes

        if self.verbose:
            logging.info(f"I: sending {command} to broker")
            dump(msg)
        self.worker.send_multipart(msg)

    def recv(self, reply=None):
        """Send reply, if any, to broker and wait for next request."""
        # Format and send the reply if we were provided one
        assert reply is not None or not self.expect_reply

        if reply is not None:
            assert self.reply_to is not None
            try:
                reply = [self.reply_to, ''] + reply
            except TypeError:       # probably trying to concatenate a list with dict
                reply = [self.reply_to, ''] + [reply]
            self.send_to_broker(MDP.W_REPLY, msg=reply)

        self.expect_reply = True

        while True:
            # Poll socket for a reply, with timeout
            try:
                items = self.poller.poll(self.timeout)
            except KeyboardInterrupt:
                break   # Interrupted

            if items:
                msg = self.worker.recv_multipart()
                if self.verbose:
                    logging.info("I: received message from broker: ")
                    dump(msg)

                self.liveness = self.HEARTBEAT_LIVENESS
                # Don't try to handle errors, just assert noisily
                assert len(msg) >= 3

                empty = msg.pop(0)
                assert empty == b''
                header = msg.pop(0)
                assert header == MDP.W_WORKER

                command = msg.pop(0)
                if command == MDP.W_REQUEST:
                    # We should pop and save as many addresses as there are
                    # up to a null part, but for now, just save one...
                    self.reply_to = msg.pop(0)
                    # pop empty
                    empty = msg.pop(0)
                    assert empty == b''
                    actual_msg = msg.pop(0)
                    self.peers_endpoints = msg[0]
                    return actual_msg  # We have a request to process

                elif command == MDP.W_HEARTBEAT:
                    # do nothing on the heartbeat
                    pass

                elif command == MDP.W_DISCONNECT:
                    self.reconnect_to_broker()

                else:
                    logging.error("E: invalid input message: ")
                    dump(msg)

            else:
                self.liveness -= 1
                if self.liveness == 0:
                    if self.verbose:
                        logging.warning("W: disconnected from broker - retrying...")
                    try:
                        time.sleep(1e-3*self.reconnect)
                    except KeyboardInterrupt:
                        break
                    self.reconnect_to_broker()

            # Send HEARTBEAT if it's time
            if time.time() > self.heartbeat_at:
                self.send_to_broker(MDP.W_HEARTBEAT, msg=self.endpoint)
                self.heartbeat_at = time.time() + 1e-3*self.heartbeat

        logging.warning("W: interrupt received, killing worker...")
        self.monitor.stop()
        return None

    def destroy(self):
        self.ctx.destroy(0)

