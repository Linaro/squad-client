import IPython
import sys

from squad_client import logging
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger(__name__)


class ShellCommand(SquadClientCommand):
    command = 'shell'
    help_text = 'run squad-client on shell'

    def register(self, subparser):
        parser = super(ShellCommand, self).register(subparser)
        parser.add_argument('script', nargs='?', help='python script to run')
        parser.add_argument('--script-params', dest='script_params', help='script parameters')

    def run(self, args):
        if args.script:
            with open(args.script, 'r') as script_source:
                try:
                    program = compile(script_source.read(), args.script, 'exec')
                except SyntaxError as e:
                    logger.error('Cannot run "%s": %s' % (args.script, e))
                    return False
            sys.argv = [args.script] + args.script_params.split(" ")
            exec(program)
            return True
        else:
            IPython.embed()
            return True
