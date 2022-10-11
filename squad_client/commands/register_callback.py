import sys

from squad_client import logging
from squad_client.shortcuts import register_callback
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger(__name__)


class RegisterCallbackCommand(SquadClientCommand):
    command = "register-callback"
    help_text = "Register callback to a build in SQUAD"

    def register(self, subparser):
        parser = super(RegisterCallbackCommand, self).register(subparser)
        parser.add_argument(
            "--group",
            help="SQUAD group where results are stored",
            required=True,
        )
        parser.add_argument(
            "--project",
            help="SQUAD project slug",
            required=True,
        )
        parser.add_argument(
            "--build",
            help="SQUAD build ID",
            required=True,
        )
        parser.add_argument(
            "--url",
            help="URL to be triggered by the callback",
            required=True,
        )
        parser.add_argument(
            '--record-response',
            help="Specify if it is desired to store callback's response",
            action='store_true'
        )

    def run(self, args):
        ok, errors = register_callback(
            group_slug=args.group,
            project_slug=args.project,
            build_version=args.build,
            url=args.url,
            record_response=args.record_response,
        )

        if len(errors):
            for error in errors:
                print('%s' % error, file=sys.stderr)

        return ok
