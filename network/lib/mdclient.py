import sys
from mdcliapi import MajorDomoClient

import time
import json
import argparse


class Client(object):
    def __init__(self, client_name, broker, port, verbose, service):
        self.client_name = client_name
        self.broker = broker        # broker's ip addr
        self.port = port        # broker's port
        self.verbose = verbose
        self.desired_service = service

        self.client = MajorDomoClient(f"tcp://{self.broker}:{self.port}", verbose, client_name=self.client_name)

    def run(self, service: str = "echo"):
        num_requests: int = 2
        for i in range(num_requests):
            request = "Hello World: " + str(i)
            try:
                self.client.send(service, request)
            except KeyboardInterrupt:
                print("Send interrupted, aborting")
                return

        count = 0
        actual_reply = 'null'
        while count < num_requests:
            try:
                reply = self.client.recv()
                # Frame 0: actual_reply
                # Frame 1: worker_origin
                actual_reply = json.loads(reply[0])
            except KeyboardInterrupt:
                break
            else:
                # also break on failure to reply:
                if reply is None:
                    break
            count += 1

        print(f"{count} requests/replies processed")
        print(f"most recent reply: {actual_reply}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-broker_ip', default='localhost', type=str, help='ip address of the broker')
    parser.add_argument('-port', default=5555, type=int, help='port to listen through')
    parser.add_argument('-service', default='echo', type=str, help='client service request')
    parser.add_argument('client_name', type=str, help='client\'s name')
    parser.add_argument("-v", default=False, type=bool, help=' verbose output')

    args = parser.parse_args()

    verbose = args.v
    broker = args.broker_ip
    port = args.port
    client_name = args.client_name
    service = args.service

    client = Client(client_name, broker, port, verbose, service)
    time.sleep(2)       # hardcoded delay
    client.run(service)


if __name__ == '__main__':
    main()
