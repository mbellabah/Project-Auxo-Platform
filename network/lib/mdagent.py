import sys
import MDP
from mdwrkapi import MajorDomoWorker

import argparse
from typing import Dict

# TODO: Interconnect the workers, perhaps use pub and sub -- better to receive the endpoints
#       from the broker, and use that to connect with various workers on the same service!
# TODO: Interconnect the agents in layer 3


class Agent(object):
    def __init__(self, agent_name, broker, port, verbose):
        """
        An agent
        :param agent_name::
        :param broker:
        :param port:
        :param verbose:
        """
        self.agent_name = agent_name
        self.broker = broker        # Broker's ip addr
        self.port = port            # Broker's port
        self.verbose = verbose
        self.agent_type = MDP.W_WORKER

        self.services = {
            MDP.S_ECHO: self.service_echo,
            MDP.S_NONE: self.service_none
        }

        self.workers: Dict[str, MajorDomoWorker] = {}

    def create_new_worker(self, worker_name, service):
        """
        Creates a new worker for a given service as of now, 1 worker per service
        :return:
        """
        worker = MajorDomoWorker(f"tcp://{self.broker}:{self.port}", service, self.verbose, worker_name)
        self.workers[service] = worker
        return worker

    def delete_worker(self, service):
        """ Deletes the worker from all data structures and deletes worker """
        worker = self.workers.pop(service, None)
        assert worker is not None
        worker.destroy()

    def service_echo(self):
        worker = self.create_new_worker(worker_name=self.agent_name+"."+MDP.S_ECHO, service=MDP.S_ECHO)
        reply = None
        while True:
            request = worker.recv(reply)
            if request is None:
                break
            reply = {'payload': request, 'origin': self.agent_name}   # simple echo

    def service_none(self):
        worker = self.create_new_worker(worker_name=self.agent_name+"."+MDP.S_NONE, service=MDP.S_NONE)
        reply = None
        while True:
            request = worker.recv(reply)
            if request is None:
                break
            reply = {'payload': None, 'origin': self.agent_name}

    def run(self, service):
        # run the service function
        try:
            self.services[service]()
        except KeyError as e:
            print(f"{service} behavior is not implemented: {e}")
        except KeyboardInterrupt:
            print(f"Killing {service} worker")
            self.delete_worker(service)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('broker_ip', default='localhost', type=str, help='ip address of the broker')
    parser.add_argument('port', default=55555, type=int, help='port to listen through')
    parser.add_argument('service', default='echo', type=str, help='initial service for the agent')
    parser.add_argument('agent_name', type=str, help='agent\'s name')
    parser.add_argument("-v", default=False, type=bool, help=' verbose output')

    args = parser.parse_args()

    verbose = args.v
    broker_addr = args.broker_ip
    port = args.port
    agent_name = args.agent_name
    service = args.service

    # Instantiate and dispatch the worker
    agent = Agent(agent_name, broker_addr, port, verbose)
    agent.run(service=service)


if __name__ == '__main__':
    main()
