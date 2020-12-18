import logging

from squad_client.core.api import SquadApi
from squad_client.core.command import SquadClientCommand
from squad_client.version import __version__


logger = logging.getLogger()


class VersionCommand(SquadClientCommand):
    command = 'version'
    help_text = 'display versions of squad-client and server'

    def run(self, args):
        print('squad-client: %s' % __version__)
        print('squad server: %s' % SquadApi.version)
