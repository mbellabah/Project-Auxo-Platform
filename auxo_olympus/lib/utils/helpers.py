class ServiceExit(Exception):
    """ Custom exception to catch the broker using unix signals """
    pass


def service_shutdown(signum, frame):
    print(f"Caught signal {signum} -- you pressed Ctrl-c")
    raise ServiceExit
