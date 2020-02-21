from squad_client.core.command import SquadClientCommand
import tests

class TestCommand(SquadClientCommand):
    command = 'test'
    help_text = 'test squad_client code'


    def run(self, args):
        print('Running tests')
        tests.run()
        return True
