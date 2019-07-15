from abc import ABCMeta, abstractmethod
import time

import MDP


class ServiceExeBase(metaclass=ABCMeta):
    def __init__(self, service_name: str = MDP.S_NONE, worker=None):
        self.service_name = service_name
        self.worker = worker
        self.worker_name: str = self.worker.worker_name.decode('utf8')      # owns this service

    def run(self):
        reply = None
        while True:
            request = self.worker.recv(reply)
            if request is None:
                break

            reply = self.process(request)

    @abstractmethod
    def process(self, *args) -> dict:
        pass


class ServiceExeEcho(ServiceExeBase):
    def __init__(self, service_name: str = MDP.S_ECHO, worker=None):
        super(ServiceExeEcho, self).__init__(service_name, worker)

    # Override process
    def process(self, *args) -> dict:
        request = args[0]

        # Do some work
        time.sleep(2)
        payload = request

        reply = {'payload': payload, 'origin': self.worker_name}
        return reply
