#!/usr/bin/env python3
from datetime import datetime, timedelta
from models import *

SquadApi.configure(url='https://qa-reports.linaro.org')
created_at = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
squad = Squad()
trs = squad.groups(slug='lkft').projects(slug='linux-next-oe-sanity').builds(limit=1, status__has_metrics=True).testruns(limit=10)
metrics = []
for tr in trs:
    metric = trs[tr].get_metrics()
    if metric:
        metrics.append(metric)
pass

# groups = squad.groups()
# for g in groups:
#     print(g)
#
# print(squad.group('lkft'))
