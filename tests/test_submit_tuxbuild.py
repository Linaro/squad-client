import unittest
import subprocess as sp
import os

from . import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad
from squad_client.utils import first

import squad_client.commands.submit_tuxbuild


class SubmitTuxbuildCommandTest(unittest.TestCase):

    testing_server = "http://localhost:%s" % settings.DEFAULT_SQUAD_PORT
    testing_token = "193cd8bb41ab9217714515954e8724f651ef8601"

    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(url=self.testing_server, token=self.testing_token)

    def submit_tuxbuild(self, tuxbuild):
        argv = [
            "./manage.py",
            "--squad-host",
            self.testing_server,
            "--squad-token",
            self.testing_token,
            "submit-tuxbuild",
            "--group",
            "my_group",
            "--project",
            "my_project",
            tuxbuild,
        ]

        env = os.environ.copy()
        env['LOG_LEVEL'] = 'INFO'
        proc = sp.Popen(argv, stdout=sp.PIPE, stderr=sp.PIPE, env=env)
        proc.ok = False

        try:
            out, err = proc.communicate()
            proc.ok = proc.returncode == 0
        except sp.TimeoutExpired:
            self.logger.error(
                'Running "%s" time out after %i seconds!' % " ".join(argv)
            )
            proc.kill()
            out, err = proc.communicate()

        proc.out = out.decode("utf-8")
        proc.err = err.decode("utf-8")
        return proc

    def test_submit_tuxbuild_build(self):
        proc = self.submit_tuxbuild("tests/data/submit/tuxbuild/build.json")
        self.assertTrue(proc.ok, msg=proc.err)
        self.assertTrue(proc.err.count("Submitting 1 tests") == 3)

        build = (
            self.squad.group("my_group").project("my_project").build("next-20201021")
        )
        self.assertIsNotNone(build)
        self.assertEqual(
            sorted(squad_client.commands.submit_tuxbuild.ALLOWED_METADATA + ["id"]),
            sorted(list(build.metadata.__dict__.keys())),
        )
        self.assertIsNone(build.metadata.git_branch)

        build = (
            self.squad.group("my_group").project("my_project").build("v4.4.4")
        )
        self.assertIsNotNone(build)
        self.assertEqual(
            sorted(squad_client.commands.submit_tuxbuild.ALLOWED_METADATA + ["id"]),
            sorted(list(build.metadata.__dict__.keys())),
        )
        self.assertIsNone(build.metadata.git_branch)

        for arch in ["arm64", "x86"]:
            environment = (
                self.squad.group("my_group").project("my_project").environment(arch)
            )
            self.assertIsNotNone(environment, "environment %s does not exist" % (arch))

        suite = self.squad.group("my_group").project("my_project").suite("build")
        self.assertIsNotNone(suite)

        test = first(self.squad.tests(name="gcc-9-defconfig-b9979cfa"))
        self.assertEqual("build/gcc-9-defconfig-b9979cfa", test.name)
        self.assertEqual("pass", test.status)

        test = first(self.squad.tests(name="gcc-9-defconfig-5b09568e"))
        self.assertEqual("build/gcc-9-defconfig-5b09568e", test.name)
        self.assertEqual("fail", test.status)

    def test_submit_tuxbuild_buildset(self):
        os.environ["KERNEL_BRANCH"] = "master"
        proc = self.submit_tuxbuild("tests/data/submit/tuxbuild/buildset.json")
        self.assertTrue(proc.ok, msg=proc.out)
        self.assertIn("Submitting 3 tests", proc.err)

        build = (
            self.squad.group("my_group").project("my_project").build("next-20201030")
        )
        self.assertIsNotNone(build)
        self.assertEqual(
            sorted(squad_client.commands.submit_tuxbuild.ALLOWED_METADATA + ["id"]),
            sorted(list(build.metadata.__dict__.keys())),
        )
        self.assertEqual(build.metadata.git_branch, os.environ.get("KERNEL_BRANCH"))

        environment = (
            self.squad.group("my_group").project("my_project").environment("x86")
        )
        self.assertIsNotNone(environment)

        suite = self.squad.group("my_group").project("my_project").suite("build")
        self.assertIsNotNone(suite)

        test = first(self.squad.tests(name="gcc-8-allnoconfig"))
        self.assertEqual("build/gcc-8-allnoconfig", test.name)
        self.assertEqual("pass", test.status)

        test = first(self.squad.tests(name="gcc-8-tinyconfig"))
        self.assertEqual("build/gcc-8-tinyconfig", test.name)
        self.assertEqual("pass", test.status)

        test = first(self.squad.tests(name="gcc-8-x86_64_defconfig"))
        self.assertEqual("build/gcc-8-x86_64_defconfig", test.name)
        self.assertEqual("pass", test.status)

    def test_submit_tuxbuild_empty(self):
        proc = self.submit_tuxbuild("")
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn("No such file or directory: ''", proc.err)

    def test_submit_tuxbuild_malformed(self):
        proc = self.submit_tuxbuild("tests/data/submit/tuxbuild/malformed.json")
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn("Failed to load json", proc.err)

    def test_submit_tuxbuild_missing(self):
        proc = self.submit_tuxbuild("tests/data/submit/tuxbuild/missing.json")
        self.assertFalse(proc.ok)
        self.assertIn(
            "No such file or directory: 'tests/data/submit/tuxbuild/missing.json'",
            proc.err,
        )

    def test_submit_tuxbuild_empty_build_status(self):
        proc = self.submit_tuxbuild(
            "tests/data/submit/tuxbuild/empty_build_status.json"
        )
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn(
            "Failed to validate tuxbuild data: '' is not one of ['fail', 'pass']",
            proc.err,
        )
        self.assertIn(
            "Failed validating 'enum' in schema['items'][0]['properties']['build_status']", proc.err
        )

    def test_submit_tuxbuild_malformed_build_status(self):
        proc = self.submit_tuxbuild(
            "tests/data/submit/tuxbuild/malformed_build_status.json"
        )
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn(
            "Failed to validate tuxbuild data: {'build': 'pass'} is not of type 'string'",
            proc.err,
        )
        self.assertIn(
            "Failed validating 'type' in schema['items'][0]['properties']['build_status']", proc.err
        )

    def test_submit_tuxbuild_missing_build_status(self):
        proc = self.submit_tuxbuild(
            "tests/data/submit/tuxbuild/missing_build_status.json"
        )
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn(
            "Failed to validate tuxbuild data: 'build_status' is a required property",
            proc.err,
        )

    def test_submit_tuxbuild_empty_kconfig(self):
        proc = self.submit_tuxbuild("tests/data/submit/tuxbuild/empty_kconfig.json")
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn("Failed to validate tuxbuild data: [] is too short", proc.err)
        self.assertIn(
            "Failed validating 'minItems' in schema['items'][0]['properties']['kconfig']", proc.err
        )

    def test_submit_tuxbuild_malformed_kconfig(self):
        proc = self.submit_tuxbuild("tests/data/submit/tuxbuild/malformed_kconfig.json")
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn(
            "Failed to validate tuxbuild data: {'CONFIG_ARM64_MODULE_PLTS': 'y'} is not of type 'string'",
            proc.err,
        )
        self.assertIn(
            "Failed validating 'type' in schema['items'][0]['properties']['kconfig']['items'][0]",
            proc.err,
        )

    def test_submit_tuxbuild_missing_kconfig(self):
        proc = self.submit_tuxbuild("tests/data/submit/tuxbuild/missing_kconfig.json")
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn(
            "Failed to validate tuxbuild data: 'kconfig' is a required property",
            proc.err,
        )
