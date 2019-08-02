import sys
import time
import json
import inspect
from typing import List, Tuple
from collections import namedtuple
from abc import ABCMeta, abstractmethod

import auxo_olympus.lib.MDP as MDP
import auxo_olympus.lib.work_functions as wf
from auxo_olympus.lib.zhelpers import strip_of_bytes
from auxo_olympus.lib.mdwrkapi import MajorDomoWorker

# MARK: to be imported from other MDP
clsmembers: List = []
s = None


# TODO: Standardize the docstrings for the process method in each of these classes

# MARK: Service definitions
class ServiceExeBase(metaclass=ABCMeta):
    BIND_WAIT: int = 0.2

    def __init__(self, service_name: str = 'base', agent_name: str = ''):
        self.service_name = service_name
        self.worker: MajorDomoWorker = None
        self.worker_name: str = agent_name + '.' + self.service_name
        self.peer_port = None

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
            self.peer_port = worker.peer_port
        except IndexError:
            raise IndexError('Error: worker object has not been supplied:')

        assert self.peer_port, "This service requires peers to exist!"
        assert kwargs, "Need to provide kwargs"
        target_number: int = int(request['target'])
        my_summand: int = kwargs['my_summand']

        # Populate the peer-ports state-space
        self.peer_port.state_space['my_summand'] = my_summand
        self.peer_port.state_space['target_number'] = target_number

        # Connect peer_port to all the peers -- Note that the worker possesses the peer port
        self.peer_port.tie_to_peers()
        time.sleep(self.BIND_WAIT)

        # Determine whether this given peer is the group's leader
        if not self.leader_bool:
            return {}

        assert self.leader_bool, f'{self.peer_port.peer_name} is not the leader of the peer group!'
        # leader sends request to all attached peers asking for their info
        for peer_identity in self.peer_port.peers:
            request: dict = strip_of_bytes({'origin': self.peer_port.peer_name, 'command': MDP.W_REQUEST, 'request_state': 'my_summand'})
            request: bytes = json.dumps(request).encode('utf8')
            self.peer_port.send(peer_identity, payload=request)

        while len(self.peer_port.state_space['other_peer_data']) != len(self.peer_port.peers):
            # Wait until we receive everything from all th peers
            pass

        # state_space {'other_peer_data': {'A02.sumnums.peer': {'my_summand': 8}}, 'my_summand': 2, 'target_number': 10}
        all_summands = [my_summand]
        for peer, data in self.peer_port.state_space['other_peer_data'].items():
            all_summands.append(data['my_summand'])

        # DO WORK!
        payload = self.work(all_nums=all_summands, target=target_number)

        reply = {'reply': payload, 'origin': self.worker_name}
        return reply

    @staticmethod
    def work(all_nums: List[int], target: int) -> str:
        out = wf.find_pair_adding_to_target(all_nums, target)
        return str(out)


# MARK: All the goodies, this is done to automate getting the available services directly from the class names
#       i.e. ServiceExeNumberBag --> s.NUMBERBAG = numberbag
clsmembers: List[Tuple[str, object]] = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers: List[str] = [class_name[10:].upper() for class_name, _ in clsmembers if class_name.startswith('Service')]
s = namedtuple('Services', clsmembers)._make(name.lower() for name in clsmembers)
