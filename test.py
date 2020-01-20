#!/usr/bin/env python3

import unittest


from api import SquadApi
from models import (
    Squad,
    Group
)


SquadApi.configure(url='https://qa-reports.linaro.org')


class ModelsTest(unittest.TestCase):

    def setUp(self):
        self.squad = Squad()

    def test_groups(self):
        groups = self.squad.groups()
        self.assertTrue(True, len(groups))


if __name__ == '__main__':
    unittest.main()
