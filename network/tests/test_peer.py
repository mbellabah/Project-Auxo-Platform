import time
from lib.mdperapi import Peer


def test_local_local():
    """
    Test peer connectivity solely on localhost
    :return:
    """
    _peers0 = {'peer1': 'ipc://routing.ipc'}
    _peers1 = {'peer0': 'ipc://routing.ipc'}

    # localhost
    peer0 = Peer(endpoint='ipc://routing.ipc', peer_name='peer0', peers=_peers0, verbose=True)

    # localhost
    peer1 = Peer(endpoint='ipc://routing.ipc', peer_name='peer1', peers=_peers1, verbose=True)

    for i in range(10):
        payload: bytes = f'request {i}'.encode('utf8')
        peer1.send(peer_ident=b'peer0', payload=payload)

        time.sleep(0.5)


def test_local_bbb(local_bool: bool = True):
    """
    Test peer connectivity on localhost and a remote bbb
    peer0: localhost
    peer1: bbb-df1f.local
    :param local_bool:
    :return:
    """
    _peers0 = {'peer1': 'tcp://192.168.0.101:5555'}
    _peers1 = {'peer0': 'tcp://192.168.0.104:5555'}

    if local_bool:
        # localhost
        peer0 = Peer(endpoint='tcp://192.168.0.104:5555', peer_name='peer0', peers=_peers0, verbose=True)
    else:
        # Running on BBB-df1f.local
        peer1 = Peer(endpoint='tcp://192.168.0.101:5555', peer_name='peer1', peers=_peers1, verbose=True)

        for i in range(10):
            payload: bytes = f'request {i}'.encode('utf8')
            peer1.send(peer_ident=b'peer0', payload=payload)

            time.sleep(0.5)


def test_bbb_bbb(peer_0_bool: bool = True):
    """
    Test peer connectivity on two independent bbbs
    peer_0: bbb-df1f.local
    peer_1: bbb-1b55.local
    :return:
    """
    _peers0 = {'peer1': 'tcp://192.168.0.100:5555'}
    _peers1 = {'peer0': 'tcp://192.168.0.101:5555'}

    if peer_0_bool:
        # bbb-df1f.local
        peer0 = Peer(endpoint='tcp://192.168.0.101:5555', peer_name='peer0', peers=_peers0, verbose=True)
    else:
        # bbb-1b55.local
        peer1 = Peer(endpoint='tcp://192.168.0.100:5555', peer_name='peer1', peers=_peers1, verbose=True)

        for i in range(10):
            payload: bytes = f'request {i}'.encode('utf8')
            peer1.send(peer_ident=b'peer0', payload=payload)

            time.sleep(0.5)


if __name__ == '__main__':
    # # peer name other_peer_name other_peer_endpoint send
    # args = sys.argv
    #
    #
    # [peer_name, other_peer_name, other_peer_endpoint, send] = args[1:]
    # peers = {other_peer_name: other_peer_endpoint}
    # peer = Peer(peer_name=peer_name, peers=peers)
    #
    # if send:
    #     peer.send(peers['peer0'], peer_ident=b'peer0')

    # test_bbb_bbb(peer_0_bool=True)
    test_local_local()





