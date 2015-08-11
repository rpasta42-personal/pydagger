#!/usr/bin/python3

#you can also use sys.argv

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='Enables the debugging')
args = parser.parse_args()

print('debug = %r' % args.debug)
