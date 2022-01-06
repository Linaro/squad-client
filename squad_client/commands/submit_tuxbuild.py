import jsonschema
import os

from urllib import parse as urlparse

from squad_client import logging
from squad_client.shortcuts import submit_results
from squad_client.tux import ALLOWED_METADATA, build_test_name, buildset_test_name, load_builds
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

    def _build_metadata(self, build):
        metadata = {k: v for k, v in build.items() if k in ALLOWED_METADATA}

        # We expect git_commit, but tuxmake calls it git_sha
        metadata.update({"git_commit": metadata.get("git_sha")})

        # We expect `git_branch`, but tuxmake calls it `git_ref`
        # `git_ref` will sometimes be null
        metadata.update({"git_branch": metadata.get("git_ref")})

        # If `git_ref` is null, use `KERNEL_BRANCH` from the CI environment
        if metadata.get("git_branch") is None:
            metadata.update({"git_branch": os.getenv("KERNEL_BRANCH")})

        # We expect `make_kernelversion`, but tuxmake calls it `kernel_version`
        metadata.update({"make_kernelversion": metadata.get("kernel_version")})

        # add config file to the metadata
        metadata["config"] = urlparse.urljoin(metadata.get('download_url'), "config")

        return metadata

    def run(self, args):
        builds = load_builds(args.tuxbuild)

        # log
        if builds is None:
            return False

        try:
            jsonschema.validate(instance=builds, schema=tuxbuild_schema)
        except jsonschema.exceptions.ValidationError as ve:
            logger.error("Failed to validate tuxbuild data: %s", ve)
            return False

        for build in builds:
            if len(builds) > 1:
                test_name = buildset_test_name(build)
            else:
                test_name = build_test_name(build)

            tests = {test_name: build["build_status"]}
            metrics = {test_name + '-warnings': build["warnings_count"]}

            submit_results(
                group_project_slug="%s/%s" % (args.group, args.project),
                build_version=build["git_describe"],
                env_slug=build["target_arch"],
                tests=tests,
                metrics=metrics,
                metadata=self._build_metadata(build)
            )

        return True
