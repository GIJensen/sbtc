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

    return True

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
        elif i in ['relayfee', 'balance', 'paytxfee', 'fee', 'modifiedfee', 'immature_balance', 'unconfirmed_balance']:
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
    elif result_type == str and '\n' in result:
        print(result)
    else:
        print(repr(result))

def getinfo(display=False):
    return rpccommand('getinfo', [], display)

def getpeerinfo(display=False):
    return rpccommand('getpeerinfo', [], display)

def getblockchaininfo(verbose=True, display=False):
    result = rpccommand('getblockchaininfo')
    if display:
        if verbose:
            displayResult(result)
        else:
            displayResult(result, ['softforks'])
    return result

def getrawtransaction(txid, verbose=False, display=False):
    return rpccommand('getrawtransaction', [txid, int(toBool(verbose))], display)

def signrawtransaction(hexstring, prevtxs=None, privatekeys=None, sighashtype='ALL', display=False):
    return rpccommand('signrawtransaction', [hexstring, json.loads(prevtxs), json.loads(privatekeys), sighashtype], display)

def getblockcount(display=False):
    return rpccommand('getblockcount', [], display)

def getbestblockhash(display=False):
    return rpccommand('getbestblockhash', [], display)

def getblock(blkhash, verbose=True, display=False):
    return rpccommand('getblock', [blkhash, toBool(verbose)], display)

def getblockheader(blkhash, verbose=True, display=False):
    return rpccommand('getblockheader', [blkhash, toBool(verbose)], display)

def getdifficulty(display=False):
    return rpccommand('getdifficulty', [], display)

def getmempoolinfo(display=False):
    return rpccommand('getmempoolinfo', [], display)

def getrawmempool(verbose=False, display=False):
    return rpccommand('getrawmempool', [toBool(verbose)], display)

def gettxout(txid, n, inclmempl=True, display=False):
    return rpccommand('gettxout', [txid, int(n), toBool(inclmempl)], display)

def ping(display=False):
    return rpccommand('ping')

def gettxoutproof(txids, blkhash=None, display=False):
    return rpccommand('gettxoutproof', [json.loads(txids), blkhash]) if blkhash else rpccommand('gettxoutproof', [json.loads(txids)], display)

def getchaintips(display=False):
    return rpccommand('getchaintips', [], display)

def getblockhash(blkid, display=False):
    return rpccommand('getblockhash', [int(blkid)], display)

def createrawtransaction(txs, outs, display=False):
    return rpccommand('createrawtransaction', [json.loads(txs), json.loads(outs)], display)

def gettxoutsetinfo(display=False):
    return rpccommand('gettxoutsetinfo', [], display)

def verifychain(chklvl=3, numblks=388, display=False):
    return rpccommand('verifychain', [int(chklvl), int(numblks)], display)

def verifytxoutproof(proof, display=False):
    return rpccommand('verifytxoutproof', [proof], display)

def stop(display=False):
    return rpccommand('stop', [], display)

def generate(numblks, display=False):
    return rpccommand('generate', [int(numblks)], display)

def getgenerate(display=False):
    return rpccommand('getgenerate', [], display)

def setgenerate(gen, genproclimit=None):
    if genproclimit:
        return rpccommand('setgenerate', [toBool(gen), int(genproclimit)], display)
    else:
        return rpccommand('setgenerate', [toBool(gen)], display)

def getblocktemplate(jsonReqObj=None, display=False):
    if jsonReqObj:
        return rpccommand('getblocktemplate', [json.loads(jsonReqObj)], display)
    else:
        return rpccommand('getblocktemplate', [], display)

def getmininginfo(display=False):
    return rpccommand('getmininginfo', [], display)

def getnetworkhashps(blocks=120, height=-1, display=False):
    return rpccommand('getnetworkhashps', [int(blocks), int(height)], display)

