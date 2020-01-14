import time
import json
import numpy as np

from auxo_olympus.lib.utils.zhelpers import jsonify_nparray

from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.services.service_exe import ServiceExeBase


class ServiceExeEcho(ServiceExeBase):
    """
    Simple echo service, doesn't need to coordinate with peers!

    In the terminal:
    python3 mdagent.py -service=echo -v=True -d='{}' A01
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.service_name = 'echo'
        self.name = f'{self.service_name}-Thread'

    # Override process
    def process(self, *args, **kwargs) -> dict:
        try:
            request: dict = json.loads(args[0])
            worker: MajorDomoWorker = args[1]
        except IndexError:
            raise IndexError('Error: worker object has not been supplied:')

        self.worker = worker

        # Do some work
        time.sleep(2)
        payload = request['payload']

        # TEST NUMPY ARRAY
        test_numpy = jsonify_nparray(np.random.randint(5, size=(5, 1)))

        reply = {'payload': payload, 'test_np_array': test_numpy, 'origin': self.worker_name}
        return reply
