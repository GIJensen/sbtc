#!/usr/bin/python3
from __future__ import print_function
import requests, json, os, psutil
from . import config

# TODO Support testing against a different UID (other than self)
# NOTE No idea if this works on OSs that aren't Linux
def bitcoindIsSafe():
    for conn in psutil.net_connections('tcp4'):
        if conn.laddr[1] == config.RPCPORT:
            uids = psutil.Process(conn.pid).uids()
            return len(set([os.getuid(), uids.real, uids.effective, uids.saved])) == 1

## Needed for catching RPC errors properly
class RPCError(Exception):
    pass

def rpccommand(cmd, params=[]):
    if not config.IGNORE_BITCOIND_UID and not bitcoindIsSafe():
        print('!!WARNING!! bitcoind was started by a different UID.')
        return

    url = "http://localhost:%d/" % config.RPCPORT
    headers = {'content-type': 'application/json'}

    payload = {
        "method": cmd,
        "params": params,
        "jsonrpc": "2.0",
        "id": 0,
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers, auth=(config.RPCUSER, config.RPCPASS))
    if response.status_code == 200:
        return response.json()['result']
    else:
        try:
            response_json = response.json()
        except:
            e = 'Error code %d when connecting via RPC.' % response.status_code
            raise RPCError(e, response.status_code)

        raise RPCError(response_json['error']['message'], response.status_code)

## Convert a string to a boolean
def toBool(v):
    if type(v) == bool:
        return v
    v = v.lower()
    if v in ['yes', 'true', '1', 'y']:
        return True
    elif v in ['no', 'false', '0', 'n']:
        return False
    else:
        raise TypeError('%s cannot be converted to bool' % v)

def rpcgetinfo():
    result = rpccommand('getinfo')
    keys = list(result.keys())
    keys.sort()
    for i in keys:
        if i in ['relayfee', 'balance', 'paytxfee']:
            print('%s: %0.8f' % (i, result[i]))
        else:
            print('%s: %s' % (i, repr(result[i])))

def rpcgetpeerinfo():
    for i in rpccommand('getpeerinfo'):
        keys = list(i.keys())
        keys.sort()
        for ii in keys:
            print('%s: %s' % (ii, repr(i[ii])))
        print('====================')

def rpcgetblockchaininfo(verbose=True):
    result = rpccommand('getblockchaininfo')
    keys = list(result.keys())
    keys.sort()
    for i in keys:
        if i == 'softforks':
            if verbose:
                print('softforks:')
                print('====================')
                for ii in result[i]:
                    for iii in ii:
                        print('\t%s: %s' % (iii, repr(ii[iii])))
                    print('====================')
        else:
            print('%s: %s' % (i, repr(result[i])))

# NOTE This function was rushed for tests
# FIXME Finish function
def rpcgetrawtransaction(txid, verbose=False):
    result = rpccommand('getrawtransaction', [txid, int(toBool(verbose))])

    if verbose:
        keys = list(result.keys())
        keys.sort()

        for i in keys:
            print ('%s: %s' % (i, result[i]))
    else:
        print(result)

def rpcsignrawtransaction(hexstring, prevtxs=None, privatekeys=None, sighashtype="ALL"): 
    result = rpccommand('signrawtransaction', [hexstring, json.loads(prevtxs), json.loads(privatekeys), sighashtype])

    keys = list(result.keys())
    keys.sort()

    for i in keys:
        print ('%s: %s' % (i, result[i]))

    return result

# TODO Perhaps display all RPC commands + prepend a * beside unsupported
def getRPCHelp():
    print('RPC functions supported by sbtc:')
    for i in rpc_commands:
        if len(rpc_commands[i]) == 3:
            print(' %s %s' % (i, rpc_commands[i][2]))
        elif rpc_commands[i][0][0] == 0 and len(rpc_commands[i][0]) == 1:
            print(' ' + i)
        else:
            print(' %s (%s args)' % (i, rpc_commands[i][0]))

rpc_commands = {
    'getinfo':[[0], rpcgetinfo],
    'getblockchaininfo':[[0, 1], lambda x=False:rpcgetblockchaininfo(toBool(x)),
                 '[verbose=False]'],
    'getblockcount':[[0], lambda:print(rpccommand('getblockcount'))],
    'getblockhash':[[1], lambda blkid:print(rpccommand('getblockhash', [int(blkid)]))],
    'getpeerinfo':[[0], rpcgetpeerinfo],
    'getrawtransaction':[[1, 2], rpcgetrawtransaction],
    'createrawtransaction':[[2], lambda txs,outs:print(rpccommand('createrawtransaction', [json.loads(txs), json.loads(outs)]))]
}

## ["command", [no. of args (-1, no limit)], function, optional helptext]
# FIXME Deprecate "commands"
config.commands.update(rpc_commands)

