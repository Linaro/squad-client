import sys
import os
import IPython


from squad_client.core.command import SquadClientCommand


class ShellCommand(SquadClientCommand):
    command = 'shell'
    help_text = 'run squad-client on shell'

    def register(self, subparser):
        parser = super(ShellCommand, self).register(subparser)
        parser.add_argument('script', nargs='?', help='python script to run')

    def run(self, args):
        if args.script:
            with open(args.script, 'r') as script_source:
                try:
                    program = compile(script_source.read(), args.script, 'exec')
                except SyntaxError as e:
                    print('Cannot run "%s": %s' % (args.script, e))

            exec(program)
            return True
        else:
            IPython.embed()
            return True
