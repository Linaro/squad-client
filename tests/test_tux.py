import os
import logging
import tempfile
import unittest

from squad_client.tux import build_test_name, buildset_test_name, load_builds, combined_kconfig_sha


class TuxTest(unittest.TestCase):

    def setUp(self):
        self.root_dir = os.path.join("tests", "data", "tux")
        self.assertTrue(os.path.exists(self.root_dir))

        self.build_dir = os.path.join(self.root_dir, "build-x86-gcc")
        self.assertTrue(os.path.exists(self.build_dir))

        self.buildset_dir = os.path.join(self.root_dir, "buildset-x86")
        self.assertTrue(os.path.exists(self.buildset_dir))

        self.tmp_dir = tempfile.mkdtemp()
        self.assertTrue(os.path.exists(self.tmp_dir))

    def test_load_builds_with_build(self):
        builds = load_builds(
            os.path.join(self.build_dir, "build.json")
        )

        self.assertTrue(len(builds) == 1)

    def test_load_builds_with_buildset(self):
        builds = load_builds(
            os.path.join(self.buildset_dir, "build.json")
        )

        self.assertTrue(len(builds) > 1)

    def test_load_builds_with_empty_json(self):
        with self.assertLogs(logger="squad_client.tux", level=logging.ERROR) as log:
            builds = load_builds(os.path.join(self.root_dir, "empty.json"))

            self.assertTrue(builds is None)
            self.assertIn(
                "ERROR:squad_client.tux:Failed to load json: Expecting value: line 1 column 1 (char 0)",
                log.output,
            )

    def test_load_builds_with_missing_json(self):
        with self.assertLogs(logger="squad_client.tux", level=logging.ERROR) as log:
            builds = load_builds(os.path.join(self.root_dir, "missing.json"))

            self.assertTrue(builds is None)
            self.assertIn(
                "ERROR:squad_client.tux:Failed to open file: [Errno 2] No such file or directory: 'tests/data/tux/missing.json'", log.output
            )

    def test_build_test_name(self):
        build = load_builds(
            os.path.join(self.build_dir, "build.json")
        ).pop()

        self.assertEqual(
            build_test_name(build),
            "build/build-x86-gcc-defconfig-1f07a874c766dddf24410b80e98d22feb144c871",
        )

    def test_buildset_test_name(self):
        builds = load_builds(
            os.path.join(self.buildset_dir, "build.json"),
        )

        tests = [
            "build/buildset-x86-x86_64-gcc-8-allnoconfig",
            "build/buildset-x86-x86_64-gcc-8-tinyconfig",
            "build/buildset-x86-x86_64-gcc-8-x86_64_defconfig",
            "build/buildset-x86-x86_64-gcc-9-allnoconfig",
            "build/buildset-x86-x86_64-gcc-9-tinyconfig",
            "build/buildset-x86-x86_64-gcc-9-x86_64_defconfig",
            "build/buildset-x86-x86_64-gcc-10-allnoconfig",
            "build/buildset-x86-x86_64-gcc-10-defconfig",
            "build/buildset-x86-x86_64-gcc-10-tinyconfig",
            "build/buildset-x86-x86_64-gcc-11-allnoconfig",
            "build/buildset-x86-x86_64-gcc-11-defconfig",
            "build/buildset-x86-x86_64-gcc-11-tinyconfig",
        ]

        for build in builds:
            self.assertIn(buildset_test_name(build), tests)

    def test_combined_kconfig_sha_with_build(self):
        build = load_builds(
            os.path.join(self.build_dir, "build.json")
        ).pop()

        """
        ❯ sha1sum tests/data/tux/build-x86-gcc/all.txt
        1f07a874c766dddf24410b80e98d22feb144c871  tests/data/tux/build-x86-gcc/all.txt
        """
        self.assertEqual(
            combined_kconfig_sha(build),
            "1f07a874c766dddf24410b80e98d22feb144c871",
        )
