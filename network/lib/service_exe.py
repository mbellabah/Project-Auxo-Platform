import sys
import time
import inspect
from collections import namedtuple
from typing import List, Tuple
from abc import ABCMeta, abstractmethod

from mdwrkapi import MajorDomoWorker
import MDP

# MARK: to be imported from other MDP
clsmembers: List = []
s = None


class ServiceExeBase(metaclass=ABCMeta):
    def __init__(self, service_name: str = 'base', agent_name: str = ''):
        self.service_name = service_name
        self.worker = None
        self.worker_name: str = agent_name + '.' + self.service_name

    def run(self, worker: MajorDomoWorker):
        reply = None
        while True:
            request = worker.recv(reply)
            if request is None:
                break

            reply = self.process(request, worker)

    @abstractmethod
    def process(self, *args) -> dict:
        pass


class ServiceExeEcho(ServiceExeBase):
    """
    Simple echo service, doesn't need to coordinate with peers!
    """
    def __init__(self, service_name: str = 'echo', agent_name: str = ''):
        super(ServiceExeEcho, self).__init__(service_name, agent_name)

    # Override process
    def process(self, *args) -> dict:
        try:
            request = args[0]
            worker: MajorDomoWorker = args[1]
        except IndexError:
            raise IndexError('Error: worker object has not been supplied:')

        # Connect peer_port to all the peers -- Note that the worker possesses the peer port
        peer_port = worker.peer_port
        # assert peer_port, f"ensure peer_port exists, i.e. the worker has peers with same service: {self.service_name}"
        if peer_port:
            peer_port.tie_to_peers()

        # Do some work
        time.sleep(2)
        payload = request

        reply = {'payload': payload, 'origin': self.worker_name}
        return reply


class ServiceExeNumberBag(ServiceExeBase):
    """
    Given a target number x from the client, return true if
    """
    def __init__(self):
        pass


clsmembers: List[Tuple[str, object]] = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers: List[str] = [class_name[10:].upper() for class_name, _ in clsmembers if class_name.startswith('Service')]
s = namedtuple('Services', clsmembers)._make(name.lower() for name in clsmembers)
