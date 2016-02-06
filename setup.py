#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'sbtc',
    version = '0.2.00',
    author = 'gijensen',
    author_email = 'gijensen@tutanota.com',
    url = 'https://github.com/gijensen/sbtc',
    description = 'Simple Bitcoin Tools',
    license = 'BSD 2-clause',
    install_requires = ['requests', 'psutil'],
    packages = ['sbtclib'],
    scripts = ['sbtc']
)
