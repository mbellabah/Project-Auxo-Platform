import time 
import json 
import numpy as np 

from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.services.service_exe import ServiceExeBase

from auxo_olympus.lib.services.serviceExeHybridSolar.asset_types import Battery, SolarPanel


class ServiceExeHybridSolar(ServiceExeBase):
    """
    asset_type <str> whether this particular agent is a battery or solar-panel 
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.service_name = 'hybridsolar'
        self.name = f'{self.service_name}-Thread'
        
        self.asset_type: str = None 


    def process(self, *args, **kwargs) -> dict:
        try: 
            request: dict = json.loads(args[0])
            worker: MajorDomoWorker = args[1]
        except IndexError:
            raise IndexError('Error: worker object has not been supplied')

        self.worker = worker 

        # Do some work 
        time.sleep(1)
        payload = request['payload']


        