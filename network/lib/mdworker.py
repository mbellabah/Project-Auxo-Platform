import sys
import MDP
from mdwrkapi import MajorDomoWorker

import json

# TODO: Interconnect the workers, perhaps use pub and sub -- better to receive the endpoints
#       from the broker, and use that to connect with various workers on the same service!
# TODO: Construct class abstractions for a worker

# TODO: Implement the json thing
# TODO: Interconnec the agents in layer 3


class Worker(object):
    def __init__(self, worker_name, broker, port, verbose, service="echo"):
        self.worker_name = worker_name
        self.broker = broker        # Broker's ip addr
        self.port = port            # Broker's port
        self.verbose = verbose
        self.agent_type = MDP.W_WORKER

        self.service = service
        self.services = {
            "echo": self.service_echo
        }

        self.worker = MajorDomoWorker(f"tcp://{self.broker}:{self.port}", self.service, self.verbose, self.worker_name)

    def change_service(self, service_name):
        if service_name in self.services:
            self.service = service_name
        else:
            raise Exception(f"{service_name} behavior does not exist in this worker: {self.worker_name}")

    def service_echo(self):
        assert self.service == "echo"
        reply = None
        while True:
            request = self.worker.recv(reply)
            if request is None:
                break
            reply = {request, self.worker_name}   # simple echo
            reply = json.dumps(reply).encode("utf8")

    def run(self):
        # run the service function
        self.services[self.service]()


def main():
    user_args = sys.argv
    verbose = '-v' in user_args

    # Args: -v *verbose* host port worker_name
    broker_addr = "localhost"      # Ip address of the broker
    port = 5555
    worker_name = 'W?'
    if len(user_args) > 2:
        broker_addr = user_args[2]
        port = user_args[3]
        worker_name = user_args[4]

    # Instantiate and dispatch the worker
    worker = Worker(worker_name, broker_addr, port, verbose, service="echo")
    worker.run()


if __name__ == '__main__':
    main()
