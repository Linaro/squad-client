from squad_client import logging
from squad_client.core.command import SquadClientCommand
from squad_client.core.models import Squad
from squad_client.shortcuts import download_tests, get_build


logger = logging.getLogger(__name__)


class DownloadResultsCommand(SquadClientCommand):
    command = "download-results"
    help_text = "download test results from SQUAD"

    def register(self, subparser):
        parser = super(DownloadResultsCommand, self).register(subparser)
        parser.add_argument(
            "--group", help="SQUAD group", required=True
        )
        parser.add_argument(
            "--project", help="SQUAD project", required=True
        )
        parser.add_argument(
            "--build", help="Build version. Exemples: my-build-version. Or pre-defined build aliases: latest and latest-finished", required=True,
        )
        parser.add_argument(
            "--environments", help="Test environments (separated by ',')"
        )
        parser.add_argument(
            "--suites", help="Test suites (separated by ',')"
        )
        parser.add_argument(
            "--filename", help="Name of the output file where results will be written"
        )
        parser.add_argument(
            "--format", help="Format of the output line", default='{test.environment.slug}/{test.name} {test.status}'
        )
        parser.add_argument(
            "--debug",
            action='store_true',
            help="Set debug mode"
        )

    def run(self, args):
        if args.debug:
            logger.setLevel(logging.DEBUG)

        group = Squad().group(args.group)
        if group is None:
            logger.error(f"Group \"{args.group}\"not found")
            return False

        project = group.project(args.project)
        if project is None:
            logger.error(f"Project \"{group.slug}/{args.project}\" not found")
            return False

        build = get_build(args.build, project)
        if build is None:
            logger.error(f"Build \"{group.slug}/{project.slug}/{args.build}\" not found")
            return False

        environments = None
        if args.environments:
            environments = [project.environment(e) for e in args.environments.split(",")]

        suites = None
        if args.suites:
            suites = [project.suite(s) for s in args.suites.split(",")]

        return download_tests(
            project,
            build,
            filter_envs=environments,
            filter_suites=suites,
            format_string=args.format,
            output_filename=args.filename,
        )
