import sys
from mdcliapi import MajorDomoClient

import argparse

class Client(object):
    def __init__(self, client_name, broker, port, verbose, service):
        self.client_name = client_name
        self.broker = broker        # broker's ip addr
        self.port = port        # broker's port
        self.verbose = verbose
        self.desired_service = service

        self.client = MajorDomoClient(f"tcp://{self.broker}:{self.port}", verbose, client_name=self.client_name)

    def run(self, service="echo"):
        requests = 10
        for i in range(requests):
            request = "Hello World: " + str(i)
            try:
                self.client.send(service, request)
            except KeyboardInterrupt:
                print("Send interrupted, aborting")
                return

        count = 0
        while count < requests:
            try:
                reply = self.client.recv()
            except KeyboardInterrupt:
                break
            else:
                # also break on failure to reply:
                if reply is None:
                    break
            count += 1

        print(f"{count} requests/replies processed")


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
    client.run(service)


if __name__ == '__main__':
    main()
