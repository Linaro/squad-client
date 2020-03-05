#!/usr/bin/env python3

import argparse
import sys


from squad_client.core.command import SquadClientCommand
from squad_client.commands import *


def main():
    parser = argparse.ArgumentParser(prog='./manage.py')
    parser.add_argument('--debug', action='store_true', help='display debug messages')
    subparser = parser.add_subparsers(help='available subcommands', dest='command')

    SquadClientCommand.add_commands(subparser)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return -1

    rc = SquadClientCommand.process(args)
    return 1 if rc is False else 0 if rc is True else -1


if __name__ == '__main__':
    sys.exit(main())
