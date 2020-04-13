import unittest

from . import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad, ALL
from squad_client.utils import first


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
        self.build = first(Squad().builds(count=1))

    def test_basic(self):
        self.assertTrue(self.build is not None)

    def test_build_metadata(self):
        metadata = self.build.metadata
        self.assertTrue(metadata.__id__ != '')


class TestRunTest(unittest.TestCase):

    def setUp(self):
        self.testrun = first(Squad().testruns(count=1))

    def test_basic(self):
        self.assertTrue(self.testrun is not None)

    def test_testrun_environment(self):
        environment = self.testrun.environment
        self.assertTrue(environment.__id__ != '')

    def test_testrun_status(self):
        status = self.testrun.summary()
        self.assertEqual(1, status.tests_fail)
