from unittest import TestCase
from squad_client.utils import getid


class UtilsTest(TestCase):

    def test_getid(self):
        url = 'https://some-squad-url.com/api/objects/42/'
        self.assertEqual(42, getid(url))

    def test_getid_null_url(self):
        self.assertEqual(-1, getid(None))

    def test_getid_not_an_integer(self):
        url = 'https://some-squad-url.com/api/objects/not-an-integer/'
        self.assertEqual(-1, getid(url))
