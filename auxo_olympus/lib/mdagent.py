import json
import time
import argparse
import threading
from typing import Dict

import auxo_olympus.lib.MDP as MDP
from auxo_olympus.lib.service_exe import s as SERVICE
import auxo_olympus.lib.service_exe as se
from auxo_olympus.lib.mdwrkapi import MajorDomoWorker

# TODO: Connect the main agent with all of its running workers via zmq??
# TODO: Have agents shutdown cleanly
# TODO: Make the workers/service_exe within the agent multithreaded


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
            SERVICE.ECHO: se.ServiceExeEcho(agent_name=self.agent_name),
            SERVICE.SUMNUMS: se.ServiceExeSumNums(agent_name=self.agent_name)
        }

        self.workers: Dict[str, MajorDomoWorker] = {}
        self.service_threads: Dict[str, threading.Thread] = {}

    def create_new_worker(self, worker_name, service):
        """
        Creates a new worker for a given service as of now, 1 worker per service
        :return:
        """
        worker = MajorDomoWorker(f"tcp://{self.broker}:{self.port}", service, self.verbose, worker_name, own_port=self.port)
        self.workers[service] = worker
        return worker

    def delete_worker(self, service):
        """ Deletes the worker from all data structures and deletes worker """
        worker = self.workers.pop(service, None)
        assert worker is not None
        worker.destroy()

    def start_service(self, service, **kwargs):
        assert self.services, "No services exist!"

        # run the service function
        try:
            service_exe: se.ServiceExeBase = self.services[service]
            worker: MajorDomoWorker = self.create_new_worker(worker_name=service_exe.worker_name, service=service_exe.service_name)

            # Create and start new thread
            service_thread = threading.Thread(target=service_exe.run, args=(worker,), kwargs=kwargs, name=f'{service}-Thread')
            self.service_threads[f'{service}-Thread'] = service_thread
            service_thread.setDaemon(True)
            service_thread.start()

            # Kill the worker
            service_thread.join()
            service_exe.worker.destroy()

        except KeyError as e:
            print(f"{service} behavior is not implemented: {repr(e)}")

        except KeyboardInterrupt:
            print(f"Killing {service} worker")
            self.delete_worker(service)

    def run(self, initial_service=None, run_once_flag=True, **kwargs):
        _run_once_flag = run_once_flag
        while True:
            if _run_once_flag:
                self.start_service(initial_service, **kwargs)
                _run_once_flag = False

            print(self.service_threads[f'{initial_service}-Thread'].isAlive())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-broker_ip', default='localhost', type=str, help='ip address of the broker')
    parser.add_argument('-port', default=5555, type=int, help='port to listen through')
    parser.add_argument('-service', default='echo', type=str, help='initial service for the agent')
    parser.add_argument('agent_name', type=str, help='agent\'s name')
    parser.add_argument("-v", default=False, type=bool, help='verbose output')
    parser.add_argument("-d", '--inputs', type=json.loads, help='inputs that correspond to the service')

    args = parser.parse_args()

    print(args)

    verbose = args.v
    broker_addr = args.broker_ip
    port = args.port
    agent_name = args.agent_name
    service = args.service
    inputs: dict = args.inputs

    # Instantiate and dispatch the worker
    agent = Agent(agent_name, broker_addr, port, verbose)
    agent.run(initial_service=service, **inputs)


if __name__ == '__main__':
    main()
