from squad_client.core.command import SquadClientCommand


class ReportCommand(SquadClientCommand):
    command = 'report'
    help_text = 'generate reports from yaml descriptor file'


    def run(self, args):
        print('Running report')
        print(args)
        return True
