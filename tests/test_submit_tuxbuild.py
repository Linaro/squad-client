import unittest
import unittest.mock
import subprocess as sp
import os

from . import settings
from squad_client.commands.submit_tuxbuild import ALLOWED_METADATA, load_builds, create_name, create_metadata
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad
from squad_client.exceptions import InvalidBuildJson
from squad_client.utils import first


class SubmitTuxbuildCommandTest(unittest.TestCase):

    def setUp(self):
        self.root_dir = os.path.join("tests", "data", "submit_tuxbuild")
        self.assertTrue(os.path.exists(self.root_dir))

        self.build_dir = os.path.join(self.root_dir, "build-x86-gcc")
        self.assertTrue(os.path.exists(self.build_dir))

        self.buildset_dir = os.path.join(self.root_dir, "buildset-x86")
        self.assertTrue(os.path.exists(self.buildset_dir))

    def test_load_builds_with_build(self):
        builds = load_builds(os.path.join(self.build_dir, "build.json"))
        self.assertEqual(len(builds), 1)

    def test_load_builds_with_buildset(self):
        builds = load_builds(os.path.join(self.buildset_dir, "build.json"))
        self.assertEqual(len(builds), 3)

    def test_load_builds_missing_json(self):
        with self.assertRaises(FileNotFoundError):
            load_builds(os.path.join(self.root_dir, "missing.json"))

    def test_load_builds_empty_json(self):
        with self.assertRaises(InvalidBuildJson):
            load_builds(os.path.join(self.root_dir, "empty.json"))

    def test_create_name_with_build(self):
        build = load_builds(os.path.join(self.build_dir, "build.json")).pop()
        self.assertEqual(create_name(build), "build/lkft-build-x86-gcc")

    def test_create_name_with_buildset(self):
        builds = load_builds(os.path.join(self.buildset_dir, "build.json"))

        tests = [
            "build/x86_64-gcc-8-allnoconfig",
            "build/x86_64-gcc-8-tinyconfig",
            "build/x86_64-gcc-8-x86_64_defconfig",
        ]

        self.assertEqual([create_name(build) for build in builds], tests)

    @unittest.mock.patch.dict(os.environ, {"KERNEL_BRANCH": "master"})
    def check_metadata(self, build):
        metadata = create_metadata(build)

        self.assertEqual(sorted(metadata.keys()), ALLOWED_METADATA)

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

    def test_create_metadata_with_build(self):
        build = load_builds(os.path.join(self.build_dir, "build.json")).pop()

        self.check_metadata(build)

    def test_create_metadata_with_buildset(self):
        builds = load_builds(os.path.join(self.buildset_dir, "build.json"))

        for build in builds:
            self.check_metadata(build)


