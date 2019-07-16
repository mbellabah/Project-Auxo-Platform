import sys
import time
import argparse
from typing import Dict

import MDP
from service_exe import s as SERVICE
import service_exe as se
from mdwrkapi import MajorDomoWorker

# TODO: Connect the main agent with all of its running workers via zmq??


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

        # Define the services here!
        self.services = {
            SERVICE.ECHO: se.ServiceExeEcho(agent_name=self.agent_name)
        }

        self.workers: Dict[str, MajorDomoWorker] = {}

    def create_new_worker(self, worker_name, service):
        """
        Creates a new worker for a given service as of now, 1 worker per service
        :return:
        """
        worker = MajorDomoWorker(f"tcp://{self.broker}:{self.port}", service, self.verbose, worker_name, self.port)
        self.workers[service] = worker
        return worker

    def delete_worker(self, service):
        """ Deletes the worker from all data structures and deletes worker """
        worker = self.workers.pop(service, None)
        assert worker is not None
        worker.destroy()

    def run(self, service, **kwargs):
        assert self.services, "No services exist!"

        # run the service function
        try:
            service_exe: se.ServiceExeBase = self.services[service]
            worker: MajorDomoWorker = self.create_new_worker(worker_name=service_exe.worker_name, service=service_exe.service_name)
            # run
            service_exe.run(worker)

        except KeyError as e:
            print(f"{service} behavior is not implemented: {repr(e)}")

        except KeyboardInterrupt:
            print(f"Killing {service} worker")
            self.delete_worker(service)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-broker_ip', default='localhost', type=str, help='ip address of the broker')
    parser.add_argument('-port', default=5555, type=int, help='port to listen through')
    parser.add_argument('-service', default='echo', type=str, help='initial service for the agent')
    parser.add_argument('agent_name', type=str, help='agent\'s name')
    parser.add_argument("-v", default=False, type=bool, help=' verbose output')

    args = parser.parse_args()

    print(args)

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
