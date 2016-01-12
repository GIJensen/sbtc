#!/usr/bin/python3
from __future__ import print_function
import requests, json, time, os, sys, select, psutil

VERSION = 'sbtc v0.2.00'
CREDITS = 'gijensen'

DATADIR = os.environ['HOME']+'/.devbitcoin'

RPCUSER = ''
RPCPASS = ''
RPCPORT = 8332

## If True will ignore the UID of bitcoind. ABSOLUTELY NOT RECOMMENDED.
IGNORE_BITCOIND_UID = False

# TODO Optionally output some positive feedback on success
def loadconfig(datadir=DATADIR):
    global RPCUSER, RPCPASS, RPCPORT
    try:
        f = open(datadir + '/bitcoin.conf', 'r')
        lines = f.readlines()
        f.close()
    except Exception as e:
        print('Error loading config: %s' % e)
        return

    tnSet = False

    for i in lines:
        line = i.strip().split('=', 1)
        if line[0] == 'rpcuser':
            RPCUSER = line[1]
        elif line[0] == 'rpcpassword':
            RPCPASS = line[1]
        elif line[0] == 'rpcport':
            RPCPORT = int(line[1])
        elif line[0] == 'testnet' and RPCPORT in [8332, 18332]:
            tnSet = True
            if bool(line[1]):
                RPCPORT = 18332
            else:
                RPCPORT = 8332

    if not tnSet and RPCPORT == 18332:
        RPCPORT = 8332

# TODO Support testing against a different UID (other than self)
# NOTE No idea if this works on OSs that aren't Linux
def bitcoindIsSafe():
    for conn in psutil.net_connections('tcp4'):
        if conn.laddr[1] == RPCPORT:
            uids = psutil.Process(conn.pid).uids()
            return len(set([os.getuid(), uids.real, uids.effective, uids.saved])) == 1

## Needed for catching RPC errors properly
class RPCError(Exception):
    pass

def rpccommand(cmd, params=[]):
    if not IGNORE_BITCOIND_UID and not bitcoindIsSafe():
        print('!!WARNING!! bitcoind was started by a different UID.')
        return

    url = "http://localhost:%d/" % RPCPORT
    headers = {'content-type': 'application/json'}

    payload = {
        "method": cmd,
        "params": params,
        "jsonrpc": "2.0",
        "id": 0,
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers, auth=(RPCUSER, RPCPASS))
    if response.status_code == 200:
        return response.json()['result']
    else:
        try:
            response_json = response.json()
        except:
            e = 'Error code %d when connecting via RPC.' % response.status_code
            raise RPCError(e, response.status_code)

        raise RPCError(response_json['error']['message'], response.status_code)

## Get input (non-blocking)
def getInput():
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline()
        if line:
            return line.strip()
        else:
            print('eof on stdin')
            exit(0)
    return None

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

## progress is a float between 0 and 100
def printverificationprogress(progress):
    sys.stdout.write('\r[%-50s] %5.2f%%' % ('x'*int(progress/2), progress))
    sys.stdout.flush()

def watchverificationprogress():
    progress = 0
    while progress < 100 and not getInput():
        result = rpccommand('getblockchaininfo')
        progress = round(float(result['verificationprogress']) * 100, 2)
        printverificationprogress(progress)
        time.sleep(0.5)
    print()

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

def getExtHelp():
    print('Extended functions provided by sbtc:')
    for i in ext_commands:
        if len(ext_commands[i]) == 3:
            print(' %s %s' % (i, ext_commands[i][2]))
        elif ext_commands[i][0][0] == 0 and len(ext_commands[i][0]) == 1:
            print( ' ' + i)
        else:
            print(' %s (%s args)' % (i, ext_commands[i][0]))

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

# TODO Test helptext field for commands
sbtc_commands = {
    'loadconfig':[[0, 1], loadconfig],
    'exthelp':[[0], getExtHelp],
    'rpchelp':[[0], getRPCHelp]
}

ext_commands = {
    'watchprogress':[[0], watchverificationprogress],
    'rpcraw':[[-1], lambda x:print(rpccommand(x[0], x[1:]))]
}

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
commands = sbtc_commands.copy()
commands.update(ext_commands)
commands.update(rpc_commands)

aliases = {
        'getbcinfo':'getblockchaininfo',
        'getrawtx':'getrawtransaction',
        'createrawtx':'createrawtransaction',
        'count':'getblockcount',
        'blockcount':'getblockcount'
}

# FIXME commands=commands may be confusing
# FIXME Change "commands" to "COMMANDS" until deprecated?
def generateCmdHelp(commands=commands):
    cmdHelp = 'Commands: exit'
    for i in commands:
        if commands[i][0][0] == 0 and len(commands[i][0]) == 1:
            cmdHelp += ', ' + i
        else:
            cmdHelp += ', %s (%s args)' % (i, commands[i][0])

    return cmdHelp

def processCmd(cmd, commands=commands):
    cmd[0] = cmd[0].lower()

    if cmd[0] in aliases:
        cmd[0] = aliases[cmd[0]]

    if cmd[0] in commands:
        args = len(cmd)-1
        if args in commands[cmd[0]][0]: 
            if args == 0:
                commands[cmd[0]][1]()
            else:
                commands[cmd[0]][1](*cmd[1:])
            return True
        elif commands[cmd[0]][0][0] == -1:
            commands[cmd[0]][1](cmd[1:])
            return True
        else:
            print('Error: Expected %s args, recieved %d.' % (commands[cmd[0]][0], args))

    return False

def prompt():
    global input
    cmdHelp = generateCmdHelp(sbtc_commands)
    cmd = ''

    # For Python 2.x compatibility.
    try: input = raw_input
    except NameError: pass
    
    print('%s by %s' % (VERSION, CREDITS))

    while cmd != 'exit':
        # TODO Handle quotes and apostrophes  enclosures as single arguments.
        #      (ex: "hello world" should be 1 arg)
        cmd = cmd.split()

        # FIXME Handle Exceptions properly (Catch TypeError at least)
        if len(cmd) > 0:
            try:
                if not processCmd(cmd):
                    print(cmdHelp)
            except RPCError as rpce:
                msg, code = rpce.args
                print('RPCError (HTTP %d): %s' % (code, msg))
            except Exception as e:
                print('Error running command: %s' % e)
        else:
            print(cmdHelp)

        cmd = input('> ')

def main():
    loadconfig()
    if len(sys.argv) == 1:
        prompt()
    else:
        processCmd(sys.argv[1:])

if __name__ == "__main__":
    main()
