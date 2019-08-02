import zmq
from zhelpers import dump
context = zmq.Context()

sink = context.socket(zmq.ROUTER)
sink.bind("inproc://example")

# First allow 0MQ to set the identity
anonymous = context.socket(zmq.DEALER)
anonymous.connect("inproc://example")
anonymous.send(b"Router uses a generated UUID")
dump(sink)

# set the identities ourselves
identified = context.socket(zmq.DEALER)
identified.identity = b"Peer2"
identified.connect("inproc://example")
extra_info = identified.getsockopt(zmq.LAST_ENDPOINT)
print('HEY', extra_info)
identified.send(b"Router socket uses REQ's socket identity")
dump(sink)