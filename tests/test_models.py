import unittest

from . import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad, ALL, Project, TestJob
from squad_client.utils import first
from unittest.mock import patch


SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT)


class SquadTest(unittest.TestCase):

    def setUp(self):
        self.squad = Squad()

    def test_groups(self):
        groups = self.squad.groups()
        self.assertTrue(True, len(groups))

    def test_not_found_groups(self):
        groups = self.squad.groups(name__startswith='no group with this name')
        self.assertEqual(0, len(groups))

    def test_groups_with_count(self):
        all_groups = self.squad.groups(count=ALL)
        self.assertEqual(2, len(all_groups))

        one_groups = self.squad.groups(count=1)
        self.assertEqual(1, len(one_groups))

    def test_not_found_group(self):
        not_found_group = self.squad.group('this-group-does-not-really-exist')
        self.assertEqual(None, not_found_group)

    def test_group(self):
        group = self.squad.group('my_group')
        self.assertTrue(group is not None)

    def test_projects(self):
        projects = self.squad.projects()
        self.assertTrue(True, len(projects))

    def test_builds(self):
        builds = self.squad.builds()
        self.assertTrue(True, len(builds))

    def test_testjobs(self):
        testjobs = self.squad.testjobs()
        self.assertTrue(True, len(testjobs))

    def test_testruns(self):
        testruns = self.squad.testruns()
        self.assertTrue(True, len(testruns))

    def test_tests(self):
        tests = self.squad.tests()
        self.assertTrue(True, len(tests))

    def test_suites(self):
        suites = self.squad.suites()
        self.assertTrue(True, len(suites))

    def test_environments(self):
        environments = self.squad.environments()
        self.assertTrue(True, len(environments))

    def test_backends(self):
        backends = self.squad.backends()
        self.assertTrue(True, len(backends))

    def test_emailtemplates(self):
        emailtemplates = self.squad.emailtemplates()
        self.assertTrue(True, len(emailtemplates))

    def test_knownissues(self):
        knownissues = self.squad.knownissues()
        self.assertTrue(True, len(knownissues))

    def test_suitemetadata(self):
        suitemetadata = self.squad.suitemetadata()
        self.assertTrue(True, len(suitemetadata))

    def test_annotations(self):
        annotations = self.squad.annotations()
        self.assertTrue(True, len(annotations))

    def test_metricthresholds(self):
        metricthresholds = self.squad.metricthresholds()
        self.assertTrue(True, len(metricthresholds))

    def test_reports(self):
        reports = self.squad.reports()
        self.assertTrue(True, len(reports))


class BuildTest(unittest.TestCase):

    def setUp(self):
        self.build = first(Squad().builds(version='my_build'))
        self.build2 = first(Squad().builds(version='my_build2'))

    def test_basic(self):
        self.assertTrue(self.build is not None)
        self.assertTrue(self.build2 is not None)

    def test_build_metadata(self):
        metadata = self.build.metadata
        self.assertTrue(metadata.__id__ != '')

    def test_build_tests(self):
        tests = self.build.tests().values()
        self.assertEqual(4, len(tests))

    def test_build_tests_per_environment(self):
        tests = self.build.tests(environment__slug='my_env').values()
        self.assertEqual(4, len(tests))

    def test_build_tests_per_environment_not_found(self):
        tests = self.build.tests(environment__slug='mynonexistentenv').values()
        self.assertEqual(0, len(tests))

    def test_build_tests_change_cache_on_different_filters(self):
        tests = self.build.tests(environment__slug='my_env').values()
        self.assertEqual(4, len(tests))

        tests = self.build.tests(environment__slug='mynonexistentenv').values()
        self.assertEqual(0, len(tests))

    def test_build_tests_change_cache_on_different_builds(self):
        tests = self.build.tests(environment__slug='my_env').values()
        self.assertEqual(4, len(tests))

        tests = self.build2.tests(environment__slug='my_env').values()
        self.assertEqual(0, len(tests))

    def test_build_metrics(self):
        tests = self.build.metrics().values()
        self.assertEqual(1, len(tests))

    def test_build_metrics_per_environment(self):
        tests = self.build.metrics(environment__slug='my_env').values()
        self.assertEqual(1, len(tests))

    def test_build_metrics_per_environment_not_found(self):
        tests = self.build.metrics(environment__slug='mynonexistentenv').values()
        self.assertEqual(0, len(tests))

    def test_build_metrics_change_cache_on_different_filters(self):
        tests = self.build.metrics(environment__slug='my_env').values()
        self.assertEqual(1, len(tests))

        tests = self.build.metrics(environment__slug='mynonexistentenv').values()
        self.assertEqual(0, len(tests))

    def test_build_metrics_change_cache_on_different_builds(self):
        metrics = self.build.metrics(environment__slug='my_env').values()
        self.assertEqual(1, len(metrics))

        metrics = self.build2.metrics(environment__slug='my_env').values()
        self.assertEqual(0, len(metrics))

    def test_build_testrun(self):
        testruns = self.build.testruns(prefetch_metadata=True)
        self.assertEqual(2, len(testruns))

        with patch('squad_client.core.api.SquadApi.get') as squad_api_get:
            testrun = first(testruns)
            self.assertEqual('bar', testrun.metadata.foo)
            squad_api_get.assert_not_called()


