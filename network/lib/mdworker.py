import sys
import MDP
from mdwrkapi import MajorDomoWorker

# TODO: Interconnect the workers, perhaps use pub and sub -- better to receive the endpoints
#       from the broker, and use that to connect with various workers on the same service!
# TODO: Construct class abstractions for a worker

# TODO: Implement the json thing
# TODO: Interconnect the agents in layer 3


class Worker(object):
    def __init__(self, worker_name, broker, port, verbose, service="echo"):
        self.worker_name = worker_name
        self.broker = broker        # Broker's ip addr
        self.port = port            # Broker's port
        self.verbose = verbose
        self.agent_type = MDP.W_WORKER

        self.service = service
        self.services = {
            "echo": self.service_echo,
            "none": self.service_none
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
            reply = {'payload': request, 'origin': self.worker_name}   # simple echo

    def service_none(self):
        assert self.service == "none"
        reply = None
        while True:
            request = self.worker.recv(reply)
            if request is None:
                break
            reply = None

    def run(self):
        # run the service function
        try:
            self.services[self.service]()
        except KeyError as e:
            print(f"{self.service} behaivor is not implemented: {e}")

def main():
    user_args = sys.argv
    verbose = '-v' in user_args

    # Args: -v *verbose* host port worker_name
    broker_addr = "localhost"      # Ip address of the broker
    port = 5555
    worker_name = 'W?'
    service = "echo"
    if len(user_args) > 2:
        broker_addr = user_args[2]
        port = user_args[3]
        worker_name = user_args[4]
        service = user_args[5]

    # Instantiate and dispatch the worker
    worker = Worker(worker_name, broker_addr, port, verbose, service)
    worker.run()


if __name__ == '__main__':
    main()
