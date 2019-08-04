import time
import json
from typing import List

import auxo_olympus.lib.utils.MDP as MDP
import auxo_olympus.lib.services.work_functions as wf
from auxo_olympus.lib.utils.zhelpers import strip_of_bytes
from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.services.service_exe import ServiceExeBase


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