def prioritisetransaction(txid, priority_d, fee_d, display=False):
    return rpccommand('prioritisetransaction', [txid, int(priority_d), int(fee_d)], display)

def submitblock(data, jsonParamsObj=None, display=False):
    if jsonParamsObj:
        return rpccommand('submitblock', [data, json.loads(jsonParamsObj)], display)
    else:
        return rpccommand('submitblock', [data], display)
    
def addnode(node, cmd, display=False):
    return rpccommand('addnode', [node, cmd], display)

def clearbanned(display=False):
    return rpccommand('clearbanned', [], display)

def disconnectnode(node, display=False):
    return rpccommand('disconnectnode', [node], display)

def getaddednodeinfo(dns, node=None, display=False):
    if node:
        return rpccommand('getaddednodeinfo', [toBool(dns), node], display)
    else:
        return rpccommand('getaddednodeinfo', [toBool(dns)], display)

def getconnectioncount(display=False):
    return rpccommand('getconnectioncount', [], display)

def getnettotals(display=False):
    return rpccommand('getnettotals', [], display)

def getnetworkinfo(display=False):
    return rpccommand('getnetworkinfo', [], display)

def listbanned(display=False):
    return rpccommand('listbanned', [], display)

def setban(ip, cmd, bantime=0, absolute=False, display=False):
    return rpccommand('setban', [ip, cmd, int(bantime), toBool(absolute)], display)

def decoderawtransaction(hexstr, display=False):
    return rpccommand('decoderawtransaction', [hexstr], display)

def decodescript(hexraw, display=False):
    return rpccommand('decodescript', [hexraw], display)

def fundrawtransaction(hexstr, inclwatch, display=False):
    return rpccommand('fundrawtransaction', [hexstr, toBool(inclwatch)], display)

def sendrawtransaction(hexstr, allowhighfees=False, display=False):
    return rpccommand('sendrawtransaction', [hexstr, toBool(allowhighfees)], display)

def createmultisig(nreq, keys, display=False):
    return rpccommand('createmultisig', [int(nreq), json.loads(keys)], display)

def estimatefee(nblks, display=False):
    return rpccommand('estimatefee', [int(nblks)], display)

def estimatepriority(nblks, display=False):
    return rpccommand('estimatepriority', [int(nblks)], display)

def estimatesmartfee(nblks, display=False):
    return rpccommand('estimatesmartfee', [int(nblks)], display)

def estimatesmartpriority(nblks, display=False):
    return rpccommand('estimatesmartpriority', [int(nblks)], display)

def validateaddress(addr, display=False):
    return rpccommand('validateaddress', [addr], display)

def abandontransaction(txid, display=False):
    return rpccommand('abandontransaction', [txid], display)

def addmultisigaddress(nreq, keys, account='', display=False):
    return rpccommand('abdmultisigaddress', [int(nreq), json.loads(keys), account], display)

def backupwallet(dest, display=False):
    return rpccommand('backupwallet', [dest], display)

def encryptwallet(passphr, display=False):
    return rpccommand('encryptwallet', [passphr], display)

def dumpprivkey(addr, display=False):
    return rpccommand('dumpprivkey', [addr], display)

def dumpwallet(filen, display=False):
    return rpccommand('dumpwallet', [filen], display)

def getaccount(addr, display=False):
    return rpccommand('getaccount', [addr], display)

def getaccountaddress(acc, display=False):
    return rpccommand('getaccountaddress', [acc], display)

def getaddressesbyaccount(acc, display=False):
    return rpccommand('getaddressesbyaccount', [acc], display)

def getbalance(acc='*', minconf=1, inclwatch=False, display=False):
    return rpccommand('getbalance', [acc, int(minconf), toBool(inclwatch)], display)

def getnewaddress(acc='', display=False):
    return rpccommand('getnewaddress', [acc], display)

def getrawchangeaddress(display=False):
    return rpccommand('getrawchangeaddress', [], display)

