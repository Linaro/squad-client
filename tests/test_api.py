from http.client import HTTPMessage
from unittest import TestCase
from unittest.mock import ANY, Mock, patch, call

from . import settings
from squad_client.core.api import SquadApi, ApiException


class SquadApiTest(TestCase):

    def setUp(self):
        SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT)

    def test_unconfigured(self):
        with self.assertRaises(ApiException):
            SquadApi.configure(None)

    def test_malformed_url(self):
        with self.assertRaises(ApiException):
            SquadApi.configure('http:/malformed/url')

    def test_out_of_domain_object_url(self):
        with self.assertRaises(ApiException):
            SquadApi.get('http://some.other.url')

    def test_unauthorized_access(self):
        with self.assertRaises(ApiException):
            SquadApi.get('/my_group/my_private_project')

        SquadApi.configure(url='http://localhost:%s' % settings.DEFAULT_SQUAD_PORT, token='193cd8bb41ab9217714515954e8724f651ef8601')
        response = SquadApi.get('/my_group/my_private_project')
        self.assertTrue(response.ok)

        # reset config
        self.setUp()

    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_handle_retries(self, getconn_mock):
        getconn_mock.return_value.getresponse.side_effect = [
            Mock(status=500, msg=HTTPMessage()),
            Mock(status=429, msg=HTTPMessage()),
            Mock(status=200, msg=HTTPMessage()),
        ]

        r = SquadApi.get("http://localhost:%s/testme" % settings.DEFAULT_SQUAD_PORT)
        r.raise_for_status()

        self.assertEqual(getconn_mock.return_value.request.mock_calls, [
            call("GET", "/testme/", body=None, headers=ANY),
            call("GET", "/testme/", body=None, headers=ANY),
            call("GET", "/testme/", body=None, headers=ANY),
        ])
