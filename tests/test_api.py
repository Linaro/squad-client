from unittest import TestCase


from squad_client.core.api import SquadApi, ApiException


def is_test_server_running():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    return result == 0


class SquadApiTest(TestCase):

    def setUp(self):
        SquadApi.configure(url='http://localhost:8000')

    def test_malformed_url(self):
        with self.assertRaises(ApiException):
            SquadApi.configure('http:/malformed/url')

    def test_out_of_domain_object_url(self):
        with self.assertRaises(ApiException):
            SquadApi.get('http://some.other.url')

    def test_server_response(self):
        # will require automatic test server to shutdown, for now, just to it by hand before running this test
        if not is_test_server_running():
            with self.assertRaises(ApiException):
                SquadApi.get('/api/groups')
        else:
            self.assertTrue(SquadApi.get('/api/groups') is not None)

