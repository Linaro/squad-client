#!/usr/bin/env python3

import jinja2
import sys


sys.path.append('..')


from squad_client.core.api import SquadApi
from squad_client.core.models import Squad


# Configure SQUAD url
SquadApi.configure(url='https://qa-reports.linaro.org/')

# Generate a report with all groups
groups = Squad().groups()

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "example_template.html"
template = templateEnv.get_template(TEMPLATE_FILE)
outputText = template.render(groups=groups.values())
with open('generated_report.html', 'w') as reportFile:
    reportFile.write(outputText)
