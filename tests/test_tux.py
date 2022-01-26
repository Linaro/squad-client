import logging
import os
import responses
import squad_client.tux as sct
import unittest
import unittest.mock


class TuxTest(unittest.TestCase):

    def setUp(self):
        self.root_dir = os.path.join("tests", "data", "tux")
        self.assertTrue(os.path.exists(self.root_dir))

        self.build_dir = os.path.join(self.root_dir, "build-x86-gcc")
        self.assertTrue(os.path.exists(self.build_dir))

        self.buildset_dir = os.path.join(self.root_dir, "buildset-x86")
        self.assertTrue(os.path.exists(self.buildset_dir))

    def test_load_builds_with_build(self):
        builds = sct.load_builds(
            os.path.join(self.build_dir, "build.json")
        )

        self.assertTrue(len(builds) == 1)

    def test_load_builds_with_buildset(self):
        builds = sct.load_builds(
            os.path.join(self.buildset_dir, "build.json")
        )

        self.assertTrue(len(builds) == 3)

    def test_load_builds_with_empty_json(self):
        with self.assertLogs(logger="squad_client.tux", level=logging.ERROR) as log:
            builds = sct.load_builds(os.path.join(self.root_dir, "empty.json"))

            self.assertTrue(builds is None)
            self.assertIn(
                "ERROR:squad_client.tux:Failed to load json: Expecting value: line 1 column 1 (char 0)",
                log.output,
            )

    def test_load_builds_with_missing_json(self):
        with self.assertLogs(logger="squad_client.tux", level=logging.ERROR) as log:
            builds = sct.load_builds(os.path.join(self.root_dir, "missing.json"))

            self.assertTrue(builds is None)
            self.assertIn(
                "ERROR:squad_client.tux:Failed to open file: [Errno 2] No such file or directory: 'tests/data/tux/missing.json'", log.output
            )

    def test_build_test_name(self):
        build = sct.load_builds(
            os.path.join(self.build_dir, "build.json")
        ).pop()

        self.assertEqual(
            sct.build_test_name(build),
            "build/build-x86-gcc-defconfig-1f07a874",
        )

    def test_buildset_test_name(self):
        builds = sct.load_builds(
            os.path.join(self.buildset_dir, "build.json"),
        )

        tests = [
            "build/buildset-x86-x86_64-gcc-8-allnoconfig",
            "build/buildset-x86-x86_64-gcc-8-tinyconfig",
            "build/buildset-x86-x86_64-gcc-8-x86_64_defconfig",
        ]

        for build in builds:
            test = tests.pop(0)
            self.assertEqual(sct.buildset_test_name(build), test)

    @responses.activate
    def test_combined_kconfig_sha_with_build(self):
        build = sct.load_builds(
            os.path.join(self.build_dir, "build.json")
        ).pop()

        download_url = "https://builds.tuxbuild.com/22j6EntJ5Zvge15BqZdxWSJllti"

        configs = [
            "lkft.config",
            "lkft-crypto.config",
            "distro-overrides.config",
            "systemd.config",
            "virtio.config",
        ]

        for config in configs:
            with open(os.path.join(self.build_dir, "fragments", config)) as f:
                responses.add(
                    responses.GET,
                    f"{download_url}/fragments/{config}",
                    body=f.read(),
                    status=200,
                )

        sha1 = sct.combined_kconfig_sha(build)

        self.assertEqual(len(responses.calls), len(configs))

        """
        ❯ sha1sum tests/data/tux/build-x86-gcc/combined.txt
        1f07a874c766dddf24410b80e98d22feb144c871  tests/data/tux/build-x86-gcc/combined.txt
        """
        self.assertEqual(sha1, "1f07a874")

    @unittest.mock.patch.dict(os.environ, {"KERNEL_BRANCH": "master"})
    def check_build_metadata(self, build):
        metadata = sct.build_metadata(build)

        self.assertEqual(sorted(metadata.keys()), sct.ALLOWED_METADATA)

        for key in metadata:
            self.assertTrue(metadata[key], msg=key)

            if key == "config":
                self.assertTrue(metadata["config"].startswith(build["download_url"]))
                self.assertTrue(metadata["config"].endswith("config"))
            elif key == "git_branch":
                self.assertEqual(metadata["git_branch"], os.environ["KERNEL_BRANCH"])
            elif key == "git_commit":
                self.assertEqual(metadata["git_commit"], build["git_sha"])
            elif key == "git_ref":
                self.assertEqual(metadata["git_ref"], os.environ["KERNEL_BRANCH"])
            elif key == "make_kernelversion":
                self.assertEqual(metadata["make_kernelversion"], build["kernel_version"])
            else:
                self.assertEqual(metadata[key], build[key], msg=key)

    def test_build_metadata(self):
        build = sct.load_builds(os.path.join(self.build_dir, "build.json")).pop()

        self.check_build_metadata(build)

    def test_buildset_metadata(self):
        builds = sct.load_builds(os.path.join(self.buildset_dir, "build.json"))

        for build in builds:
            self.check_build_metadata(build)
