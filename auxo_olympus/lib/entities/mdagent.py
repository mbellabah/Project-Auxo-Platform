import json
import queue
import argparse
from typing import Dict, Tuple

from auxo_olympus.lib.utils import MDP
from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker

# Import the relevant services
from auxo_olympus.lib.services import service_exe as se
from auxo_olympus.lib.services.service_exe import s as SERVICE
from auxo_olympus.lib.services import serviceExeSumNums, serviceExeEcho

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
        self.agent_type = MDP.A_AGENT

        self.result_q = queue.Queue()

        # Define the services here!
        self.available_services = [SERVICE.ECHO, SERVICE.SUMNUMS]
        self.running_services: Dict[str, se.ServiceExeBase] = {}

    def start_service(self, service, result_q, **kwargs) -> se.ServiceExeBase:
        assert self.available_services, "No services exist!"
        assert service in self.available_services, f"Can't run {service}"

        package = {
            'ip': self.broker,
            'port': self.port,
            'own_port': self.port,
            'verbose': True,
            'result_q': self.result_q,
            'inputs': kwargs
        }
        service_exe = self.service_handler(service, kwargs=package)

        service_exe.set_kwargs()

        self.running_services[service] = service_exe
        service_exe.start()
        return service_exe

    def service_handler(self, service: str, kwargs) -> se.ServiceExeBase:
        if service == SERVICE.ECHO:
            return serviceExeEcho.ServiceExeEcho(self.agent_name)

        elif service == SERVICE.SUMNUMS:
            return serviceExeSumNums.ServiceExeSumNums(self.agent_name, kwargs)

    def run(self, initial_service=None, **kwargs):
        """ Runs a single service to completion/interruption """
        try:
            curr_service = self.start_service(service=initial_service, result_q=self.result_q, **kwargs)
        except Exception as e:
            raise Exception(f'Something went wrong {repr(e)}')

        assert curr_service
        while self.result_q.empty():
            try:
                pass
            except KeyboardInterrupt:
                break
        else:
            print(f'{initial_service} Complete!')
            _ = self.result_q.get()
            self.cleanup()

    def cleanup(self):
        for service_name, service in self.running_services.items():
            if service.is_alive():
                service.join(0.0)

        self.running_services.clear()


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
