import time
import json

from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.services.service_exe import ServiceExeBase


class ServiceExeEcho(ServiceExeBase):
    """
    Simple echo service, doesn't need to coordinate with peers!
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.service_name = 'echo'

    # Override process
    def process(self, *args, **kwargs) -> dict:
        try:
            request: dict = json.loads(args[0])
            self.worker: MajorDomoWorker = args[1]
        except IndexError:
            raise IndexError('Error: worker object has not been supplied:')

        # Do some work
        time.sleep(2)
        payload = request['payload']

        reply = {'payload': payload, 'origin': self.worker_name}
        return reply
