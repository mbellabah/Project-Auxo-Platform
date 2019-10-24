from auxo_olympus.lib.utils.zhelpers import jsonify_nparray, restore_nparray
from auxo_olympus.lib.entities.mdcliapi import MajorDomoClient

import time
import json
import argparse


# Note how the client has no access to the service class definitions in MDP
# TODO: Break down the requests into request classes

class Client(object):
    TIMEOUT: int = 10       # seconds

    def __init__(self, client_name, broker, port, verbose, service):
        self.client_name = client_name
        self.broker = broker        # broker's ip addr
        self.port = port        # broker's port
        self.verbose = verbose
        self.desired_service = service

        self.client = MajorDomoClient(f"tcp://{self.broker}:{self.port}", verbose, client_name=self.client_name)

    def run(self, service: str, **kwargs):
        num_requests: int = kwargs.get('num_requests', 1)

        for i in range(num_requests):
            request = json.dumps(kwargs)    # FIXME: May have to remove some extra client information here!
            try:
                self.client.send(service, request)
            except KeyboardInterrupt:
                print("Send interrupted, aborting")
                return

        count = 0
        actual_reply = 'null'
        timeout = time.time() + self.TIMEOUT    # TIMEOUT second timeout
        while time.time() < timeout:        # count < expected_num_replies:
            try:
                reply = self.client.recv()
                # Frame 0: actual_reply
                # Frame 1: worker_origin
                if reply:
                    actual_reply = json.loads(reply[0])
                    if actual_reply:
                        break

            except KeyboardInterrupt:
                break
            else:
                # also break on failure to reply:
                if reply is None:
                    break
            count += 1

        print(f"{count} requests/replies processed")
        print(f"most recent reply: {actual_reply}")

        # TEST NUMPY ARRAY
        print("#"*15)
        if 'test_np_array' in actual_reply:
            print("RECEIVED THIS NP ARRAY")
            print(restore_nparray(actual_reply['test_np_array']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-broker_ip', default='localhost', type=str, help='ip address of the broker')
    parser.add_argument('-port', default=5555, type=int, help='port to listen through')
    parser.add_argument('-service', default='echo', type=str, help='client service request')
    parser.add_argument('client_name', type=str, help='client\'s name')
    parser.add_argument("-v", default=False, type=bool, help=' verbose output')
    parser.add_argument("-d", '--inputs', type=json.loads)

    args = parser.parse_args()

    verbose = args.v
    broker = args.broker_ip
    port = args.port
    client_name = args.client_name
    service = args.service
    inputs: dict = args.inputs

    client = Client(client_name, broker, port, verbose, service)
    time.sleep(2)       # hardcoded delay
    client.run(service, **inputs)


if __name__ == '__main__':
    main()
