#!/usr/bin/env python3

import argparse
import logging
import os
import sys


from squad_client.core.api import SquadApi, ApiException
from squad_client.core.command import SquadClientCommand
from squad_client.commands import *  # noqa


logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)s] %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


def main():
    parser = argparse.ArgumentParser(prog='./manage.py')
    parser.add_argument('--debug', action='store_true', help='display debug messages')
    parser.add_argument('--squad-host', help='SQUAD host, example: https://qa-reports.linaro.org')
    parser.add_argument('--squad-token', help='SQUAD authentication token')
    subparser = parser.add_subparsers(help='available subcommands', dest='command')

    SquadClientCommand.add_commands(subparser)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return -1

    squad_host = args.squad_host or os.getenv('SQUAD_HOST')
    squad_token = args.squad_token or os.getenv('SQUAD_TOKEN')
    if squad_host is None:
        logger.error('Either --squad-host or SQUAD_HOST env variable are required')
        return -1

    try:
        SquadApi.configure(squad_host, token=squad_token)
    except ApiException as e:
        logger.error('Failed to configure squad api: %s' % e)
        return -1

    rc = SquadClientCommand.process(args)
    return 1 if rc is False else 0 if rc is True else -1


if __name__ == '__main__':
    sys.exit(main())
