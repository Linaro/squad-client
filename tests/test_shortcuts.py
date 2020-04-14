from unittest import TestCase


from . import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad
from squad_client.shortcuts import retrieve_latest_builds, retrieve_build_results, submit_results


class ShortcutsTest(TestCase):

    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT)

    def test_retrieve_latest_builds(self):
        builds = retrieve_latest_builds('my_group/my_project', count=5)
        self.assertEqual(5, len(builds))

    def test_retrieve_build_results(self):
        results = retrieve_build_results('my_group/my_project/build/my_build')
        self.assertIsNotNone(results)


class SubmitResultsShortcutTest(TestCase):

    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT, token='193cd8bb41ab9217714515954e8724f651ef8601')

    def test_basic(self):
        metadata = {'job_id': '12345', 'a-metadata-field': 'value'}
        tests = {'testa': 'pass', 'testb': {'result': 'pass', 'log': 'the log'}}
        metrics = {'metrica': 42}
        submit_results(group_project_slug='my_group/my_project', build_version='my_build',
                       env_slug='my_env', tests=tests, metrics=metrics, metadata=metadata)

        results = self.squad.tests(name='testa')
        self.assertTrue(len(results) > 0)

    def test_malformed_data(self):
        # job_id already exists
        metadata = {'job_id': '12345', 'a-metadata-field': 'value'}
        tests = {'test-malformed': 'pass', 'testb': {'result': 'pass', 'log': 'the log'}}
        metrics = {'metrica': 42}
        submit_results(group_project_slug='my_group/my_project', build_version='my_build',
                       env_slug='my_env', tests=tests, metrics=metrics, metadata=metadata)

        results = self.squad.tests(name='test-malformed')
        self.assertTrue(len(results) == 0)
