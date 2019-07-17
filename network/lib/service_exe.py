import sys
import time
import json
import inspect
from collections import namedtuple
from typing import List, Tuple
from abc import ABCMeta, abstractmethod

from mdwrkapi import MajorDomoWorker

# MARK: to be imported from other MDP
clsmembers: List = []
s = None


# TODO: Standardize the docstrings for the process method in each of these classes
# TODO: Implement some form of leader election on the first peer-to-peer connection

# MARK: Service definitions
class ServiceExeBase(metaclass=ABCMeta):
    BIND_WAIT: int = 0.2

    def __init__(self, service_name: str = 'base', agent_name: str = ''):
        self.service_name = service_name
        self.worker: MajorDomoWorker = None
        self.worker_name: str = agent_name + '.' + self.service_name

    def run(self, worker: MajorDomoWorker, **kwargs):
        reply = None
        while True:
            request = worker.recv(reply)
            if request is None:
                break

            reply = self.process(request, worker, **kwargs)

    @property
    def leader_bool(self):
        if self.worker:
            return self.worker.leader_bool

    @abstractmethod
    def determine_leader(self):
        """
        Determine the leader in a given peer group for the given service_exe
        """
        pass

    @abstractmethod
    def process(self, *args, **kwargs) -> dict:
        pass


class ServiceExeEcho(ServiceExeBase):
    """
    Simple echo service, doesn't need to coordinate with peers!
    """
    def __init__(self, service_name: str = 'echo', agent_name: str = ''):
        super(ServiceExeEcho, self).__init__(service_name, agent_name)

    # Override process
    def process(self, *args, **kwargs) -> dict:
        try:
            request: dict = json.loads(args[0])
            worker: MajorDomoWorker = args[1]
        except IndexError:
            raise IndexError('Error: worker object has not been supplied:')

        # Do some work
        time.sleep(2)
        payload = request['payload']

        reply = {'payload': payload, 'origin': self.worker_name}
        return reply

    def determine_leader(self):
        """
        Simple echo service doesn't need to coordinate with peers!
        """
        pass


class ServiceExeSumNums(ServiceExeBase):
    """
    Given a target number x from the client, return true if the sum of self with peer add up to target
    request: {'target': <int> 10, ...}
    """
    def __init__(self, service_name: str = 'sumnums', agent_name: str = ''):
        super(ServiceExeSumNums, self).__init__(service_name, agent_name)

    def process(self, *args, **kwargs) -> dict:
        try:
            request: dict = json.loads(args[0])
            worker: MajorDomoWorker = args[1]
            self.worker = worker
        except IndexError:
            raise IndexError('Error: worker object has not been supplied:')

        target: int = int(request['target'])

        if kwargs:
            my_summand: int = kwargs['my_summand']
        else:
            raise KeyError("Need values to provide", {self.service_name})

        # Connect peer_port to all the peers -- Note that the worker possesses the peer port
        peer_port = worker.peer_port
        if not peer_port:
            raise Exception("This service requires peers to exist!")

        peer_port.tie_to_peers()
        time.sleep(self.BIND_WAIT)

        for my_peer_ident in peer_port.peers:
            payload: bytes = str(my_summand).encode('utf8')
            peer_port.send(my_peer_ident, payload=payload)

        # Determine whether this given peer is the group's leader
        self.determine_leader()
        if not self.leader_bool:
            return {}

        # Do some work
        time.sleep(2)
        payload = my_summand

        reply = {'reply': payload, 'origin': self.worker_name}

        # Send a reply
        return reply

    def determine_leader(self):
        assert self.worker, "worker doesn't exist!"
        result = False

        self.worker.leader_bool = result


# MARK: All the goodies, this is done to automate getting the available services directly from the class names
#       i.e. ServiceExeNumberBag --> s.NUMBERBAG = numberbag
clsmembers: List[Tuple[str, object]] = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers: List[str] = [class_name[10:].upper() for class_name, _ in clsmembers if class_name.startswith('Service')]
s = namedtuple('Services', clsmembers)._make(name.lower() for name in clsmembers)
