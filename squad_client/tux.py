import hashlib
import json
import logging
import os
import posixpath
import tempfile
import urllib


logger = logging.getLogger(__name__)


ALLOWED_METADATA = [
    "config",
    "download_url",
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
    tmp_dir = tempfile.mkdtemp()
    kconfig = os.path.join(tmp_dir, "kconfig")
    with open(kconfig, "w") as kfp:
        for k in build["kconfig"][1:]:
            url = urllib.parse.urlparse(k)

            if url.scheme in ["http", "https"]:
                partial = os.path.basename(url.path)
                src = urllib.parse.urljoin(build["download_url"], posixpath.join("fragments", partial))
                dst = os.path.join(tmp_dir, partial)
                urllib.request.urlretrieve(src, dst)

                with open(dst) as fp:
                    kfp.write(fp.read())

            else:
                kfp.write(k + "\n")

    with open(kconfig) as kfp:
        text = kfp.read()

    return hashlib.sha1(text.encode()).hexdigest()
