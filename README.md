# sbtc
## Simple Bitcoin Tools

A collection of tools and scripts to hopefully simplify some tasks for programmers and power users.

Recommended python 3.x, supports python 2.x (not sure which versions specifically).

## Installation

`python setup.py install`

## Usage

You can start an interactive console by simply running `sbtc`. From there you can run any RPC command like you normally would with bitcoin-cli. Try `getinfo`.

You can even use Python eval/exec by enclosing the command in quotes `eval "getblockhash(getblockcount())"`. All the RPC commands have an equivalent python function.

Any interactive console command can be run from a shell with simply `sbtc <cmd> [args,...]`.

## Library

sbtc comes with "sbtclib". It's currently undocumented and may be prone to large changes before v1.0.00. See the source code for usage.
