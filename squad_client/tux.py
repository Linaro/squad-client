import hashlib
import json
import logging
import os
import posixpath
import requests
import urllib


logger = logging.getLogger(__name__)


def load_builds(build_json):
    builds = None

    try:
        with open(build_json) as fp:
            builds = json.load(fp)

    except json.JSONDecodeError as jde:
        logger.error("Failed to load json: %s", jde)

    except OSError as ose:
        logger.error("Failed to open file: %s", ose)

    return builds


def build_test_name(build):
    sha = combined_kconfig_sha(build)

    return "build/%s-%s-%s" % (
        build["build_name"],
        build["kconfig"][0],
        sha
    )


def buildset_test_name(build):
    return "build/%s-%s-%s-%s" % (
        build["build_name"],
        build["target_arch"],
        build["toolchain"],
        build["kconfig"][0],
    )


def combined_kconfig_sha(build):
    sha1 = hashlib.sha1()

    for k in build["kconfig"][1:]:
        if k.startswith("http"):
            url = urllib.parse.urlparse(k)
            partial = os.path.basename(url.path)
            config = urllib.parse.urljoin(build["download_url"], posixpath.join("fragments", partial))
            r = requests.get(config)
            sha1.update(r.text.encode())
        else:
            sha1.update(f"{k}\n".encode())

    return sha1.hexdigest()[0:8]


ALLOWED_METADATA = [
    "config",
    "download_url",
    "duration",
    "git_branch",
    "git_commit",
    "git_describe",
    "git_ref",
    "git_repo",
    "git_sha",
    "git_short_log",
    "kconfig",
    "kernel_version",
    "make_kernelversion",
]


def build_metadata(build):
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
