import sys
from mdwrkapi import MajorDomoWorker

# TODO: Interconnect the workers, perhaps use pub and sub -- better to receive the endpoints
#       from the broker, and use that to connect with various workers on the same service!


def main():
    user_args = sys.argv
    verbose = '-v' in user_args

    # Args: -v *verbose* host port worker_name
    host = "localhost"      # Ip address of the broker
    port = 5555
    if len(user_args) > 2:
        host = user_args[2]
        port = user_args[3]
        worker_name = user_args[4]

    worker = MajorDomoWorker(f"tcp://{host}:{port}", "echo", verbose, worker_name)
    reply = None
    while True:
        request = worker.recv(reply)
        if request is None:
            break
        reply = request     # simple echo


if __name__ == '__main__':
    main()
