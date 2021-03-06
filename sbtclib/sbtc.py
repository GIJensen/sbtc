#
# Copyright (c) 2016, gijensen
#
from __future__ import print_function
import time, sys, select
from . import config
from .srpc import *

# TODO gettxfeepaid function
# TODO exec from file function
# TODO prompt command history, arrow key support
# TODO Plugin support, .so, and .py files

## For Python 2.x compatibility.
try: range = xrange
except NameError: pass

## For Python2.x compatibility.
def exec2(cmd):
    exec(cmd)

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

def watchverificationprogress(display=True):
    progress = 0
    while progress < 100 and getInput() == None:
        result = rpccommand('getblockchaininfo')
        progress = round(float(result['verificationprogress']) * 100, 2)
        printverificationprogress(progress)
        time.sleep(0.5)
    print()

def getExtHelp(display=True):
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
    'eval':[[-1], lambda expr, display=True:displayResult(eval(' '.join(expr))) if display else eval(' '.join(expr))],
    'exec':[[-1], lambda expr, display=False:exec2(' '.join(expr))],
    'copyright':[[0], lambda display=True:print('Copyright (c) 2016, gijensen')]
}

ext_commands = {
    'watchprogress':[[0], watchverificationprogress],
    'rpcraw':[[-1], lambda x, display=False:rpccommand(x[0], x[1:], display)]
}

## ["command", [no. of args (-1, no limit)], function, optional helptext]
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
                commands[cmd[0]][1](display=True)
            else:
                commands[cmd[0]][1](*cmd[1:], display=True)
            return True
        elif commands[cmd[0]][0][0] == -1:
            commands[cmd[0]][1](cmd[1:], display=True)
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

# Copied from: stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user
def _find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch

getch = _find_getch()

def handleInput(prefix=''):
    char = ''
    result = ''
    i = 0

    sys.stdout.write(prefix)

    while True:
        sys.stdout.flush()
        char = getch()

        if char == '\r':
            sys.stdout.write('\r\n')
            return str(result)
        elif char == '\x1b':
            getch() # Always "["
            arrow = getch() # A up, B down, C right, D left
            if arrow == 'C':
                if i != len(result):
                    sys.stdout.write(result[i])
                    i += 1
            elif arrow == 'D':
                if i > 0:
                    sys.stdout.write('\b')
                    i -= 1
        elif char == '\x7f': # backspace
            if i > 0:
                end = result[i:]
                result = result[:i-1] + end
                end += ' '
                sys.stdout.write('\b%s%s' % (end, '\b'*len(end)))
                i -= 1
        elif char == '\x03': # ctrl+c
            exit(1)
        elif char == '\t':
            if len(result.strip()) == 0 or i != len(result): continue
            cmd = result.split()[0]
            if len(cmd) != len(result): continue # continue if tabbing a param

            hits = []
            for ii in config.commands:
                if len(cmd) <= len(ii) and ii[:len(cmd)] == cmd:
                    if len(hits) == 1:
                        print()
                        print(hits[0])
                        print(ii)
                    elif len(hits) > 1:
                        print(ii)
                    hits.append(ii)
            if len(hits) == 1:
                result = hits[0] + ' '
                i = len(result)
                sys.stdout.write(result[len(cmd):])
            elif len(hits) > 1:
                print()
                sys.stdout.write(prefix+result)
                same = ''
                for ii in enumerate(hits[0][i:], i):
                    for iii in hits:
                        if ii[0] == len(iii) or iii[ii[0]] != ii[1]:
                            result += same
                            i += len(same)
                            sys.stdout.write(same)
                            same = None
                            break
                    if same == None:
                        break
                    else:
                        same += ii[1]
        elif i == len(result):
            sys.stdout.write(char)
            result += char
            i += 1
        else:
            end = char+result[i:]
            sys.stdout.write(end+'\b'*(len(end)-1))
            result = result[:i]+end
            i += 1

#TODO Allow multi-line commands in prompt (for exec)
def prompt():
    global input
    cmdHelp = generateCmdHelp(sbtc_commands)
    cmd = ''

    print('%s by %s' % (config.VERSION, config.CREDITS))

    while cmd != 'exit':
        # FIXME Handle Exceptions properly (Catch TypeError at least)
        if len(cmd) > 0:
            cmd = joinQuotes(cmd.split(' '))
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

        cmd = handleInput('> ').strip()
