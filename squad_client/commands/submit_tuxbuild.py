import hashlib
import json
import jsonschema
import os
import urllib

from urllib import parse as urlparse

from squad_client import logging
from squad_client.exceptions import InvalidBuildJson
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


def load_builds(build_json):
    try:
        with open(build_json) as f:
            return json.load(f)
    except json.JSONDecodeError as jde:
        raise InvalidBuildJson(f"Invalid build json: {jde}")


def create_name(build):
    suite = "build/"
    name = ""

    if build["build_name"]:
        name = build["build_name"]
    else:
        name += "%s-%s-%s" % (
            build["target_arch"],
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


ALLOWED_METADATA = [
    "config",
    "download_url",
    "duration",
    "git_describe",
    "git_ref",
    "git_repo",
    "git_sha",
    "git_short_log",
    "kconfig",
    "kernel_version",
    "toolchain",
]


def create_metadata(build):
    metadata = {k: v for k, v in build.items() if k in ALLOWED_METADATA}

    # We expect git_commit, but tuxmake calls it git_sha
    metadata.update({"git_commit": metadata.get("git_sha")})

    # If `git_ref` is null, use `KERNEL_BRANCH` from the CI environment
    # TODO: Default?
    if metadata.get("git_ref") is None:
        metadata.update({"git_ref": os.getenv("KERNEL_BRANCH")})

    # We expect `git_branch`, but tuxmake calls it `git_ref`
    metadata.update({"git_branch": metadata.get("git_ref")})

    # We expect `make_kernelversion`, but tuxmake calls it `kernel_version`
    metadata.update({"make_kernelversion": metadata.get("kernel_version")})

    # add config file to the metadata
    metadata["config"] = urllib.parse.urljoin(metadata.get('download_url'), "config")

    return metadata


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

        # If `git_ref` is null, use `KERNEL_BRANCH` from the CI environment
        if metadata.get("git_ref") is None:
            metadata.update({"git_ref": os.getenv("KERNEL_BRANCH")})

        # add config file to the metadata
        metadata["config"] = urlparse.urljoin(metadata.get('download_url'), "config")

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

        for build in builds:
            arch = build["target_arch"]
            description = build["git_describe"]
            kconfig = build["kconfig"]
            toolchain = build["toolchain"]
            warnings_count = build["warnings_count"]
            test_name = self._get_test_name(kconfig, toolchain)
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
                metadata=self._build_metadata(build)
            )

        return True
