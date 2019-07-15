# encoding: utf-8
"""
Helper module for example applications. Mimics ZeroMQ Guide's zhelpers.h.
"""
from __future__ import print_function

import binascii
import os
import json
import socket
import threading
from random import randint

import zmq
from zmq.utils.monitor import recv_monitor_message


line = lambda: print('-' * 40)


def socket_set_hwm(socket, hwm=-1):
    """libzmq 2/3/4 compatible sethwm"""
    try:
        socket.sndhwm = socket.rcvhwm = hwm
    except AttributeError:
        socket.hwm = hwm


def dump(msg_or_socket):
    """Receives all message parts from socket, printing each frame neatly"""
    if isinstance(msg_or_socket, zmq.Socket):
        # it's a socket, call on current message
        msg = msg_or_socket.recv_multipart()
    else:
        msg = msg_or_socket
    line()
    for part in msg:
        print("[%03d]" % len(part), end=' ')
        is_text = True
        try:
            print(part)
        except UnicodeDecodeError:
            print(r"0x%s" % (binascii.hexlify(part).decode('ascii')))


def set_id(zsocket):
    """Set simple random printable identity on socket"""
    identity = u"%04x-%04x" % (randint(0, 0x10000), randint(0, 0x10000))
    zsocket.setsockopt_string(zmq.IDENTITY, identity)


def zpipe(ctx):
    """build inproc pipe for talking to threads
    mimic pipe used in czmq zthread_fork.
    Returns a pair of PAIRs connected via inproc
    """
    a = ctx.socket(zmq.PAIR)
    b = ctx.socket(zmq.PAIR)
    a.linger = b.linger = 0
    a.hwm = b.hwm = 1
    iface = "inproc://%s" % binascii.hexlify(os.urandom(8))
    a.bind(iface)
    b.connect(iface)
    return a, b


def ensure_is_bytes(msg):
    out = []
    for part in msg:
        if not isinstance(part, bytes):
            try:
                part = part.encode("utf8")
            except AttributeError:
                # Clean the dict (our message structure
                part = strip_of_bytes(part)
                part = json.dumps(part).encode("utf8")
            except Exception as e:
                print(f"Failed to check if bytes: {e}")
        out.append(part)
    return out


def strip_of_bytes(input_dict: dict):
    for key in input_dict.keys():

        if isinstance(key, bytes):
            value = input_dict.pop(key)
            key = key.decode("utf8")        # change to str
            input_dict[key] = value

        if isinstance(input_dict[key], bytes):
            input_dict[key] = input_dict[key].decode("utf8")

        elif isinstance(input_dict[key], list):
            out = []
            for val in input_dict[key]:
                out.append(val.decode("utf8"))
            input_dict[key] = out

    return input_dict


def get_host_name_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        print("Error: Unable to get hostname and ip address:")
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


EVENT_MAP = {}
for name in dir(zmq):
    if name.startswith('EVENT_'):
        value = getattr(zmq, name)
        EVENT_MAP[value] = name


# MARK: Classes
class ZMQMonitor(object):
    evt: dict = None

    def __init__(self, socket):
        self.socket = socket
        self.monitor = self.socket.get_monitor_socket()
        self.t = None

    @staticmethod
    def event_monitor(monitor, event='ALL') -> dict:
        while monitor.poll():
            evt = recv_monitor_message(monitor)
            evt['description'] = EVENT_MAP[evt['event']]
            ZMQMonitor.evt = evt        # set class variable

            if event == 'ALL' and evt['description'] not in ["NONE", "EVENT_CLOSED", "EVENT_CONNECT_DELAYED", "EVENT_CONNECT_RETRIED"]:
                print("Event:", evt)
            if event == evt['event']:
                print("Event:", evt)

            if evt['event'] == zmq.EVENT_MONITOR_STOPPED:
                break
        monitor.close()
        print("\nEvent monitor thread done!")

    def run(self, event):
        line()
        print("Starting socket monitor...")
        line()
        self.t = threading.Thread(target=self.event_monitor, args=(self.monitor, event,))
        self.t.start()

    def stop(self):
        self.socket.disable_monitor()
        self.monitor = None

