from abc import ABCMeta, abstractmethod
import time

import MDP


class ServiceExeBase(metaclass=ABCMeta):
    def __init__(self, service_name: str = MDP.S_NONE, agent_name: str = ''):
        self.service_name = service_name
        self.worker = None
        self.worker_name: str = agent_name + '.' + self.service_name

    def run(self, worker):
        reply = None
        while True:
            request = worker.recv(reply)
            if request is None:
                break

            reply = self.process(request)

    @abstractmethod
    def process(self, *args) -> dict:
        pass


class ServiceExeEcho(ServiceExeBase):
    def __init__(self, service_name: str = MDP.S_ECHO, agent_name: str = ''):
        super(ServiceExeEcho, self).__init__(service_name, agent_name)

    # Override process
    def process(self, *args) -> dict:
        request = args[0]

        # Do some work
        time.sleep(2)
        payload = request

        reply = {'payload': payload, 'origin': self.worker_name}
        return reply
