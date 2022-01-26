import jsonschema
import squad_client.tux as sct

from squad_client import logging
from squad_client.shortcuts import submit_results
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger(__name__)


tuxbuild_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "minItems": 1,
    "items": [{
        "type": "object",
        "properties": {
            "build_status": {
                "type": "string",
                "enum": ["fail", "pass"],
            },
            "git_describe": {
                "type": "string",
            },
            "kconfig": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": [{"type": "string"}],
            },
            "target_arch": {
                "type": "string",
            },
            "toolchain": {
                "type": "string",
            },
            "download_url": {
                "type": "string",
            },
            "duration": {
                "type": "integer",
            },
            "warnings_count": {
                "type": "integer",
            },
        },
        "required": [
            "download_url",
            "build_status",
            "git_describe",
            "kconfig",
            "target_arch",
            "toolchain",
        ],
    }],
}


class SubmitTuxbuildCommand(SquadClientCommand):
    command = "submit-tuxbuild"
    help_text = "submit tuxbuild results to SQUAD"

    def register(self, subparser):
        parser = super(SubmitTuxbuildCommand, self).register(subparser)
        parser.add_argument(
            "--group", help="SQUAD group where results are stored", required=True
        )
        parser.add_argument(
            "--project", help="SQUAD project where results are stored", required=True
        )
        parser.add_argument(
            "tuxbuild",
            help="File with tuxbuild results to submit",
        )

    def run(self, args):
        builds = sct.load_builds(args.tuxbuild)

        # log
        if builds is None:
            return False

        try:
            jsonschema.validate(instance=builds, schema=tuxbuild_schema)
        except jsonschema.exceptions.ValidationError as ve:
            logger.error("Failed to validate tuxbuild data: %s", ve)
            return False

        for build in builds:
            arch = build["target_arch"]
            description = build["git_describe"]
            warnings_count = build["warnings_count"]
            duration = build["duration"]

            test_status = build["build_status"]
            if len(builds) > 1:
                test_name = sct.buildset_test_name(build)
            else:
                test_name = sct.build_test_name(build)

            tests = {test_name: test_status}
            metrics = {test_name + '-warnings': warnings_count}
            metrics.update({test_name + '-duration': duration})

            submit_results(
                group_project_slug="%s/%s" % (args.group, args.project),
                build_version=description,
                env_slug=arch,
                tests=tests,
                metrics=metrics,
                metadata=sct.build_metadata(build),
            )

        return True
