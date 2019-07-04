"""MDP Protocol Definitions"""

C_CLIENT = b"MDPC01"

W_WORKER = b"MDPW01"


# MDP/Server commands, as bytes
W_READY = b"\001"
W_REQUEST = b"\002"
W_REPLY = b"\003"
W_HEARTBEAT = b"\004"
W_DISCONNECT = b"\005"

commands = [None, "READY", "REQUEST", "REPLY", "HEARTBEAT", "DISCONNECT"]
