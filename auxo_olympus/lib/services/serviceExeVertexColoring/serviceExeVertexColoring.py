import time
import json

from auxo_olympus.lib.utils.zhelpers import strip_of_bytes

import auxo_olympus.lib.utils.MDP as MDP
from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.services.service_exe import ServiceExeBase


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

        neighbors: list = request['neighbors']      # get the neighbors, those it can talk to

        # Populate the peer_port's state-space
        self.peer_port.state_space['color'] = None

        # Connect peer_port to all the peers
        self.peer_port.tie_to_peers()
        time.sleep(self.BIND_WAIT)

        # All peers talk to one another
        for peer_identity in self.peer_port.peers:
            request: dict = strip_of_bytes({'origin': self.peer_port.peer_name, 'command': MDP.W_REQUEST, 'request_state': 'color'})
            request: bytes = json.dumps(request).encode('utf8')
            self.peer_port.send(peer_identity, payload=request)

        if not self.leader_bool:
            return {}
        else:
            return {}



