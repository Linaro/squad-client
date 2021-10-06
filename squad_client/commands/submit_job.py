import os
import sys

from squad_client import logging
from squad_client.shortcuts import submit_job
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger(__name__)


class SubmitJobCommand(SquadClientCommand):
    command = "submit-job"
    help_text = "submit job requests to SQUAD"

    def register(self, subparser):
        parser = super(SubmitJobCommand, self).register(subparser)
        parser.add_argument(
            "--group", help="SQUAD group where results are stored", required=True
        )
        parser.add_argument(
            "--project", help="SQUAD project where results are stored", required=True
        )
        parser.add_argument(
            "--build", help="Build version where results are stored", required=True
        )
        parser.add_argument(
            "--environment",
            help="Build environent where results are stored",
            required=True,
        )
        parser.add_argument(
            "--backend", help="SQUAD backend to be used to process results", required=True
        )
        parser.add_argument(
            "--definition", help="File containing the job definition", required=True
        )

    def __read_definition(self, file_path):
        if not os.path.exists(file_path):
            logger.error("Definition file %s does not exist" % file_path)
            sys.exit(-1)

        # check file size and quit if the file is too big
        if os.stat(file_path).st_size > 5242881:
            logger.error("%s - file too big" % file_path)
            sys.exit(-1)

        contents = ''
        with open(file_path, "r") as f:
            try:
                contents = f.read()
            except Exception as e:
                logger.error('Failed reading "%s": %s' % (file_path, e))
                sys.exit(-1)

        return contents

    def run(self, args):
        return submit_job(
            group_project_slug="%s/%s" % (args.group, args.project),
            build_version=args.build,
            env_slug=args.environment,
            backend_name=args.backend,
            definition=self.__read_definition(args.definition),
        )
