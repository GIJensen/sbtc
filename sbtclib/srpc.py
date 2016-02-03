#!/usr/bin/python3
#
# Copyright (c) 2016, gijensen
#
from __future__ import print_function
import requests, json, os, psutil
from . import config

# NOTE No idea if this works on OSs that aren't Linux
def bitcoindIsSafe():
    if config.RPCPORT in config.TRUSTED_UIDS:
        expected_uid = config.TRUSTED_UIDS[config.RPCPORT]
    else:
        expected_uid = None

    for conn in psutil.net_connections('tcp4'):
        if conn.laddr[1] == config.RPCPORT:
            uids = psutil.Process(conn.pid).uids()
            if len(set([uids.real, uids.effective, uids.saved])) == 1:
                if not expected_uid:
                    print('Trusting unknown port:uid, %d:%d...' % (config.RPCPORT, uids.real))
                    config.TRUSTED_UIDS[config.RPCPORT] = uids.real
                    open(config.DATADIR + '/sbtc.uids', 'a').write('%d:%d\n' % (config.RPCPORT, uids.real))
                    expected_uid = uids.real
                return uids.real == expected_uid

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

def displayDict(data, exclude=[], depth=0):
    keys = list(data.keys())
    keys.sort()
    for i in keys:
        if i in exclude: continue
        data_type = type(data[i])
        spacing = '    '*depth
        if data_type == dict:
            print('%s%s: {' % (spacing, i))
            displayDict(data[i], exclude, depth+1)
            print('%s}' % spacing)
        elif data_type == list:
            print('%s%s: [' % (spacing, i))
            displayList(data[i], exclude, depth+1)
            print('%s]' % spacing)
        elif i in ['relayfee', 'balance', 'paytxfee', 'fee', 'modifiedfee']:
            print('%s%s: %0.8f' % (spacing, i, data[i]))
        else:
            print('%s%s: %s' % (spacing, i, repr(data[i])))

def displayList(data, exclude=[], depth=0):
    for i in data:
        data_type = type(i)
        spacing = '    '*depth
        if data_type == dict:
            print('%s{' % spacing)
            displayDict(i, exclude, depth+1)
            print('%s}' % spacing)
        elif data_type == list:
            print('%s[' % spacing)
            displayList(i, exclude, depth+1)
            print('%s]' % spacing)
        else:
            print('%s%s' % (spacing, repr(i)))

def displayResult(result, exclude=[]):
    result_type = type(result)
    if result_type == dict:
        displayDict(result, exclude)
    elif result_type == list:
        displayList(result, exclude)
    else:
        print(repr(result))

def getinfo(display=False):
    result = rpccommand('getinfo')
    if display: displayResult(result)
    return result

def getpeerinfo(display=False):
    result = rpccommand('getpeerinfo')
    if display: displayResult(result)
    return result

def getblockchaininfo(verbose=True, display=False):
    result = rpccommand('getblockchaininfo')
    if display:
        if verbose:
            displayResult(result)
        else:
            displayResult(result, ['softforks'])
    return result

def getrawtransaction(txid, verbose=False, display=False):
    result = rpccommand('getrawtransaction', [txid, int(toBool(verbose))])
    if display: displayResult(result)
    return result

def signrawtransaction(hexstring, prevtxs=None, privatekeys=None, sighashtype="ALL", display=False):
    result = rpccommand('signrawtransaction', [hexstring, json.loads(prevtxs), json.loads(privatekeys), sighashtype])
    if display: displayResult(result)
    return result

def getblockcount(display=False):
    result = rpccommand('getblockcount')
    if display: print(result)
    return result

def getbestblockhash(display=False):
    result = rpccommand('getbestblockhash')
    if display: print(result)
    return result

def getblock(blkhash, verbose=True, display=False):
    result = rpccommand('getblock', [blkhash, toBool(verbose)])
    if display: displayResult(result)
    return result

def getblockheader(blkhash, verbose=True, display=False):
    result = rpccommand('getblockheader', [blkhash, toBool(verbose)])
    if display: displayResult(result)
    return result

def getdifficulty(display=False):
    result = rpccommand('getdifficulty')
    if display: print(result)
    return result

def getmempoolinfo(display=False):
    result = rpccommand('getmempoolinfo')
    if display: displayResult(result)
    return result

def getrawmempool(verbose=False, display=False):
    result = rpccommand('getrawmempool', [toBool(verbose)])
    if display: displayResult(result)
    return result

def gettxout(txid, n, inclmempl=True, display=False):
    result = rpccommand('gettxout', [txid, int(n), toBool(inclmempl)])
    if display: displayResult(result)
    return result

def ping(display=False):
    return rpccommand('ping')

def gettxoutproof(txids, blkhash=None, display=False):
    result = rpccommand('gettxoutproof', [json.loads(txids), blkhash]) if blkhash else rpccommand('gettxoutproof', [json.loads(txids)])
    if display: displayResult(result)
    return result

def getchaintips(display=False):
    result = rpccommand('getchaintips')
    if display: displayResult(result)
    return result

def getblockhash(blkid, display=False):
    result = rpccommand('getblockhash', [int(blkid)])
    if display: displayResult(result)
    return result

def createrawtransaction(txs, outs, display=False):
    result = rpccommand('createrawtransaction', [json.loads(txs), json.loads(outs)])
    if display: displayResult(result)
    return result

def rpchelp(func=None, display=False):
    if func:
        result = rpccommand('help', [func])
        if display: displayResult(result)
    else:
        result = rpccommand('help')
        if display: getRPCHelp()

    return result

# TODO Find a clean way to integrate extended help
def getRPCHelp(display=True):
    result = rpccommand('help', [])
    for i in result.split('\n'):
        if len(i) > 0 and i[0] != '=':
            if i.split()[0] in rpc_commands:
                print(i)
            else:
                print('*' + i)
        else:
            print(i)
    print('* = Unsupported')

rpc_commands = {
    'getinfo':[[0], getinfo],
    'getblockchaininfo':[[0, 1], lambda x=False, display=False:getblockchaininfo(toBool(x), display),
                 '[verbose=False]'],
    'getblockcount':[[0], getblockcount],
    'getbestblockhash':[[0], getbestblockhash],
    'getblock':[[1, 2], getblock],
    'getblockheader':[[1, 2], getblockheader],
    'getdifficulty':[[0], getdifficulty],
    'getmempoolinfo':[[0], getmempoolinfo],
    'getrawmempool':[[0, 1], getrawmempool],
    'gettxout':[[2, 3], gettxout],
    'ping':[[0], ping],
    'gettxoutproof':[[1, 2], gettxoutproof],
    'getchaintips':[[0], getchaintips],
    'getblockhash':[[1], getblockhash],
    'getpeerinfo':[[0], getpeerinfo],
    'getrawtransaction':[[1, 2], getrawtransaction],
    'createrawtransaction':[[2], createrawtransaction],
    'help':[[0, 1], rpchelp]
}

## ["command", [no. of args (-1, no limit)], function, optional helptext]
# FIXME Deprecate "commands"
config.commands.update(rpc_commands)