class TestRunTest(unittest.TestCase):

    def setUp(self):
        self.testruns = Squad().testruns(count=2)
        self.testrun = self.testruns[1]
        self.testrun_no_metadata = self.testruns[2]

    def test_basic(self):
        self.assertTrue(self.testrun is not None)

    def test_testrun_metadata(self):
        self.assertTrue(self.testrun.metadata_file is not None)
        self.assertTrue(self.testrun.metadata is not None)
        self.assertEqual(self.testrun.metadata.foo, "bar")
        self.assertEqual(self.testrun.metadata.not_existing, None)

        self.assertTrue(self.testrun_no_metadata.metadata_file is not None)
        self.assertTrue(self.testrun_no_metadata.metadata is None)

    def test_testrun_status(self):
        status = self.testrun.summary()
        self.assertEqual(1, status.tests_fail)


class ProjectTest(unittest.TestCase):

    def setUp(self):
        SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT, token='193cd8bb41ab9217714515954e8724f651ef8601')

        self.project = first(Squad().projects(slug='my_project'))
        self.build = first(Squad().builds(version='my_build'))
        self.build2 = first(Squad().builds(version='my_build2'))

    def test_basic(self):
        self.assertTrue(self.project is not None)

    def test_project_environments(self):
        environments = self.project.environments()
        self.assertEqual(2, len(environments))

        environment = self.project.environment('my_env')
        self.assertEqual(environment.slug, 'my_env')

    def test_project_suites(self):
        suites = self.project.suites()
        self.assertEqual(2, len(suites))

        suite = self.project.suite('my_suite')
        self.assertEqual(suite.slug, 'my_suite')

    def test_project_thresholds(self):
        thresholds = self.project.thresholds()
        self.assertEqual(1, len(thresholds))
        threshold = first(thresholds)
        self.assertEqual(threshold.name, 'my-threshold')

    def test_compare_builds_from_same_project(self):
        # tests
        comparison = self.project.compare_builds(self.build2.id, self.build.id)
        self.assertEqual('Cannot report regressions/fixes on non-finished builds', comparison[0])

        # metrics
        comparison = self.project.compare_builds(self.build2.id, self.build.id, by="metrics")
        self.assertEqual('Cannot report regressions/fixes on non-finished builds', comparison[0])

    def test_compare_builds_from_same_project_force(self):
        comparison = self.project.compare_builds(self.build2.id, self.build.id, force=True)
        self.assertEqual({}, comparison['regressions'])
        self.assertEqual({}, comparison['fixes'])

        comparison = self.project.compare_builds(self.build2.id, self.build.id, by="metrics", force=True)
        self.assertEqual({}, comparison['regressions'])
        self.assertEqual({}, comparison['fixes'])

    def test_create_project(self):
        group = Squad().group('my_group')
        slug = 'test-create-project'
        new_project = Project()
        new_project.slug = slug
        new_project.group = group
        new_project.enabled_plugins_list = ['linux-log-parser']
        new_project.save()

        check_project = first(Squad().projects(slug=slug, group__slug=group.slug))
        self.assertEqual(new_project.id, check_project.id)

        new_project.delete()

    def test_save_project_settings(self):
        settings = 'SETTING: value'
        self.project.project_settings = settings
        self.project.save()
        project = first(Squad().projects(slug=self.project.slug))
        self.assertTrue(project is not None)

    def test_project_basic_settings(self):
        self.assertTrue(hasattr(self.project, "basic_settings"))
        self.assertTrue(self.project.basic_settings is not None)
        # These are default values from squad
        self.assertEqual(self.project.basic_settings.build_confidence_count, 20)
        self.assertEqual(self.project.basic_settings.build_confidence_threshold, 90)


class GroupTest(unittest.TestCase):

    def setUp(self):
        SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT, token='193cd8bb41ab9217714515954e8724f651ef8601')

        self.group = first(Squad().groups(slug='my_group'))

    def test_create_project(self):
        project_slug = 'test-create-project2'
        self.group.create_project(slug=project_slug)

        check_project = Squad().projects(slug=project_slug, group__slug=self.group.slug)
        self.assertEqual(1, len(check_project))

        p = first(check_project)
        p.delete()


class SuiteTest(unittest.TestCase):

    def setUp(self):
        self.suite = first(Squad().suites(slug='my_suite'))

    def test_basic(self):
        self.assertTrue(self.suite is not None)

    def test_suite_tests(self):
        tests = self.suite.tests()
        self.assertEqual(4, len(tests))


class TestJobTest(unittest.TestCase):

    def test_basic(self):
        testjob = first(Squad().testjobs())
        fetched_by_id = TestJob(str(testjob.id))
        self.assertEqual(testjob.id, fetched_by_id.id)

    def test_resubmitted_jobs(self):
        testjob = first(Squad().testjobs())
        resubmitted_jobs = testjob.resubmitted_jobs()
        self.assertEqual(1, len(resubmitted_jobs))
        resubmitted = first(resubmitted_jobs)
        self.assertEqual(testjob.url, resubmitted.parent_job)
