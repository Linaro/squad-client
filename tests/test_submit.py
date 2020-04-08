import unittest

from . import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad, Group, Project, Build, Environment, Test, TestRun, Metric
from squad_client.utils import first


PASS = 'pass'
FAIL = 'fail'
XFAIL = 'xfail'
SKIP = 'skip'


class SquadSubmitTest(unittest.TestCase):

    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT, token='193cd8bb41ab9217714515954e8724f651ef8601')

    def test_submit(self):
        group = Group()
        group.slug = 'my_group'

        project = Project()
        project.slug = 'my_project'
        project.group = group

        env = Environment()
        env.slug = 'my_env'
        env.project = project

        build = Build()
        build.project = project
        build.version = 'my_build'

        testrun = TestRun()
        testrun.build = build

        test = Test()
        test.name = 'test1'
        test.status = PASS
        test.log = 'test1 log'

        metric = Metric()
        metric.name = 'metric1'
        metric.result = 42

        testrun.environment = env
        testrun.add_test(test)
        testrun.add_metric(metric)
        testrun.log = 'really long log'
        testrun.metadata = {'metadata1': 'value1', 'metadata2': 'value2', 'job_id': '123'}

        testrun.submit_results()

        results = self.squad.tests(name='test1')
        self.assertTrue(len(results) > 0)
        t = first(results)
        self.assertEqual(t.log, test.log)
        self.assertEqual(t.name, test.name)
