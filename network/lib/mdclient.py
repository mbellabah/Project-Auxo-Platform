import sys
from mdcliapi import MajorDomoClient


def main():
    user_args = sys.argv
    verbose = '-v' in user_args

    # Args: -v *verbose* host port client_name
    host = "localhost"      # ip address of the broker
    port = 5555
    if len(user_args) > 2:
        host = user_args[2]
        port = user_args[3]
        client_name = user_args[4]

    client = MajorDomoClient(f"tcp://{host}:{port}", verbose, client_name=client_name)
    requests = 10
    for i in range(requests):
        request = "Hello world"
        try:
            client.send("echo", request)
        except KeyboardInterrupt:
            print("send interrupted, aborting")
            return

    count = 0
    while count < requests:
        try:
            reply = client.recv()
        except KeyboardInterrupt:
            break
        else:
            # also break on failure to reply:
            if reply is None:
                break
        count += 1
    print("%i requests/replies processed" % count)


if __name__ == '__main__':
    main()
