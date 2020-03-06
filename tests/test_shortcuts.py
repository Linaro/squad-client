from unittest import TestCase


from squad_client.core.api import SquadApi
from squad_client.shortcuts import retrieve_latest_builds, retrieve_build_results


class ShortcutsTest(TestCase):

    def setUp(self):
        SquadApi.configure('http://localhost:8000')

    def test_retrieve_latest_builds(self):
        builds = retrieve_latest_builds('lkft/linux-stable-rc-4.14-oe', count=5)
        self.assertEqual(5, len(builds))

    def test_retrieve_build_results(self):
        results = retrieve_build_results('lkft/linux-stable-rc-4.14-oe-sanity/build/v4.14.74')
        self.assertIsNotNone(results)
