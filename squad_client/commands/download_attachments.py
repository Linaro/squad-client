from squad_client import logging
from squad_client.core.command import SquadClientCommand
from squad_client.core.models import TestRun
from squad_client.shortcuts import download_attachments


logger = logging.getLogger(__name__)


class DownloadAttachmentsCommand(SquadClientCommand):
    command = "download-attachments"
    help_text = "download the attachments from a SQUAD testrun"

    def register(self, subparser):
        parser = super(DownloadAttachmentsCommand, self).register(subparser)
        parser.add_argument(
            "--testrun",
            help="The SQUAD ID of the testrun",
            type=int,
            required=True,
        )
        parser.add_argument(
            "--filenames",
            nargs="+",
            help="If not all files are required, specify the names of the files to download",
        )
        parser.add_argument(
            "--debug",
            action='store_true',
            help="Set debug mode"
        )

    def run(self, args):
        if args.debug:
            logger.setLevel(logging.DEBUG)

        # Check testrun
        testrun = TestRun(args.testrun)
        if testrun is None:
            logger.error(f"TestRun {args.testrun} not found")

        # Check if requested files exist
        return download_attachments(testrun, args.filenames)