def getreceivedbyaccount(acc, minconf=1, display=False):
    return rpccommand('getreceivedbyaccount', [acc, int(minconf)], display)

def getreceivedbyaddress(addr, minconf=1, display=False):
    return rpccommand('getreceivedbyaddress', [addr, int(minconf)], display)

def gettransaction(txid, inclwatch=False, display=False):
    return rpccommand('gettransaction', [txid, toBool(inclwatch)], display)

def getunconfirmedbalance(display=False):
    return rpccommand('getunconfirmedbalance', [], display)

def getwalletinfo(display=False):
    return rpccommand('getwalletinfo', [], display)

def importaddress(addr, label='', rescan=True, p2sh=False, display=False):
    return rpccommand('importaddress', [addr, label, toBool(rescan), toBool(p2sh)], display)

def importprivkey(privkey, label='', rescan=True, display=False):
    return rpccommand('importprivkey', [privkey, label, toBool(rescan)], display)

def importpubkey(pubkey, label='', rescan=True, display=False):
    return rpccommand('importpubkey', [pubkey, label, toBool(rescan)], display)

def importwallet(filen, display=False):
    return rpccommand('importwallet', [filen], display)

def keypoolrefill(size=100, display=False):
    return rpccommand('keypoolrefill', [int(size)], display)

def listaccounts(minconf=1, inclwatch=False, display=False):
    return rpccommand('listaccounts', [int(minconf), toBool(inclwatch)], display)

def listaddressgroupings(display=False):
    return rpccommand('listaddressgroupings', [], display)

def listlockunspent(display=False):
    return rpccommand('listlockunspent', [], display)

def listreceivedbyaccount(minconf=1, inclempty=False, inclwatch=False, display=False):
    return rpccommand('listreceivedbyaccount', [int(minconf), toBool(inclempty), toBool(inclwatch)], display)

def listreceivedbyaddress(minconf=1, inclempty=False, inclwatch=False, display=False):
    return rpccommand('listreceivedbyaddress', [int(minconf), toBool(inclempty), toBool(inclwatch)], display)

def listsinceblock(blkhash=None, minconf=1, inclwatch=False, display=False):
    if blkhash:
        return rpccommand('listsinceblock', [blkhash, int(minconf), toBool(inclwatch)], display)
    else:
        return rpccommand('listsinceblock', [], display)

def listtransactions(acc='*', count=10, skip=0, inclwatch=False, display=False):
    return rpccommand('listtransactions', [acc, int(count), int(skip), toBool(inclwatch)], display)

def listunspent(minconf=1, maxconf=999999999, addrs=None, display=False):
    if addrs:
        return rpccommand('listunspent', [int(minconf), int(maxconf), json.loads(addrs)], display)
    else:
        return rpccommand('listunspent', [int(minconf), int(maxconf)], display)

def lockunspent(unlock, txns, display=False):
    return rpccommand('lockunspent', [toBool(unlock), json.loads(txns)], display)

def move(fromacc, toacc, amnt, minconf=1, comment='', display=False):
    return rpccommand('move', [fromacc, toacc, float(amnt), int(minconf), comment], display)

def sendfrom(acc, addr, amnt, minconf=1, comment='', commentto='', display=False):
    return rpccommand('sendfrom', [acc, addr, float(amnt), int(minconf), comment, commentto], display)

def sendmany(acc, amnts, minconf=1, comment='', commenttos=None, display=False):
    if commenttos:
        return rpccommand('sendmany', [acc, json.loads(amnts), int(minconf), comment, json.loads(commenttos)], display)
    else:
        return rpccommand('sendmany', [acc, json.loads(amnts), int(minconf), comment], display)

def sendtoaddress(addr, amnt, comment='', commentto='', subfeefromamnt=False, display=False):
    return rpccommand('sendtoaddress', [addr, float(amnt), comment, commentto, toBool(subfeefromamnt)], display)

def setaccount(addr, acc, display=False):
    return rpccommand('setaccount', [addr, acc], display)

