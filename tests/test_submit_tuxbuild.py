import unittest
import subprocess as sp
import os

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
        self.assertTrue(proc.err.count("Submitting 1 tests, 1 metrics") == 3)
        project = self.squad.group("my_group").project("my_project")

        # Check results for next-20201021, which has 2 instances in build.json
        build = project.build("next-20201021")

        base_kconfig = [
            'defconfig',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/lkft.config',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/lkft-crypto.config',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/distro-overrides.config',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/systemd.config',
            'https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/virtio.config',
        ]

        # Make sure metadata values match expected values
        urls = ['https://builds.tuxbuild.com/%s/' % _id for _id in ['B3TECkH4_1X9yKoWOPIhew', 't8NSUfTBZiSPbBVaXLH7kw']]
        configs = [url + "config" for url in urls]
        expected_metadata = {
            'git_repo': "https://gitlab.com/Linaro/lkft/mirrors/next/linux-next",
            'git_ref': None,
            'git_commit': "5302568121ba345f5c22528aefd72d775f25221e",
            'git_sha': "5302568121ba345f5c22528aefd72d775f25221e",
            'git_short_log': '5302568121ba ("Add linux-next specific files for 20201021")',
            'git_describe': "next-20201021",
            'kconfig': [base_kconfig + ["CONFIG_ARM64_MODULE_PLTS=y"], base_kconfig + ["CONFIG_IGB=y", "CONFIG_UNWINDER_FRAME_POINTER=y"]],
            'git_branch': os.environ.get("KERNEL_BRANCH"),
            'make_kernelversion': "5.9.0",
            'kernel_version': "5.9.0",
            'config': configs,
            'download_url': urls,
        }
        for expected_key in expected_metadata.keys():
            self.assertEqual(expected_metadata[expected_key], getattr(build.metadata, expected_key))

        # Make sure there's no extra attributes in the metadata object
        metadata_attrs = build.metadata.__dict__
        del metadata_attrs["id"]
        self.assertEqual(sorted(expected_metadata.keys()), sorted(metadata_attrs.keys()))

        # Check results for v4.4.4, which has 1 instance in build.json
        build = project.build("v4.4.4")
        # Make sure metadata values match expected values
        url = 'https://builds.tuxbuild.com/%s/' % 'B3TECkH4_1X9yKoWOPIhew'
        config = url + "config"
        expected_metadata = {
            'git_repo': "https://gitlab.com/Linaro/lkft/mirrors/next/linux-next",
            'git_ref': None,
            'git_commit': "5302568121ba345f5c22528aefd72d775f25221e",
            'git_sha': "5302568121ba345f5c22528aefd72d775f25221e",
            'git_short_log': '5302568121ba ("Add linux-next specific files for 20201021")',
            'git_describe': "v4.4.4",
            'kconfig': base_kconfig + ["CONFIG_ARM64_MODULE_PLTS=y"],
            'git_branch': os.environ.get("KERNEL_BRANCH"),
            'make_kernelversion': "5.9.0",
            'kernel_version': "5.9.0",
            'config': config,
            'download_url': url,
        }
        for expected_key in expected_metadata.keys():
            self.assertEqual(expected_metadata[expected_key], getattr(build.metadata, expected_key))

        # Make sure there's no extra attributes in the metadata object
        metadata_attrs = build.metadata.__dict__
        del metadata_attrs["id"]
        self.assertEqual(sorted(expected_metadata.keys()), sorted(metadata_attrs.keys()))

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

        metric = first(self.squad.metrics(name="gcc-9-defconfig-b9979cfa-warnings"))
        self.assertEqual("build/gcc-9-defconfig-b9979cfa-warnings", metric.name)
        self.assertEqual(1, metric.result)

        metric = first(self.squad.metrics(name="gcc-9-defconfig-5b09568e-warnings"))
        self.assertEqual("build/gcc-9-defconfig-5b09568e-warnings", metric.name)
        self.assertEqual(2, metric.result)

    def test_submit_tuxbuild_buildset(self):
        os.environ["KERNEL_BRANCH"] = "master"
        proc = self.submit_tuxbuild("tests/data/submit/tuxbuild/buildset.json")
        self.assertTrue(proc.ok, msg=proc.out)
        self.assertTrue(proc.err.count("Submitting 1 tests, 1 metrics") == 3)

        build = self.squad.group("my_group").project("my_project").build("next-20201030")

        # Make sure metadata values match expected values
        urls = ['https://builds.tuxbuild.com/%s/' % _id for _id in ['9NeOU1kd65bhMrL4eyI2yA', 'cjLreGasHSZj3OctZlNdpw', 'x5Mi9j6xZItTGqVtOKmnVw']]
        configs = [url + "config" for url in urls]
        expected_metadata = {
            'git_repo': "https://gitlab.com/Linaro/lkft/mirrors/next/linux-next",
            'git_ref': None,
            'git_commit': "4e78c578cb987725eef1cec7d11b6437109e9a49",
            'git_sha': "4e78c578cb987725eef1cec7d11b6437109e9a49",
            'git_short_log': '4e78c578cb98 ("Add linux-next specific files for 20201030")',
            'git_describe': "next-20201030",
            'kconfig': [['allnoconfig'], ['tinyconfig'], ['x86_64_defconfig']],
            'git_branch': os.environ.get("KERNEL_BRANCH"),
            'make_kernelversion': "5.10.0-rc1",
            'kernel_version': "5.10.0-rc1",
            'config': configs,
            'download_url': urls,
        }
        for expected_key in expected_metadata.keys():
            self.assertEqual(expected_metadata[expected_key], getattr(build.metadata, expected_key))

        # Make sure there's no extra attributes in the metadata object
        metadata_attrs = build.metadata.__dict__
        del metadata_attrs["id"]
        self.assertEqual(sorted(expected_metadata.keys()), sorted(metadata_attrs.keys()))

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

        metric = first(self.squad.metrics(name="gcc-8-allnoconfig-warnings"))
        self.assertEqual("build/gcc-8-allnoconfig-warnings", metric.name)
        self.assertEqual(0, metric.result)

        metric = first(self.squad.metrics(name="gcc-8-tinyconfig-warnings"))
        self.assertEqual("build/gcc-8-tinyconfig-warnings", metric.name)
        self.assertEqual(0, metric.result)

        metric = first(self.squad.metrics(name="gcc-8-x86_64_defconfig-warnings"))
        self.assertEqual("build/gcc-8-x86_64_defconfig-warnings", metric.name)
        self.assertEqual(0, metric.result)

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
