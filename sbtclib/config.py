#
# Copyright (c) 2016, gijensen
#
import os

VERSION = 'sbtc v0.2.00'
CREDITS = 'gijensen'

DATADIR = os.environ['HOME']+'/.bitcoin'

RPCUSER = ''
RPCPASS = ''
RPCPORT = 8332

## If True will ignore the UID of bitcoind. ABSOLUTELY NOT RECOMMENDED.
IGNORE_BITCOIND_UID = False

ALIASES = {
        'getbcinfo':'getblockchaininfo',
        'getrawtx':'getrawtransaction',
        'createrawtx':'createrawtransaction',
        'count':'getblockcount',
        'blockcount':'getblockcount'
}

TRUSTED_UIDS = {}
commands = {}

# TODO Optionally output some positive feedback on success
# NOTE This function may not need a parameter
def loadconfig(datadir=DATADIR):
    global RPCUSER, RPCPASS, RPCPORT, TRUSTED_UIDS
    try:
        f = open(datadir + '/bitcoin.conf', 'r')
        lines = f.readlines()
        f.close()
    except Exception as e:
        print('Error loading config: %s' % e)
        return

    portSet = False

    RPCPORT = 8332

    for i in lines:
        line = i.strip().split('=', 1)
        if line[0] == 'rpcuser':
            RPCUSER = line[1]
        elif line[0] == 'rpcpassword':
            RPCPASS = line[1]
        elif line[0] == 'rpcport':
            portSet = True
            RPCPORT = int(line[1])
        elif line[0] == 'testnet' and not portSet and bool(line[1]):
            RPCPORT = 18332

    try:
        f = open(datadir + '/sbtc.uids', 'r')
    except:
        return
    TRUSTED_UIDS = {}
    uids = f.read().split('\n')
    for i in uids[:-1]:
        port, uid = i.split(':')
        TRUSTED_UIDS[int(port)] = int(uid)
    f.close()
