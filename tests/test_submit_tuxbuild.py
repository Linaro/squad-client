import unittest
import subprocess as sp
import os

import squad_client.tux

from . import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad
from squad_client.utils import first


class SubmitTuxbuildCommandTest(unittest.TestCase):

    testing_server = "http://localhost:%s" % settings.DEFAULT_SQUAD_PORT
    testing_token = "193cd8bb41ab9217714515954e8724f651ef8601"

    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(url=self.testing_server, token=self.testing_token)

        self.root_dir = os.path.join("tests", "data", "tux")
        self.assertTrue(os.path.exists(self.root_dir))

        self.build_dir = os.path.join(self.root_dir, "build-x86-gcc")
        self.assertTrue(os.path.exists(self.build_dir))

        self.buildset_dir = os.path.join(self.root_dir, "buildset-x86")
        self.assertTrue(os.path.exists(self.buildset_dir))

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
        proc = self.submit_tuxbuild(os.path.join(self.build_dir, "build.json"))
        self.assertTrue(proc.ok, msg=proc.err)
        self.assertTrue(proc.err.count("Submitting 1 tests, 1 metrics") == 1)

        group = self.squad.group("my_group")
        self.assertIsNotNone(group)

        project = group.project("my_project")
        self.assertIsNotNone(project)

        build = project.build("next-20211224")
        self.assertIsNotNone(build)

        for m in squad_client.tux.ALLOWED_METADATA:
            self.assertTrue(hasattr(build.metadata, m))

        # Make sure there's no extra attributes in the metadata object
        build_metadata = build.metadata.__dict__
        build_metadata.pop("id")
        self.assertEqual(
            sorted(squad_client.tux.ALLOWED_METADATA), sorted(build_metadata)
        )

        suite = project.suite("build")
        self.assertIsNotNone(suite)

        test = first(self.squad.tests(name="build-x86-gcc-defconfig-1f07a874c766dddf24410b80e98d22feb144c871"))
        self.assertEqual("build/build-x86-gcc-defconfig-1f07a874c766dddf24410b80e98d22feb144c871", test.name)
        self.assertEqual("pass", test.status)

        metric = first(self.squad.metrics(name="build-x86-gcc-defconfig-1f07a874c766dddf24410b80e98d22feb144c871-warnings"))
        self.assertEqual("build/build-x86-gcc-defconfig-1f07a874c766dddf24410b80e98d22feb144c871-warnings", metric.name)
        self.assertEqual(1, metric.result)

    def test_submit_tuxbuild_buildset(self):
        os.environ["KERNEL_BRANCH"] = "master"
        proc = self.submit_tuxbuild(os.path.join(self.buildset_dir, "build.json"))
        self.assertTrue(proc.ok, msg=proc.err)
        self.assertTrue(proc.err.count("Submitting 1 tests, 1 metrics") == 12)

        group = self.squad.group("my_group")
        self.assertIsNotNone("my_group")

        project = group.project("my_project")
        self.assertIsNotNone("my_project")

        build = project.build("next-20211224")
        self.assertIsNotNone(build)

        for m in squad_client.tux.ALLOWED_METADATA:
            self.assertTrue(hasattr(build.metadata, m))

        # Make sure there's no extra attributes in the metadata object
        build_metadata = build.metadata.__dict__
        build_metadata.pop("id")
        self.assertEqual(
            sorted(squad_client.tux.ALLOWED_METADATA), sorted(build_metadata),
        )

        environment = project.environment("x86_64")
        self.assertIsNotNone(environment)

        suite = project.suite("build")
        self.assertIsNotNone(suite)

        test = first(self.squad.tests(name="buildset-x86-x86_64-gcc-8-allnoconfig"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-allnoconfig", test.name)
        self.assertEqual("pass", test.status)

        metric = first(self.squad.metrics(name="buildset-x86-x86_64-gcc-8-allnoconfig-warnings"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-allnoconfig-warnings", metric.name)
        self.assertEqual(0, metric.result)

    def test_submit_tuxbuild_empty(self):
        proc = self.submit_tuxbuild("")
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn("No such file or directory: ''", proc.err)

    def test_submit_tuxbuild_missing(self):
        proc = self.submit_tuxbuild(os.path.join(self.root_dir, "missing.json"))
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn(
            "No such file or directory: 'tests/data/tux/missing.json'",
            proc.err,
        )
