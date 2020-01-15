"""
Performs the HybridSolar behaviors specified in ...

Expected Client Request 
input: {

}

Provided Agent Input 
input: {
    "asset_type": <str>         whether the agent is a battery or solar 
    "asset_obj_kwargs": <dict>      contains all the necessary args to define the given asset_type 
}
"""

import time 
import json 
import numpy as np 
from typing import List, Dict 

from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.services.service_exe import ServiceExeBase

from auxo_olympus.lib.services.serviceExeHybridSolar.asset_types import Battery, SolarPanel, Offer


class ServiceExeHybridSolar(ServiceExeBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.service_name = 'hybridsolar'
        self.name = f'{self.service_name}-Thread'

        # Getting all the relevant attributes from self.inputs (passed through the command line) 
        assert self.inputs, "Need to provide kwargs (command line) when initing the service"

        self.asset_type: str = self.inputs['asset_type'] 
        if self.asset_type == 'battery':
            self.asset_obj = Battery(self.service_name, **self.inputs['asset_obj_kwargs'])
        elif self.asset_type == 'solarpanel':
            self.asset_obj = SolarPanel(self.service_name, **self.inputs['asset_obj_kwargs'])

    def process(self, *args, **kwargs) -> dict:
        try: 
            request: dict = json.loads(args[0])     # the client's request 
            worker: MajorDomoWorker = args[1]
        except IndexError:
            raise IndexError('Error: worker object has not been supplied')
        
        self.worker = worker 
        self.peer_port = worker.peer_port 

        assert self.peer_port, "This service requires peers to exist!"
        assert self.inputs, "Need to provide kwargs whenn initing service"

        # let agent who holds the service-exe know that it has received a request by signaling on the got_req_q
        self.got_req_q.put('ADD')

        # Populate the peer-port's state-space
        self.peer_port.state_space['my_asset_type'] = self.asset_type
        self.peer_port.state_space['my_asset'] = self.asset_obj

        # Connect peer-port to all the peers -- Note that the worker posseses the PeerPort object
        self.peer_port.tie_to_peers()
        time.sleep(self.BIND_WAIT)

        self.asset_handler(self.asset_type, request=request)

    def asset_handler(self, asset_type, request=None): 
        """
        Different assets 
        """
        if self.asset_type == 'battery':
            self.worker.leader_bool = False 
            pass        # battery kinda waits 

        elif self.asset_type == 'solarpanel': 
            self.worker.leader_bool = True 
            my_reliability = self.peer_port.state_space['my_asset'].reliability

            # if reliability is poor enough that can't expect good revenue 
            if self.peer_port.state_space['my_asset'].expected_revenue(my_reliability) <= self.peer_port.state_space['my_asset'].threshold:
                # Query peers and see who is a battery 
                battery_peers: Dict[bytes, str] = self.find_battery_peers()

                # Solar panel determines some level of capacity that it needs, along with the length of the offer (contract)
                # receieves asks from battery peers, hosted within the solarpanel object 
                # solicitation: Offer = self.peer_port.state_space['my_asset'].construct_solicitation()

                # self.solicit(battery_peers, solicitation)
            
                print('other batteries', battery_peers)

    # MARK: Functions relevant to solarpanel asset 
    def find_battery_peers(self) -> Dict[bytes, str]: 
        """
        Finds the batteries among the peers, only the solarpanel can do this
        returns: dict of peer names and their endpoint for peers that are batteries 
        """
        assert self.asset_type == 'solarpanel', "Only the solar panel can see battery peers in this service"

        send_to: List[bytes] or Dict[bytes, str] = self.peer_port.peers     # send to all peers
        # self.request_from_peers(state='my_asset_type', send_to=send_to)
        self.request_from_peers(state='my_asset_type', send_to=send_to)

        battery_peers: Dict[bytes, str] = {}
        for peer_name, peer_data in self.peer_port.state_space['other_peer_data'].items():
            if peer_data['my_asset_type'] == 'battery':
                peer_name: bytes = peer_name.encode('utf8')
                battery_peers[peer_name] = self.peer_port.peers[peer_name]

        return battery_peers

    def solicit(self, battery_peers, solicitation):
        send_to: Dict[bytes, str] = battery_peers

    
