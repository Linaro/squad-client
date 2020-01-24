#!/usr/bin/env python3
import os
import jinja2
import sys


sys.path.append('..')


from squad_client.api import SquadApi
from squad_client.models import Squad


SquadApi.configure(url='https://qa-reports.linaro.org/', token=os.getenv('QA_REPORTS_TOKEN'))
group = Squad().group('schneider')
project = group.project('schneider')
build = project.build('184')
testruns = build.testruns(bucket_suites=True, completed=True).values()

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "schneider_template.html"
template = templateEnv.get_template(TEMPLATE_FILE)
outputText = template.render(group=group, project=project, build=build, testruns=testruns)
with open('schneider_generated_report.html', 'w') as reportFile:
    reportFile.write(outputText)
