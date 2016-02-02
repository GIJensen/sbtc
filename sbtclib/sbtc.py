#!/usr/bin/python3
from __future__ import print_function
import time, sys, select
from . import config
from .srpc import *

## For Python 2.x compatibility.
try: range = xrange
except NameError: pass

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

def getExtHelp():
    print('Extended functions provided by sbtc:')
    for i in ext_commands:
        if len (ext_commands[i]) == 3:
            print(' %s %s' % (i, ext_commands[i][2]))
        elif ext_commands[i][0][0] == 0 and len (ext_commands[i][0]) == 1:
            print(' ' + i)
        else:
            print(' %s (%s args)' % (i, ext_commands[i][0]))

sbtc_commands = {
    'loadconfig':[[0, 1], config.loadconfig],
    'exthelp':[[0], getExtHelp],
    'rpchelp':[[0], getRPCHelp],
    'eval':[[1], lambda expr:print(eval(expr))]
}

ext_commands = {
    'watchprogress':[[0], watchverificationprogress],
    'rpcraw':[[-1], lambda x:print(rpccommand(x[0], x[1:]))]
}

## ["command", [no. of args (-1, no limit)], function, optional helptext]
# FIXME Deprecate "commands"
config.commands.update(sbtc_commands)
config.commands.update(ext_commands)

def generateCmdHelp(commands):
    cmdHelp = 'Commands: exit'
    for i in commands:
        if commands[i][0][0] == 0 and len(commands[i][0]) == 1:
            cmdHelp += ', ' + i
        else:
            cmdHelp += ', %s (%s args)' % (i, commands[i][0])

    return cmdHelp

def processCmd(cmd, commands=None):
    cmd[0] = cmd[0].lower()

    if not commands:
        commands = config.commands

    if cmd[0] in config.ALIASES:
        cmd[0] = config.ALIASES[cmd[0]]

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

def joinQuotes(cmd):
    i = 0
    start = -1
    delim = None
    out = []

    for i in range(len(cmd)):
        if cmd[i][0] in ['\'', '"'] and start == -1:
            delim = cmd[i][0]
            cmd[i] = cmd[i][1:]
            start = i
        if cmd[i][-1] == delim:
            cmd[i] = cmd[i][:-1]
            out.append(' '.join(cmd[start:i+1]))
            start = -1
            delim = None
        elif start == -1:
            out.append(cmd[i])

    if start == -1:
        return out
    else:
        print('Warning: Failed to locate end of quote.')
        return cmd

def prompt():
    global input
    cmdHelp = generateCmdHelp(sbtc_commands)
    cmd = ''

    # For Python 2.x compatibility.
    try: input = raw_input
    except NameError: pass
    
    print('%s by %s' % (config.VERSION, config.CREDITS))

    while cmd != 'exit':
        cmd = joinQuotes(cmd.split())

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
