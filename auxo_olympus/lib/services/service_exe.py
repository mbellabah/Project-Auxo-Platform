import os
import json
import threading
from pathlib import Path
from typing import List, Dict
from collections import namedtuple
from abc import ABCMeta, abstractmethod

from auxo_olympus.lib.utils.zhelpers import strip_of_bytes
from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.utils import MDP

# MARK: to be imported from other MDP
s = None


# TODO: Standardize the docstrings for the process method in each of these classes

# MARK: Service definitions
class ServiceExeBase(threading.Thread, metaclass=ABCMeta):
    BIND_WAIT: int = 0.2

    def __init__(self, *args):
        super().__init__()
        self.args = args
        self.kwargs = args[1]

        self.service_name = 'base'
        self.agent_name: str = self.args[0]

        self.worker: MajorDomoWorker = None
        self.ip = None
        self.port = None
        self.own_port = None
        self.verbose = False
        self.result_q = None
        self.got_req_q = None
        self.inputs = {}     # the owned inputs relevant to the problem

        self.peer_port = None
        self.name = f'{self.service_name}-Thread'
        self.daemon = True

        self.set_kwargs()

    def set_kwargs(self):
        # Set the variables from the kwargs -- kwargs originate from the mdagent class (package)
        for kwarg_variable in self.kwargs:
            setattr(self, kwarg_variable, self.kwargs[kwarg_variable])
        self.kwargs['worker'] = self.create_new_worker(worker_name=self.worker_name, service=self.service_name)

    def run(self):
        assert self.kwargs
        self.worker = self.kwargs.get('worker')
        status = MDP.SUCCESS

        if self.worker:
            reply = None
            request = self.worker.recv(reply=None)
            try:
                reply = self.process(request, self.worker, self.inputs)
            except Exception as e:
                status = MDP.FAIL
                print(f"Error: {repr(e)}")

            _ = self.worker.recv(reply)     # send reply, don't get msg back

            # assert self.peer_port.shutdown_flag
            self.result_q.put(status)       # how we signal to the main agent that this service-exe is complete

    def create_new_worker(self, worker_name, service):
        worker = MajorDomoWorker(f"tcp://{self.ip}:{self.port}", service, self.verbose, worker_name, own_port=self.own_port)
        return worker

    @property
    def leader_bool(self):
        if self.worker:
            return self.worker.leader_bool

    @property
    def worker_name(self):
        return self.agent_name + '.' + self.service_name

    @abstractmethod
    def process(self, *args, **kwargs) -> dict:
        pass

    # P2P suite
    def request_from_peers(self, state: str, send_to: List[bytes] or Dict[bytes, str]):
        # Send request to all attached peers asking for particular information
        for peer_identity in send_to:
            request: dict = strip_of_bytes(
                {'origin': self.peer_port.peer_name, 'command': MDP.W_REQUEST, 'request_state': state}
            )
            request: bytes = json.dumps(request).encode('utf8')
            self.peer_port.send(peer_identity, payload=request)

        while len(self.peer_port.state_space['other_peer_data']) != len(self.peer_port.peers):
            # Wait until we receive everything from all the peers
            pass

    def inform_peers(self, send_to: List[bytes] or Dict[bytes, str]):
        assert self.leader_bool, f'{self.peer_port.peer_name} is not the leader of the peer group!'

        for peer_identity in send_to:
            info: dict = strip_of_bytes(
                {'origin': self.peer_port.peer_name, 'command': MDP.W_DISCONNECT, 'info': 'DONE'}
            )
            info: bytes = json.dumps(info).encode('utf8')
            self.peer_port.send(peer_identity, payload=info)

    def quit(self):
        """ Quit and cleanup """
        if self.worker:
            self.worker.destroy()
            self.worker = None

    def join(self, timeout=None):
        self.quit()
        super(ServiceExeBase, self).join(timeout)


# MARK: All the goodies, this is done to automate getting the available services directly from the class names
curr_dir = Path(os.getcwd())
if not curr_dir.name == 'services':
    curr_dir = curr_dir.parent.joinpath('services')

dirmembers = os.listdir(curr_dir)
dirmembers: List[str] = [file_name[10:].upper() for file_name in dirmembers if file_name.startswith('serviceExe')]
s = namedtuple('Services', dirmembers)._make(name.lower() for name in dirmembers)

if __name__ == '__main__':
    print(s)
