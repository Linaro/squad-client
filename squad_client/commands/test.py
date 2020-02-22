import sys
import os


from squad_client.core.command import SquadClientCommand


import tests


class TestCommand(SquadClientCommand):
    command = 'test'
    help_text = 'test squad_client code'

    def register(self, subparser):
        parser = super(TestCommand, self).register(subparser)
        parser.add_argument('tests', nargs='*', help='list of tests to run')
        parser.add_argument('--coverage', help='run tests with coverage', action='store_true', default=False)

    def run(self, args):
        print('Running tests')
        if args.coverage:
            print('\t --coverage is enabled, run `coverage report -m` to view coverage report')
            argv = [
                'coverage', 'run', '--source', 'squad_client', '-m', 'unittest', 'discover'
            ]
            return os.execvp('coverage', argv)
        else:
            tests.run()
            return True
