import os
import threading
from typing import List
from collections import namedtuple
from abc import ABCMeta, abstractmethod

from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker

# MARK: to be imported from other MDP
clsmembers: List = []
s = None


# TODO: Standardize the docstrings for the process method in each of these classes

# MARK: Service definitions
class ServiceExeBase(threading.Thread, metaclass=ABCMeta):
    BIND_WAIT: int = 0.2

    def __init__(self, service_name: str = 'base', agent_name: str = ''):
        super(ServiceExeBase, self).__init__()
        self.service_name = service_name
        self.agent_name: str = agent_name
        self.kwargs = None
        self.worker: MajorDomoWorker = None
        self.peer_port = None

        self.name = f'{self.service_name}-Thread'
        self.shutdown_flag = threading.Event()

    def set_kwargs(self, kwargs):
        self.kwargs = kwargs

    def run(self):
        assert self.kwargs
        self.worker = self.kwargs.get('worker')
        if self.worker:
            reply = None
            while not self.shutdown_flag.is_set():
                request = self.worker.recv(reply)
                if request is None:
                    break

                reply = self.process(request, self.worker, **self.kwargs)

        print(f'{self.getName()} has been stopped')

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

    def quit(self):
        """ Quit and cleanup """
        if self.worker:
            self.worker.destroy()
            self.worker = None


# MARK: All the goodies, this is done to automate getting the available services directly from the class names
curr_dir = os.getcwd()
if not curr_dir.endswith('services'):
    curr_dir = os.path.join(curr_dir, '../services')
dirmembers = os.listdir(curr_dir)
dirmembers: List[str] = [file_name[10:file_name.find('.py')].upper() for file_name in dirmembers if file_name.startswith('serviceExe')]
s = namedtuple('Services', dirmembers)._make(name.lower() for name in dirmembers)


if __name__ == '__main__':
    print(s)
