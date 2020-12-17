from unittest import TestCase
from squad_client.utils import getid


class UtilsTest(TestCase):

    def test_getid(self):
        url = 'https://some-squad-url.com/api/objects/42/'
        self.assertEqual(42, getid(url))
