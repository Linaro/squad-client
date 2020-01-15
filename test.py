#!/usr/bin/env python3

from models import *

SquadApi.configure(url='https://qa-reports.linaro.org')

squad = Squad()
groups = squad.groups()
for g in groups:
    print(g)

print(squad.group('lkft'))
