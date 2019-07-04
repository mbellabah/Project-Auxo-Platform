"""
Request-reply client in python
Connects REQ socket to tcp://localhost:5559
Sends Hello to server, expects World back
"""

import zmq


context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5559")

# Make 10 requests, wait each time for a response
for request in range(1, 11):
    socket.send(b"Hello")
    message = socket.recv()
    print("Received reply", request, message)
