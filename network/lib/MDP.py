"""MDP Protocol Definitions"""

C_CLIENT = b"MDPC"
W_WORKER = b"MDPW"


# MDP/Server commands, as bytes -- these are the base behaviors
W_READY = b"\001"
W_REQUEST = b"\002"
W_REPLY = b"\003"
W_HEARTBEAT = b"\004"
W_DISCONNECT = b"\005"

commands = [None, "READY", "REQUEST", "REPLY", "HEARTBEAT", "DISCONNECT"]


# Services
S_ECHO = "echo"
S_NONE = "none"