class SubmitTuxbuildCommandIntegrationTest(unittest.TestCase):

    testing_server = "http://localhost:%s" % settings.DEFAULT_SQUAD_PORT
    testing_token = "193cd8bb41ab9217714515954e8724f651ef8601"

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
        self.assertEqual(sorted(testrun.metadata.__dict__.keys()), sorted(["id"] + ALLOWED_METADATA))

        base_kconfig = [
            "defconfig",
            "https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/lkft.config",
            "https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/lkft-crypto.config",
            "https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/distro-overrides.config",
            "https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/systemd.config",
            "https://raw.githubusercontent.com/Linaro/meta-lkft/sumo/recipes-kernel/linux/files/virtio.config",
        ]

        expected_metadata = {
            "git_repo": "https://gitlab.com/Linaro/lkft/mirrors/next/linux-next",
            "git_ref": None,
            "git_commit": "ea586a076e8aa606c59b66d86660590f18354b11",
            "git_sha": "ea586a076e8aa606c59b66d86660590f18354b11",
            "git_short_log": "ea586a076e8a (\"Add linux-next specific files for 20211224\")",
            "git_describe": "next-20211224",
            "kconfig": base_kconfig + ["CONFIG_IGB=y", "CONFIG_UNWINDER_FRAME_POINTER=y", "CONFIG_SYN_COOKIES=y"],
            "git_branch": os.environ.get("KERNEL_BRANCH"),
            "make_kernelversion": "5.16.0-rc6",
            "kernel_version": "5.16.0-rc6",
            "config": "https://builds.tuxbuild.com/22j6EntJ5Zvge15BqZdxWSJllti/config",
            "download_url": "https://builds.tuxbuild.com/22j6EntJ5Zvge15BqZdxWSJllti/",
            "duration": 273,
            "toolchain": "gcc-11"
        }

        for k in ALLOWED_METADATA:
            self.assertEqual(getattr(testrun.metadata, k), expected_metadata[k], msg=k)

        environment = project.environment("x86_64")
        self.assertIsNotNone(environment)

        suite = project.suite("build")
        self.assertIsNotNone(suite)

        test = first(self.squad.tests(name="gcc-11-defconfig-ec3ad359"))
        self.assertEqual("build/gcc-11-defconfig-ec3ad359", test.name)
        self.assertEqual("pass", test.status)

        metric = first(self.squad.metrics(name="gcc-11-defconfig-ec3ad359-warnings"))
        self.assertEqual("build/gcc-11-defconfig-ec3ad359-warnings", metric.name)
        self.assertEqual(1, metric.result)

        metric = first(self.squad.metrics(name="gcc-11-defconfig-ec3ad359-duration"))
        self.assertEqual("build/gcc-11-defconfig-ec3ad359-duration", metric.name)
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
            "git_repo": "https://gitlab.com/Linaro/lkft/mirrors/next/linux-next",
            "git_ref": None,
            "git_commit": "ea586a076e8aa606c59b66d86660590f18354b11",
            "git_sha": "ea586a076e8aa606c59b66d86660590f18354b11",
            "git_short_log": "ea586a076e8a (\"Add linux-next specific files for 20211225\")",
            "git_describe": "next-20211225",
            "git_branch": os.environ.get("KERNEL_BRANCH"),
            "make_kernelversion": "5.16.0-rc6",
            "kernel_version": "5.16.0-rc6",
            "toolchain": "gcc-8",
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
            self.assertEqual(sorted(tr.metadata.__dict__.keys()), sorted(["id"] + ALLOWED_METADATA))

            metadata = expected_metadata.pop(0)
            for k in ALLOWED_METADATA:
                self.assertEqual(getattr(tr.metadata, k), metadata[k])

        environment = project.environment("x86_64")
        self.assertIsNotNone(environment)

        suite = project.suite("build")
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
        self.assertEqual(1, metric.result)

        metric = first(self.squad.metrics(name="gcc-8-x86_64_defconfig-warnings"))
        self.assertEqual("build/gcc-8-x86_64_defconfig-warnings", metric.name)
        self.assertEqual(0, metric.result)

        metric = first(self.squad.metrics(name="gcc-8-allnoconfig-duration"))
        self.assertEqual("build/gcc-8-allnoconfig-duration", metric.name)
        self.assertEqual(121, metric.result)

        metric = first(self.squad.metrics(name="gcc-8-tinyconfig-duration"))
        self.assertEqual("build/gcc-8-tinyconfig-duration", metric.name)
        self.assertEqual(125, metric.result)

        metric = first(self.squad.metrics(name="gcc-8-x86_64_defconfig-duration"))
        self.assertEqual("build/gcc-8-x86_64_defconfig-duration", metric.name)
        self.assertEqual(347, metric.result)

    def test_submit_tuxbuild_empty(self):
        proc = self.submit_tuxbuild(os.path.join(self.root_dir, "empty.json"))
        self.assertFalse(proc.ok, msg=proc.err)
        self.assertIn("Failed to load json", proc.err)

    def test_submit_tuxbuild_missing(self):
        proc = self.submit_tuxbuild(os.path.join(self.root_dir, "missing.json"))
        self.assertFalse(proc.ok)
        self.assertIn("No such file or directory", proc.err)
