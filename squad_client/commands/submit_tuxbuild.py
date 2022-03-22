import hashlib
import json
import jsonschema
import os
import urllib

from squad_client import logging
from squad_client.exceptions import InvalidBuildJson
from squad_client.shortcuts import submit_results
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger(__name__)


TUXBUILD_SCHEMA = {
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
            "build_status",
            "download_url",
            "duration",
            "git_describe",
            "git_ref",
            "git_repo",
            "git_sha",
            "git_short_log",
            "kernel_version",
            "kconfig",
            "target_arch",
            "toolchain",
        ],
    }],
}

ALLOWED_METADATA = TUXBUILD_SCHEMA["items"][0]["required"]


def load_builds(build_json):
    try:
        with open(build_json) as f:
            return json.load(f)
    except json.JSONDecodeError as jde:
        raise InvalidBuildJson(f"Invalid build json: {jde}")


def create_metadata(build):
    metadata = {k: v for k, v in build.items() if k in ALLOWED_METADATA}

    # If `git_ref` is null, use `KERNEL_BRANCH` from the CI environment
    if metadata.get("git_ref") is None:
        metadata.update({"git_ref": os.getenv("KERNEL_BRANCH")})

    # add config file to the metadata
    metadata["config"] = urllib.parse.urljoin(metadata.get('download_url'), "config")

    return metadata


def create_name(build):
    suite = "build/"
    name = ""

    if build["build_name"]:
        name = build["build_name"]
    else:
        name += "%s-%s" % (
            build["toolchain"],
            build["kconfig"][0],
        )

        if len(build["kconfig"]) > 1:
            name += "-" + create_sha(build)

    return suite + name


def create_sha(build):
    sha = hashlib.sha1()

    # log?
    for k in build["kconfig"][1:]:
        sha.update(f"{k}".encode())

    return sha.hexdigest()[0:8]


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
        try:
            builds = load_builds(args.tuxbuild)
        except InvalidBuildJson as ibj:
            logger.error("Failed to load build json: %s", ibj)
            return False
        except OSError as ose:
            logger.error("Failed to load build json: %s", ose)
            return False

        try:
            jsonschema.validate(instance=builds, schema=TUXBUILD_SCHEMA)
        except jsonschema.exceptions.ValidationError as ve:
            logger.error("Failed to validate tuxbuild data: %s", ve)
            return False

        for build in builds:
            arch = build["target_arch"]
            description = build["git_describe"]
            warnings_count = build["warnings_count"]
            test_name = create_name(build)
            test_status = build["build_status"]
            duration = build["duration"]

            tests = {test_name: test_status}
            metrics = {test_name + '-warnings': warnings_count}
            metrics.update({test_name + '-duration': duration})

            submit_results(
                group_project_slug="%s/%s" % (args.group, args.project),
                build_version=description,
                env_slug=arch,
                tests=tests,
                metrics=metrics,
                metadata=create_metadata(build),
            )

        return True
