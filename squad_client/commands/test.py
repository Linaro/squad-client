from squad_client import logging
from squad_client.core.command import SquadClientCommand


INCLUDE_TESTS_CMD = True


logger = logging.getLogger(__name__)


try:
    import tests
except ImportError:
    INCLUDE_TESTS_CMD = False


class TestCommand(SquadClientCommand):
    command = 'test'
    help_text = 'test squad_client code'

    def register(self, subparser):
        if not INCLUDE_TESTS_CMD:
            return False
        parser = super(TestCommand, self).register(subparser)
        parser.add_argument('tests', nargs='*', help='list of tests to run')
        parser.add_argument('-v', '--verbose', help='verbose mode', action='store_true', default=False)
        parser.add_argument('--coverage', help='run tests with coverage', action='store_true', default=False)

    def run(self, args):
        logger.info('Running tests')
        return tests.run(args.coverage, args.tests, args.verbose)
