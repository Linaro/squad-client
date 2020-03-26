from unittest import TestCase


from . import settings
from squad_client.core.api import SquadApi
from squad_client.shortcuts import retrieve_latest_builds, retrieve_build_results


class ShortcutsTest(TestCase):

    def setUp(self):
        SquadApi.configure('http://localhost:%s' % settings.DEFAULT_SQUAD_PORT)

    def test_retrieve_latest_builds(self):
        builds = retrieve_latest_builds('my_group/my_project', count=5)
        self.assertEqual(5, len(builds))

    def test_retrieve_build_results(self):
        results = retrieve_build_results('my_group/my_project/build/my_build')
        self.assertIsNotNone(results)
