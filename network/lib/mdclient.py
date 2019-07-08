import sys
from mdcliapi import MajorDomoClient


class Client(object):
    def __init__(self, client_name, broker, port, verbose):
        self.client_name = client_name
        self.broker = broker        # broker's ip addr
        self.port = port        # broker's port
        self.verbose = verbose

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
    user_args = sys.argv
    verbose = '-v' in user_args

    # Args: -v *verbose* host port client_name
    broker = "localhost"      # ip address of the broker
    port = 5555
    if len(user_args) > 2:
        broker = user_args[2]
        port = user_args[3]
        client_name = user_args[4]

    client = Client(client_name, broker, port, verbose)
    client.run(service="echo")


if __name__ == '__main__':
    main()
