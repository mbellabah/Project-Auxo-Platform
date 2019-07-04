import zmq
import uuid
import utils


class Peer(object):
    def __init__(self, broker, port):
        self.broker = broker       # ip address of the broker's front facing socket
        self.port = port       # port of the broker's front facing socket

        self.id = uuid.uuid4()
        self.my_ip = utils.get_ip()
        self.socket = None

    def connect_to_broker(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{self.broker}:{self.port}")

    def send_request(self, msg):
        assert self.socket is not None, "Failed to connect to broker"
        self.socket.send_m(msg)

    def receive_reply(self):
        msg = self.socket.recv_multipart()
        return msg

    def run(self):
        self.connect_to_broker()

        for request in range(1, 11):
            self.send_request(msg={"sender": self.my_ip, "payload": request})
            msg = self.receive_reply()
            print("Received", msg)


if __name__ == '__main__':
    # IP address of broker: 192.168.0.104
    broker = "192.168.0.104"
    port = 5559
    peer = Peer(broker=broker, port=port)
    peer.run()
