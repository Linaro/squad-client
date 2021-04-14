import unittest
import subprocess as sp
import os

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


class SubmitCommandTest(unittest.TestCase):

    testing_server = 'http://localhost:%s' % settings.DEFAULT_SQUAD_PORT
    testing_token = '193cd8bb41ab9217714515954e8724f651ef8601'

    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(url=self.testing_server, token=self.testing_token)

    def manage_submit(self, results=None, result_name=None, result_value=None, metrics=None,
                      metadata=None, attachments=None, logs=None, environment=None):
        argv = ['./manage.py', '--squad-host', self.testing_server, '--squad-token', self.testing_token,
                'submit', '--group', 'my_group', '--project', 'my_project', '--build', 'my_build6', '--environment', 'test_submit_env']

        if logs:
            argv += ['--logs', logs]
        if results:
            argv += ['--results', results]
        if metrics:
            argv += ['--metrics', metrics]
        if metadata:
            argv += ['--metadata', metadata]
        if attachments:
            argv += ['--attachments', attachments]
        if result_name:
            argv += ['--result-name', result_name]
        if result_value:
            argv += ['--result-value', result_value]

        env = os.environ.copy()
        env['LOG_LEVEL'] = 'INFO'
        proc = sp.Popen(argv, stdout=sp.PIPE, stderr=sp.PIPE, env=env)
        proc.ok = False

        try:
            out, err = proc.communicate()
            proc.ok = (proc.returncode == 0)
        except sp.TimeoutExpired:
            self.logger.error('Running "%s" time out after %i seconds!' % ' '.join(argv))
            proc.kill()
            out, err = proc.communicate()

        proc.out = out.decode('utf-8')
        proc.err = err.decode('utf-8')
        return proc

    def test_submit_empty(self):
        proc = self.manage_submit()
        self.assertFalse(proc.ok)
        self.assertIn('At least one of --result-name, --results, --metrics is required', proc.err)

    def test_submit_single_test(self):
        proc = self.manage_submit(result_name='single-test', result_value='pass')
        self.assertTrue(proc.ok)
        self.assertIn('1 tests', proc.err)

        test = first(self.squad.tests(name='single-test'))
        self.assertEqual('single-test', test.name)
        self.assertEqual('pass', test.status)

    def test_submit_invalid_result_value(self):
        proc = self.manage_submit(result_name='single-invalid-test', result_value='not-valid')
        self.assertFalse(proc.ok)
        self.assertIn("result-value: invalid choice: 'not-valid'", proc.err)

    def test_submit_results_json(self):
        proc = self.manage_submit(results='tests/submit_results/sample_results.json')
        self.assertTrue(proc.ok)
        self.assertIn('2 tests', proc.err)

        test = first(self.squad.tests(name='json-test-1'))
        self.assertEqual('json-test-1', test.name)
        self.assertEqual('pass', test.status)

        test = first(self.squad.tests(name='json-test-2'))
        self.assertEqual('json-test-2', test.name)
        self.assertEqual('fail', test.status)
        self.assertEqual('json-test-2 log', test.log)

    def test_submit_results_malformed_json(self):
        proc = self.manage_submit(results='tests/submit_results/sample_results_malformed.json')
        self.assertFalse(proc.ok)
        self.assertIn('Failed parsing file', proc.err)

    def test_submit_results_yaml(self):
        proc = self.manage_submit(results='tests/submit_results/sample_results.yaml')
        self.assertTrue(proc.ok)
        self.assertIn('2 tests', proc.err)

        test = first(self.squad.tests(name='yaml-test-1'))
        self.assertEqual('yaml-test-1', test.name)
        self.assertEqual('pass', test.status)

        test = first(self.squad.tests(name='yaml-test-2'))
        self.assertEqual('yaml-test-2', test.name)
        self.assertEqual('fail', test.status)
        self.assertEqual('yaml-test-2 log', test.log)

    def test_submit_results_malformed_yaml(self):
        proc = self.manage_submit(results='tests/submit_results/sample_results_malformed.yaml')
        self.assertFalse(proc.ok)
        self.assertIn('Failed parsing file', proc.err)

    def test_submit_results_bad_extension(self):
        p = "tests/submit_results/sample_results.txt"
        proc = self.manage_submit(results=p)
        self.assertFalse(proc.ok)
        self.assertIn('File "%s" does not have a JSON or YAML file extension' % p, proc.err)

    def test_submit_single_metric(self):
        proc = self.manage_submit(metrics='tests/submit_results/sample_metrics.json')
        self.assertTrue(proc.ok)
        self.assertIn('1 metrics', proc.err)

    def test_submit_everything(self):
        proc = self.manage_submit(results='tests/submit_results/sample_results.json',
                                  metrics='tests/submit_results/sample_metrics.json',
                                  metadata='tests/submit_results/sample_metadata.json',
                                  logs='tests/submit_results/sample_log.log')
        self.assertTrue(proc.ok, msg=proc.err)
        self.assertIn('2 tests, 1 metrics', proc.err)

        testrun = first(self.squad.testruns(job_id='jsonmetadatajobid1'))
        self.assertEqual('jsonmetadatajobid1', testrun.job_id)

        self.assertEqual(2, len(testrun.tests()))
        self.assertEqual(1, len(testrun.metrics()))
