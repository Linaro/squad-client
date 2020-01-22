#!/usr/bin/env python3
import os
import jinja2


from api import SquadApi
from models import Squad


#SquadApi.configure(url='https://qa-reports.linaro.org/', token=os.getenv('QA_REPORTS_TOKEN'))
SquadApi.configure(url='http://localhost:8000/', token=os.getenv('QA_REPORTS_TOKEN'))

group = Squad().group('lkft')
project = group.project('linux-stable-rc-4.14-oe-sanity')
build = project.build('v4.14.74')
#group = Squad().group('schneider')
#project = group.project('schneider')
#build = project.build('184')
testruns = build.testruns(completed=True).values()

for testrun in testruns:
    testrun.fill_metric_and_test_suites()
    for suite in testrun.test_suites:
        print('suite: %s on %s' % (suite.name, testrun.environment.slug))
        for test in suite.tests:
            print('* %s - %s' % (test.name, test.status))

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "schneider_template.html"
template = templateEnv.get_template(TEMPLATE_FILE)
outputText = template.render(group=group, project=project, build=build, testruns=testruns)
with open('schneider_generated_report.html', 'w') as reportFile:
    reportFile.write(outputText)
