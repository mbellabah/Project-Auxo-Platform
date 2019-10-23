import time
import json
from typing import List, Dict

from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.services.service_exe import ServiceExeBase


# NOT COMPLETE !

class ServiceExeVertexColoring(ServiceExeBase):
    """
    Given undirected graph G = (V, E), assign a color c_v to each vertex
    such that for an edge (v,w), c_v != c_w

    solves through greedy sequential
    1: while there is an uncolored vertex v do
    2: color v with the minimal color (number) that does not conflict with the
    already colored neighbors
    3: end while
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.service_name = 'vertexcoloring'
        self.name = f'{self.service_name}-Thread'

    def process(self, *args, **kwargs) -> dict:
        try:
            request: dict = json.loads(args[0])
            worker: MajorDomoWorker = args[1]
        except IndexError:
            raise IndexError('Error: worker object has not been supplied')

        self.worker = worker
        self.peer_port = self.worker.peer_port

        assert self.peer_port, "This service requires peers to exist!"
        assert self.inputs, "Need to provide kwargs when initing service"

        # Extract relevant details from the requests and inputs
        color: str = self.inputs.get('color', 'None')
        neighbors: list = self.inputs.get('neighbors')     # get the neighbors, those it can talk to

        # Populate the peer_port's state-space
        self.peer_port.state_space['color'] = color

        # Connect peer_port to all the peers
        self.peer_port.tie_to_peers()
        time.sleep(self.BIND_WAIT)

        send_to: List[bytes] = self.parse_send_to(send_to=neighbors)

        self.request_from_peers(state='color', send_to=send_to)

        all_colors = [self.peer_port.state_space['color']]
        all_colors += [data['color'] for data in self.peer_port.state_space['other_peer_data'].values()]

        payload = all_colors
        reply = {'reply': payload, 'origin': self.worker_name}

        self.peer_port.stop()
        return reply

    def parse_send_to(self, send_to) -> List[bytes]:
        return [peer_name for peer_name in self.peer_port.peers if peer_name.split(b'.')[0] in send_to]


