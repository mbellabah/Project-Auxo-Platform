"""
Given a target number x from the client, return true if the sum of self with peer add up to target
request: {'target': <int> 10, ...}

Expected Client Request
input: {
    "multiple_bool": <bool>      Coordination required?
    "target": <int>              Target value to add up to
}

Provided Agent Input
input: {
    "my_summand": <int>
}

"""

import time
import json
from typing import List

import auxo_olympus.lib.services.serviceExeSumNums.work_functions as wf
from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.services.service_exe import ServiceExeBase


class ServiceExeSumNums(ServiceExeBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.service_name = 'sumnums'
        self.name = f'{self.service_name}-Thread'

    def process(self, *args) -> dict:
        try:
            request: dict = json.loads(args[0])
            worker: MajorDomoWorker = args[1]
        except IndexError:
            raise IndexError('Error: worker object has not been supplied:')

        self.worker = worker
        self.peer_port = worker.peer_port

        assert self.peer_port, "This service requires peers to exist!"
        assert self.inputs, "Need to provide kwargs when initing service"

        # Extract relevant details from the requests and inputs
        target_number: int = int(request['target'])
        my_summand: int = self.inputs.get('my_summand', 0)

        # Populate the peer-ports state-space
        self.peer_port.state_space['my_summand'] = my_summand
        self.peer_port.state_space['target_number'] = target_number

        # Connect peer_port to all the peers -- Note that the worker possesses the peer port
        self.peer_port.tie_to_peers()
        time.sleep(self.BIND_WAIT)

        if self.leader_bool:
            self.request_from_peers(state='my_summand')

            # state_space {'other_peer_data': {'A02.sumnums.peer': {'my_summand': 8}}, 'my_summand': 2, 'target_number': 10}
            all_summands = [my_summand]
            for peer, data in self.peer_port.state_space['other_peer_data'].items():
                all_summands.append(data['my_summand'])

            # DO WORK! Formulate reply
            payload = self.work(all_nums=all_summands, target=target_number)
            reply = {'reply': payload, 'origin': self.worker_name}

            # inform peers that leader is done and so they can die
            self.inform_peers()     # Peers that are not leaders will shutdown themselves
            self.peer_port.stop()
        else:
            reply = None

        return reply

    @staticmethod
    def work(all_nums: List[int], target: int) -> str:
        out = wf.find_pair_adding_to_target(all_nums, target)
        return str(out)

