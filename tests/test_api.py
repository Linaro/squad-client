from unittest import TestCase

from . import settings
from squad_client.core.api import SquadApi, ApiException


class SquadApiTest(TestCase):

    def setUp(self):
        SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT)

    def test_malformed_url(self):
        with self.assertRaises(ApiException):
            SquadApi.configure('http:/malformed/url')

    def test_out_of_domain_object_url(self):
        with self.assertRaises(ApiException):
            SquadApi.get('http://some.other.url')

    def test_unauthorized_access(self):
        response = SquadApi.get('/my_group/my_private_project')
        self.assertFalse(response.ok)

        SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT, token='193cd8bb41ab9217714515954e8724f651ef8601')
        response = SquadApi.get('/my_group/my_private_project')
        self.assertTrue(response.ok)

        # reset config
        self.setUp()
