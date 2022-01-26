import os
import subprocess as sp
import unittest
import unittest.mock

import squad_client.tux as sct

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

    @unittest.mock.patch.dict(os.environ, {"KERNEL_BRANCH": "master"})
    def test_submit_tuxbuild_build(self):
        proc = self.submit_tuxbuild(os.path.join(self.build_dir, "build.json"))
        self.assertTrue(proc.ok, msg=proc.err)
        self.assertTrue(proc.err.count("Submitting 1 tests, 2 metrics") == 1)
        project = self.squad.group("my_group").project("my_project")

        build = project.build("next-20211224")
        self.assertIsNotNone(build)

        testrun = first(build.testruns())
        self.assertIsNotNone(testrun)

        # Make sure there's no extra attributes in the testrun metadata object
        # all objects fetched from squad have an id attribute, but the metadata does not use it
        self.assertEqual(sorted(testrun.metadata.__dict__.keys()), sorted(["id"] + sct.ALLOWED_METADATA))

        base_kconfig = [
            'defconfig',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/lkft.config',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/lkft-crypto.config',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/distro-overrides.config',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/systemd.config',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/virtio.config',
        ]

        # Make sure metadata values match expected values
        expected_metadata = {
            'git_repo': "https://gitlab.com/Linaro/lkft/mirrors/next/linux-next",
            'git_ref': os.environ.get("KERNEL_BRANCH"),
            'git_commit': "ea586a076e8aa606c59b66d86660590f18354b11",
            'git_sha': "ea586a076e8aa606c59b66d86660590f18354b11",
            'git_short_log': "ea586a076e8a (\"Add linux-next specific files for 20211224\")",
            'git_describe': "next-20211224",
            'kconfig': base_kconfig + ["CONFIG_IGB=y", "CONFIG_UNWINDER_FRAME_POINTER=y", "CONFIG_SYN_COOKIES=y"],
            'git_branch': os.environ.get("KERNEL_BRANCH"),
            'make_kernelversion': "5.16.0-rc6",
            'kernel_version': "5.16.0-rc6",
            'config': "https://builds.tuxbuild.com/22j6EntJ5Zvge15BqZdxWSJllti/config",
            'download_url': "https://builds.tuxbuild.com/22j6EntJ5Zvge15BqZdxWSJllti/",
            'duration': 273,
        }

        for k in sct.ALLOWED_METADATA:
            self.assertTrue(getattr(testrun.metadata, k), msg=k)
            self.assertEqual(getattr(testrun.metadata, k), expected_metadata[k], msg=k)

        environment = project.environment("x86_64")
        self.assertIsNotNone(environment)

        suite = project.suite("build")
        self.assertIsNotNone(suite)

        test = first(self.squad.tests(name="build-x86-gcc-defconfig-1f07a874"))
        self.assertEqual("build/build-x86-gcc-defconfig-1f07a874", test.name)
        self.assertEqual("pass", test.status)

        metric = first(self.squad.metrics(name="build-x86-gcc-defconfig-1f07a874-warnings"))
        self.assertEqual("build/build-x86-gcc-defconfig-1f07a874-warnings", metric.name)
        self.assertEqual(1, metric.result)

        metric = first(self.squad.metrics(name="build-x86-gcc-defconfig-1f07a874-duration"))
        self.assertEqual("build/build-x86-gcc-defconfig-1f07a874-duration", metric.name)
        self.assertEqual(273, metric.result)

    @unittest.mock.patch.dict(os.environ, {"KERNEL_BRANCH": "master"})
    def test_submit_tuxbuild_buildset(self):
        proc = self.submit_tuxbuild(os.path.join(self.buildset_dir, "build.json"))
        self.assertTrue(proc.ok, msg=proc.out)
        self.assertTrue(proc.err.count("Submitting 1 tests, 2 metrics") == 3)
        project = self.squad.group("my_group").project("my_project")

        build = project.build("next-20211225")
        self.assertIsNotNone(build)

        testruns = build.testruns()
        self.assertIsNotNone(testruns)

        base_metadata = {
            'git_repo': "https://gitlab.com/Linaro/lkft/mirrors/next/linux-next",
            'git_ref': os.environ.get("KERNEL_BRANCH"),
            'git_commit': "ea586a076e8aa606c59b66d86660590f18354b11",
            'git_sha': "ea586a076e8aa606c59b66d86660590f18354b11",
            'git_short_log': "ea586a076e8a (\"Add linux-next specific files for 20211225\")",
            'git_describe': "next-20211225",
            'git_branch': os.environ.get("KERNEL_BRANCH"),
            'make_kernelversion': "5.16.0-rc6",
            'kernel_version': "5.16.0-rc6",
        }

        expected_metadata = [
            dict(base_metadata, **{
                "config": "https://builds.tuxbuild.com/22j6CjIqvbdDMVUVrumx3inbHFX/config",
                "download_url": "https://builds.tuxbuild.com/22j6CjIqvbdDMVUVrumx3inbHFX/",
                "duration": 121,
                "kconfig": ["allnoconfig"],
            }),
            dict(base_metadata, **{
                "config": "https://builds.tuxbuild.com/22j6CiFwHyguAAMiJCFbJOr9KRw/config",
                "download_url": "https://builds.tuxbuild.com/22j6CiFwHyguAAMiJCFbJOr9KRw/",
                "duration": 125,
                "kconfig": ["tinyconfig"],
            }),
            dict(base_metadata, **{
                "config": "https://builds.tuxbuild.com/22j6ClgZS7KogYSjiW86y3djh1q/config",
                "download_url": "https://builds.tuxbuild.com/22j6ClgZS7KogYSjiW86y3djh1q/",
                "duration": 347,
                "kconfig": ["x86_64_defconfig"],
            }),
        ]

        for tr in testruns.values():
            # Make sure there's no extra attributes in the metadata object
            # all objects fetched from squad have an id attribute, but the metadata does not use it
            self.assertEqual(sorted(tr.metadata.__dict__.keys()), sorted(["id"] + sct.ALLOWED_METADATA))

            metadata = expected_metadata.pop(0)
            for k in sct.ALLOWED_METADATA:
                self.assertTrue(getattr(tr.metadata, k), msg=k)
                self.assertEqual(getattr(tr.metadata, k), metadata[k])

        environment = project.environment("x86_64")
        self.assertIsNotNone(environment)

        suite = project.suite("build")
        self.assertIsNotNone(suite)

        test = first(self.squad.tests(name="buildset-x86-x86_64-gcc-8-allnoconfig"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-allnoconfig", test.name)
        self.assertEqual("pass", test.status)

        test = first(self.squad.tests(name="buildset-x86-x86_64-gcc-8-tinyconfig"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-tinyconfig", test.name)
        self.assertEqual("pass", test.status)

        test = first(self.squad.tests(name="buildset-x86-x86_64-gcc-8-x86_64_defconfig"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-x86_64_defconfig", test.name)
        self.assertEqual("pass", test.status)

        metric = first(self.squad.metrics(name="buildset-x86-x86_64-gcc-8-allnoconfig-warnings"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-allnoconfig-warnings", metric.name)
        self.assertEqual(0, metric.result)

        metric = first(self.squad.metrics(name="buildset-x86-x86_64-gcc-8-tinyconfig-warnings"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-tinyconfig-warnings", metric.name)
        self.assertEqual(1, metric.result)

        metric = first(self.squad.metrics(name="buildset-x86-x86_64-gcc-8-x86_64_defconfig-warnings"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-x86_64_defconfig-warnings", metric.name)
        self.assertEqual(0, metric.result)

        metric = first(self.squad.metrics(name="buildset-x86-x86_64-gcc-8-allnoconfig-duration"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-allnoconfig-duration", metric.name)
        self.assertEqual(121, metric.result)

        metric = first(self.squad.metrics(name="buildset-x86-x86_64-gcc-8-tinyconfig-duration"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-tinyconfig-duration", metric.name)
        self.assertEqual(125, metric.result)

        metric = first(self.squad.metrics(name="buildset-x86-x86_64-gcc-8-x86_64_defconfig-duration"))
        self.assertEqual("build/buildset-x86-x86_64-gcc-8-x86_64_defconfig-duration", metric.name)
        self.assertEqual(347, metric.result)

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