def settxfee(amnt, display=False):
    return rpccommand('settxfee', [float(amnt)], display)

def signmessage(addr, msg, display=False):
    return rpccommand('signmessage', [addr, msg], display)

def verifymessage(addr, sig, msg, display=False):
    return rpccommand('verifymessage', [addr, sig, msg], display)

def rpchelp(func=None, display=False):
    if func:
        result = rpccommand('help', [func], display)
    else:
        result = rpccommand('help')
        if display: getRPCHelp()

    return result

# TODO Find a clean way to integrate extended help
def getRPCHelp(display=True):
    result = rpccommand('help')
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
    'signrawtransaction':[[1, 2, 3, 4], signrawtransaction],
    'decoderawtransaction':[[1], decoderawtransaction],
    'decodescript':[[1], decodescript],
    'fundrawtransaction':[[2], fundrawtransaction],
    'sendrawtransaction':[[1, 2], sendrawtransaction],
    'createmultisig':[[2], createmultisig],
    'estimatefee':[[1], estimatefee],
    'estimatepriority':[[1], estimatepriority],
    'estimatesmartfee':[[1], estimatesmartfee],
    'estimatesmartpriority':[[1], estimatesmartpriority],
    'validateaddress':[[1], validateaddress],
    'verifymessage':[[3], verifymessage],
    'abandontransaction':[[1], abandontransaction],
    'addmultisigaddress':[[2, 3], addmultisigaddress],
    'backupwallet':[[1], backupwallet],
    'dumpprivkey':[[1], dumpprivkey],
    'dumpwallet':[[1], dumpwallet],
    'encryptwallet':[[1], encryptwallet],
    'getaccount':[[1], getaccount],
    'getaccountaddress':[[1], getaccountaddress],
    'getaddressesbyaccount':[[1], getaddressesbyaccount],
    'getbalance':[[0, 1, 2, 3], getbalance],
    'getnewaddress':[[0, 1], getnewaddress],
    'getrawchangeaddress':[[0], getrawchangeaddress],
    'getreceivedbyaccount':[[1, 2], getreceivedbyaccount],
    'getreceivedbyaddress':[[1, 2], getreceivedbyaddress],
    'gettransaction':[[1, 2], gettransaction],
    'getunconfirmedbalance':[[0], getunconfirmedbalance],
    'getwalletinfo':[[0], getwalletinfo],
    'importaddress':[[1, 2, 3, 4], importaddress],
    'importprivkey':[[1, 2, 3], importprivkey],
    'importpubkey':[[1, 2, 3], importpubkey],
    'importwallet':[[1], importwallet],
    'keypoolrefill':[[0, 1], keypoolrefill],
    'listaccounts':[[0, 1, 2], listaccounts],
    'listaddressgroupings':[[0], listaddressgroupings],
    'listlockunspent':[[0], listlockunspent],
    'listreceivedbyaccount':[[0, 1, 2, 3], listreceivedbyaccount],
    'listreceivedbyaddress':[[0, 1, 2, 3], listreceivedbyaddress],
    'listsinceblock':[[0, 1, 2, 3], listsinceblock],
    'listtransactions':[[0, 1, 2, 3, 4], listtransactions],
    'listunspent':[[0, 1, 2, 3], listunspent],
    'lockunspent':[[2], lockunspent],
    'move':[[3, 4, 5], move],
    'sendfrom':[[3, 4, 5, 6], sendfrom],
    'sendmany':[[2, 3, 4, 5], sendmany],
    'sendtoaddress':[[2, 3, 4, 5], sendtoaddress],
    'setaccount':[[2], setaccount],
    'settxfee':[[1], settxfee],
    'signmessage':[[2], signmessage],
    'help':[[0, 1], rpchelp]
}

## ["command", [no. of args (-1, no limit)], function, optional helptext]
# FIXME Deprecate "commands"
config.commands.update(rpc_commands)
