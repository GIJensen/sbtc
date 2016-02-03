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

def rpccommand(cmd, params=[], display=False):
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
        result = response.json()['result']
        if display: displayResult(result)
        return result
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

def gettxoutsetinfo(display=False):
    result = rpccommand('gettxoutsetinfo')
    if display: displayResult(result)
    return result

def verifychain(chklvl=3, numblks=388, display=False):
    result = rpccommand('verifychain', int(chklvl), int(numblks))
    if display: displayResult(result)
    return result

def verifytxoutproof(proof, display=False):
    result = rpccommand('verifytxoutproof', [proof])
    if display: displayResult(result)
    return result

def stop(display=False):
    result = rpccommand('stop')
    if display: displayResult(result)
    return result

def generate(numblks, display=False):
    result = rpccommand('generate', [int(numblks)])
    if display: displayResult(result)
    return result

def getgenerate(display=False):
    result = rpccommand('getgenerate')
    if display: displayResult(result)
    return result

def setgenerate(gen, genproclimit=None):
    if genproclimit:
        result = rpccommand('setgenerate', [int(genproclimit)])
    else:
        result = rpccommand('setgenerate')
    if display: displayResult(result)
    return result

def getblocktemplate(jsonReqObj=None, display=False):
    if jsonReqObj:
        result = rpccommand('getblocktemplate', [json.loads(jsonReqObj)])
    else:
        result = rpccommand('getblocktemplate')
    if display: displayResult(result)
    return result

def getmininginfo(display=False):
    result = rpccommand('getmininginfo')
    if display: displayResult(result)
    return result

def getnetworkhashps(blocks=120, height=-1, display=False):
    result = rpccommand('getnetworkhashps', [int(blocks), int(height)])
    if display: displayResult(result)
    return result

def prioritisetransaction(txid, priority_d, fee_d, display=False):
    result = rpccommand('prioritisetransaction', [txid, int(priority_d), int(fee_d)])
    if display: displayResult(result)
    return result

def submitblock(data, jsonParamsObj=None, display=False):
    if jsonParamsObj:
        result = rpccommand('submitblock', [data, json.loads(jsonParamsObj)])
    else:
        result = rpccommand('submitblock', [data])
    if display: displayResult(result)
    return result
    
def addnode(node, cmd, display=False):
    result = rpccommand('addnode', [node, cmd])
    if display: displayResult(result)
    return result

def clearbanned(display=False):
    result = rpccommand('clearbanned')
    if display: displayResult(result)
    return result

def disconnectnode(node, display=False):
    result = rpccommand('disconnectnode', [node])
    if display: displayResult(result)
    return result

def getaddednodeinfo(dns, node=None, display=False):
    if node:
        result = rpccommand('getaddednodeinfo', [toBool(dns), node])
    else:
        result = rpccommand('getaddednodeinfo', [toBool(dns)])
    if display: displayResult(result)
    return result

def getconnectioncount(display=False):
    result = rpccommand('getconnectioncount')
    if display: displayResult(result)
    return result

def getnettotals(display=False):
    result = rpccommand('getnettotals')
    if display: displayResult(result)
    return result

def getnetworkinfo(display=False):
    result = rpccommand('getnetworkinfo')
    if display: displayResult(result)
    return result

def listbanned(display=False):
    result = rpccommand('listbanned')
    if display: displayResult(result)
    return result

def setban(ip, cmd, bantime=0, absolute=False, display=False):
    result = rpccommand('setban', [ip, cmd, int(bantime), toBool(absolute)])
    if display: displayResult(result)
    return result

def rpchelp(func=None, display=False):
    if func:
        result = rpccommand('help', [func])
        if display: print(result)
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
    'gettxoutsetinfo':[[0], gettxoutsetinfo],
    'verifychain':[[0, 1, 2], verifychain],
    'verifytxoutproof':[[1], verifytxoutproof],
    'stop':[[0], stop],
    'generate':[[1], generate],
    'getgenerate':[[0], getgenerate],
    'setgenerate':[[1, 2], setgenerate],
    'getblocktemplate':[[0, 1], getblocktemplate],
    'getmininginfo':[[0], getmininginfo],
    'getnetworkhashps':[[0, 1, 2], getnetworkhashps],
    'prioritisetransaction':[[3], prioritisetransaction],
    'submitblock':[[1, 2], submitblock],
    'addnode':[[2], addnode],
    'clearbanned':[[0], clearbanned],
    'disconnectnode':[[1], disconnectnode],
    'getaddednodeinfo':[[1, 2], getaddednodeinfo],
    'getconnectioncount':[[0], getconnectioncount],
    'getnettotals':[[0], getnettotals],
    'getnetworkinfo':[[0], getnetworkinfo],
    'listbanned':[[0], listbanned],
    'setban':[[2, 3, 4], setban],
    'help':[[0, 1], rpchelp]
}

## ["command", [no. of args (-1, no limit)], function, optional helptext]
# FIXME Deprecate "commands"
config.commands.update(rpc_commands)

