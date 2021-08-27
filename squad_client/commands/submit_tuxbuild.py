import hashlib
import json
import jsonschema
import os

from squad_client import logging
from squad_client.shortcuts import submit_results
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger(__name__)


tuxbuild_schema = {
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
        },
        "required": [
            "build_status",
            "git_describe",
            "kconfig",
            "target_arch",
            "toolchain",
        ],
    }],
}

ALLOWED_METADATA = [
    "git_branch", "git_commit", "git_describe", "git_ref", "git_repo", "git_sha", "git_short_log", "kernel_version", "make_kernelversion",
]


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

    def _build_metadata(self, builds):
        metadata = {k: v for k, v in builds[0].items() if k in ALLOWED_METADATA}

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

        return metadata

    def _load_builds(self, path):
        builds = None
        try:
            with open(path) as f:
                builds = json.load(f)

        except json.JSONDecodeError as jde:
            logger.error("Failed to load json: %s", jde)

        except OSError as ose:
            logger.error("Failed to open file: %s", ose)

        return builds

    def _get_test_name(self, kconfig, toolchain):
        if len(kconfig[1:]):
            kconfig_hash = "%s-%s" % (
                kconfig[0],
                hashlib.sha1(json.dumps(kconfig[1:]).encode()).hexdigest()[0:8],
            )
        else:
            kconfig_hash = kconfig[0]

        return "build/%s-%s" % (toolchain, kconfig_hash)

    def run(self, args):
        builds = self._load_builds(args.tuxbuild)

        # log
        if builds is None:
            return False

        try:
            jsonschema.validate(instance=builds, schema=tuxbuild_schema)
        except jsonschema.exceptions.ValidationError as ve:
            logger.error("Failed to validate tuxbuild data: %s", ve)
            return False

        data = {}
        for build in builds:
            arch = build["target_arch"]
            description = build["git_describe"]
            kconfig = build["kconfig"]
            status = build["build_status"]
            toolchain = build["toolchain"]
            test = self._get_test_name(kconfig, toolchain)

            multi_key = (description, arch)
            if multi_key not in data:
                data[multi_key] = {}

            data[multi_key].update({test: status})

        for key, result in data.items():
            description, arch = key
            submit_results(
                group_project_slug="%s/%s" % (args.group, args.project),
                build_version=description,
                env_slug=arch,
                tests=result,
                metadata=self._build_metadata(builds),
            )

        return True
