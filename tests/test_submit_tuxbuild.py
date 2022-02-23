import os
import subprocess as sp
import unittest
import unittest.mock

from . import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad
from squad_client.utils import first


class SubmitTuxbuildCommandTest(unittest.TestCase):

    testing_server = "http://localhost:%s" % settings.DEFAULT_SQUAD_PORT
    testing_token = '193cd8bb41ab9217714515954e8724f651ef8601'

    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(url=self.testing_server, token=self.testing_token)

        self.root_dir = os.path.join("tests", "data", "submit_tuxbuild")
        self.assertTrue(os.path.exists(self.root_dir))

        self.build_dir = os.path.join(self.root_dir, "build-x86-gcc")
        self.assertTrue(os.path.exists(self.build_dir))

        self.buildset_dir = os.path.join(self.root_dir, "buildset-x86")
        self.assertTrue(os.path.exists(self.buildset_dir))

    def submit_tuxbuild(self, tuxbuild):
        argv = [
            './manage.py',
            '--squad-host',
            self.testing_server,
            '--squad-token',
            self.testing_token,
            'submit-tuxbuild',
            '--group',
            'my_group',
            '--project',
            'my_project',
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
                "Running '%s' time out after %i seconds!" % " ".join(argv)
            )
            proc.kill()
            out, err = proc.communicate()

        proc.out = out.decode('utf-8')
        proc.err = err.decode('utf-8')
        return proc

    @unittest.mock.patch.dict(os.environ, {'KERNEL_BRANCH': 'master'})
    def test_submit_tuxbuild_build(self):
        proc = self.submit_tuxbuild(os.path.join(self.build_dir, "build.json"))
        self.assertTrue(proc.ok, msg=proc.err)
        self.assertTrue(proc.err.count('Submitting 1 tests, 2 metrics') == 1)
        project = self.squad.group('my_group').project('my_project')

        build = project.build('next-20220217')
        self.assertIsNotNone(build)

        testrun = first(build.testruns())
        self.assertIsNotNone(testrun)

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
            'git_repo': 'https://gitlab.com/Linaro/lkft/mirrors/next/linux-next',
            'git_ref': 'master',
            'git_sha': '3c30cf91b5ecc7272b3d2942ae0505dd8320b81c',
            'git_short_log': '3c30cf91b5ec ("Add linux-next specific files for 20220217")',
            'git_describe': 'next-20220217',
            'kconfig': base_kconfig + ['CONFIG_IGB=y', 'CONFIG_UNWINDER_FRAME_POINTER=y', 'CONFIG_SYN_COOKIES=y'],
            'kernel_version': '5.17.0-rc4',
            'config': 'https://builds.tuxbuild.com/25EZVbc7oK6aCJfKV7V3dtFOMq5/config',
            'download_url': 'https://builds.tuxbuild.com/25EZVbc7oK6aCJfKV7V3dtFOMq5/',
            'duration': 422,
            'toolchain': 'gcc-11',
        }

        for k, v in expected_metadata.items():
            self.assertEqual(getattr(testrun.metadata, k), v, msg=k)

        environment = self.squad.group('my_group').project('my_project').environment('x86_64')
        self.assertIsNotNone(environment)

        suite = self.squad.group('my_group').project('my_project').suite('build')
        self.assertIsNotNone(suite)

        test = first(self.squad.tests(name='gcc-11-defconfig-ec3ad359'))
        self.assertEqual('build/gcc-11-defconfig-ec3ad359', test.name)
        self.assertEqual('pass', test.status)

        metric = first(self.squad.metrics(name='gcc-11-defconfig-ec3ad359-warnings'))
        self.assertEqual('build/gcc-11-defconfig-ec3ad359-warnings', metric.name)
        self.assertEqual(1, metric.result)

        metric = first(self.squad.metrics(name='gcc-11-defconfig-ec3ad359-duration'))
        self.assertEqual('build/gcc-11-defconfig-ec3ad359-duration', metric.name)
        self.assertEqual(422, metric.result)

        build.delete()

    @unittest.mock.patch.dict(os.environ, {'KERNEL_BRANCH': 'master'})
    def test_submit_tuxbuild_buildset(self):
        proc = self.submit_tuxbuild(os.path.join(self.buildset_dir, "build.json"))
        self.assertTrue(proc.ok, msg=proc.out)
        self.assertTrue(proc.err.count('Submitting 1 tests, 2 metrics') == 3)
        project = self.squad.group('my_group').project('my_project')

        build = project.build('next-20220217')
        self.assertIsNotNone(build)

        testruns = build.testruns()
        self.assertIsNotNone(testruns)

        base_metadata = {
            'git_repo': 'https://gitlab.com/Linaro/lkft/mirrors/next/linux-next',
            'git_ref': 'master',
            'git_sha': '3c30cf91b5ecc7272b3d2942ae0505dd8320b81c',
            'git_short_log': '3c30cf91b5ec ("Add linux-next specific files for 20220217")',
            'git_describe': 'next-20220217',
            'kernel_version': '5.17.0-rc4',
            'toolchain': 'gcc-8',
        }

        expected_metadata = [
            dict(base_metadata, **{
                'config': 'https://builds.tuxbuild.com/25EZULlT5YOdXc5Hix07IGcbFtA/config',
                'download_url': 'https://builds.tuxbuild.com/25EZULlT5YOdXc5Hix07IGcbFtA/',
                'kconfig': ['allnoconfig'],
                'duration': 324,
            }),
            dict(base_metadata, **{
                'config': 'https://builds.tuxbuild.com/25EZUJH3rXb2Ev1z5QUnTc6UKMU/config',
                'download_url': 'https://builds.tuxbuild.com/25EZUJH3rXb2Ev1z5QUnTc6UKMU/',
                'kconfig': ['tinyconfig'],
                'duration': 350,
            }),
            dict(base_metadata, **{
                'config': 'https://builds.tuxbuild.com/25EZUJt40js6qte4xtKeLTnajQd/config',
                'download_url': 'https://builds.tuxbuild.com/25EZUJt40js6qte4xtKeLTnajQd/',
                'kconfig': ['x86_64_defconfig'],
                'duration': 460,
            })
        ]

        for tr in testruns.values():
            metadata = expected_metadata.pop(0)
            for k, v in metadata.items():
                self.assertEqual(getattr(tr.metadata, k), v, msg=k)

        environment = project.environment('x86_64')
        self.assertIsNotNone(environment)

        suite = project.suite('build')
        self.assertIsNotNone(suite)

        test = first(self.squad.tests(name='gcc-8-allnoconfig'))
        self.assertEqual('build/gcc-8-allnoconfig', test.name)
        self.assertEqual('pass', test.status)

        test = first(self.squad.tests(name='gcc-8-tinyconfig'))
        self.assertEqual('build/gcc-8-tinyconfig', test.name)
        self.assertEqual('pass', test.status)

        test = first(self.squad.tests(name='gcc-8-x86_64_defconfig'))
        self.assertEqual('build/gcc-8-x86_64_defconfig', test.name)
        self.assertEqual('pass', test.status)

        metric = first(self.squad.metrics(name='gcc-8-allnoconfig-warnings'))
        self.assertEqual('build/gcc-8-allnoconfig-warnings', metric.name)
        self.assertEqual(0, metric.result)

        metric = first(self.squad.metrics(name='gcc-8-tinyconfig-warnings'))
        self.assertEqual('build/gcc-8-tinyconfig-warnings', metric.name)
        self.assertEqual(1, metric.result)

        metric = first(self.squad.metrics(name='gcc-8-x86_64_defconfig-warnings'))
        self.assertEqual('build/gcc-8-x86_64_defconfig-warnings', metric.name)
        self.assertEqual(0, metric.result)

        metric = first(self.squad.metrics(name='gcc-8-allnoconfig-duration'))
        self.assertEqual('build/gcc-8-allnoconfig-duration', metric.name)
        self.assertEqual(324, metric.result)

        metric = first(self.squad.metrics(name='gcc-8-tinyconfig-duration'))
        self.assertEqual('build/gcc-8-tinyconfig-duration', metric.name)
        self.assertEqual(350, metric.result)

        metric = first(self.squad.metrics(name='gcc-8-x86_64_defconfig-duration'))
        self.assertEqual('build/gcc-8-x86_64_defconfig-duration', metric.name)
        self.assertEqual(460, metric.result)

        build.delete()

    def test_submit_tuxbuild_empty(self):
        proc = self.submit_tuxbuild(os.path.join(self.root_dir, 'empty.json'))
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn('Failed to load json', proc.err)

    def test_submit_tuxbuild_missing(self):
        proc = self.submit_tuxbuild(os.path.join(self.root_dir, 'missing.json'))
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn('No such file or directory', proc.err)

    def test_submit_tuxbuild_empty_build_status(self):
        proc = self.submit_tuxbuild(
            'tests/data/submit/tuxbuild/empty_build_status.json'
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
            'tests/data/submit/tuxbuild/malformed_build_status.json'
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
            'tests/data/submit/tuxbuild/missing_build_status.json'
        )
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn(
            "Failed to validate tuxbuild data: 'build_status' is a required property",
            proc.err,
        )

    def test_submit_tuxbuild_empty_kconfig(self):
        proc = self.submit_tuxbuild('tests/data/submit/tuxbuild/empty_kconfig.json')
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn("Failed to validate tuxbuild data: [] is too short", proc.err)
        self.assertIn(
            "Failed validating 'minItems' in schema['items'][0]['properties']['kconfig']", proc.err
        )

    def test_submit_tuxbuild_malformed_kconfig(self):
        proc = self.submit_tuxbuild('tests/data/submit/tuxbuild/malformed_kconfig.json')
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
        proc = self.submit_tuxbuild('tests/data/submit/tuxbuild/missing_kconfig.json')
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn(
            "Failed to validate tuxbuild data: 'kconfig' is a required property",
            proc.err,
        )
