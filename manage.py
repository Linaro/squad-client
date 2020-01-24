#!/usr/bin/env python3


import argparse
import sys


import tests


class Manage:

    def __init__(self):
        parser = argparse.ArgumentParser(description='Manage Squad-Client')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, args.command)()

    def test(self):
        parser = argparse.ArgumentParser(description='Runs tests for Squad-Client')
        args = parser.parse_args(sys.argv[2:])
        print('Running tests')
        tests.run()


if __name__ == '__main__':
    Manage()
