import json
import time
import queue
import argparse
from typing import Dict

from auxo_olympus.lib.utils import MDP

# Import the relevant services
from auxo_olympus.lib.services import service_exe as se
from auxo_olympus.lib.services.service_exe import s as SERVICE

# TODO: Connect the main agent with all of its running workers via zmq??
# TODO: Have agents shutdown cleanly
# TODO: Make the workers/service_exe within the agent multithreaded


class Agent(object):
    TIMEOUT = 5

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

        self.got_req_q = queue.Queue(maxsize=1)
        self.result_q = queue.Queue(maxsize=1)

        # Define the services here!
        self.available_services = [SERVICE.ECHO, SERVICE.SUMNUMS, SERVICE.VERTEXCOLORING]
        self.running_services: Dict[str, se.ServiceExeBase] = {}

    def start_service(self, service, **kwargs) -> se.ServiceExeBase:
        assert self.available_services, "No services exist!"
        assert service in self.available_services, f"Can't run {service} -- doesn't exist"

        package = {
            'ip': self.broker,
            'port': self.port,
            'own_port': self.port,
            'verbose': True,
            'result_q': self.result_q,
            'got_req_q': self.got_req_q,
            'inputs': kwargs
        }
        service_exe = self.service_handler(service, kwargs=package)

        service_exe.set_kwargs()

        self.running_services[service] = service_exe
        service_exe.start()
        return service_exe

    def service_handler(self, service: str, kwargs) -> se.ServiceExeBase:
        if service == SERVICE.ECHO:
            from auxo_olympus.lib.services.serviceExeEcho import serviceExeEcho
            return serviceExeEcho.ServiceExeEcho(self.agent_name)

        elif service == SERVICE.SUMNUMS:
            from auxo_olympus.lib.services.serviceExeSumNums import serviceExeSumNums
            return serviceExeSumNums.ServiceExeSumNums(self.agent_name, kwargs)

        elif service == SERVICE.VERTEXCOLORING:
            from auxo_olympus.lib.services.serviceExeVertexColoring import serviceExeVertexColoring
            return serviceExeVertexColoring.ServiceExeVertexColoring(self.agent_name, kwargs)

    def run(self, initial_service=None, **kwargs):
        """ Runs a single service to completion/interruption """
        try:
            curr_service = self.start_service(service=initial_service, result_q=self.result_q, **kwargs)
        except Exception as e:
            raise Exception(f'Something went wrong {repr(e)}')

        assert curr_service

        t_end = time.time() + self.TIMEOUT + 60*100
        try:
            while self.result_q.empty() and time.time() < t_end:
                if not self.got_req_q.empty():
                    t_end = time.time() + self.TIMEOUT
                    _ = self.got_req_q.get(block=False)

            else:
                try:
                    status = self.result_q.get(block=False)     # pop from queue
                except queue.Empty:
                    status = MDP.TIMEOUT

                if status == MDP.SUCCESS:
                    print(f'{initial_service} successfully completed :)')
                elif status == MDP.FAIL:
                    print(f'{initial_service} failed :(')
                elif status == MDP.TIMEOUT:
                    print(f'{initial_service} timed out :(')

                assert self.result_q.empty()
                assert self.got_req_q.empty()

        except KeyboardInterrupt:
            pass

        self.cleanup(service_name=initial_service)

    def cleanup(self, service_name: str):
        if service_name == 'ALL':
            for service_name, service in self.running_services.items():
                if service.is_alive():
                    service.join(0.0)

            self.running_services.clear()
        else:
            curr_service = self.running_services[service_name]
            if curr_service.is_alive():
                curr_service.join(0.0)

            self.running_services.pop(service_name)


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
    print("#"*40)

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
