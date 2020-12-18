#!/usr/bin/env python3
import argparse
from collections import defaultdict
import jinja2
import sys
import re
sys.path.append('..')

from squad_client.core.api import SquadApi
from squad_client.core.models import Squad, SquadObject, ALL

parser = argparse.ArgumentParser()
parser.add_argument('--debug',
        action='store_true',
        dest='debug',
        help='display debug messages')
parser.add_argument('--group',
        dest='group',
        required=True,
        help='SQUAD group slug')
parser.add_argument('--project',
        dest='project',
        required=True,
        help='SQUAD project slug')
parser.add_argument('--build',
        dest='build',
        required=True,
        help='Build ID within a project')
parser.add_argument('--token',
        dest='token',
        required=True,
        help='SQUAD authorization token')
parser.add_argument('--template',
        dest='template',
        required=True,
        help='Rendering template')
parser.add_argument('--intro',
        dest='intro',
        required=False,
        default=None,
        help='Free form text or HTML to be added to template introduction')
parser.add_argument('--output',
        dest='output',
        required=True,
        help='Output filename')
parser.add_argument('--squad-host',
        dest='server',
        default='https://qa-reports.linaro.org/',
        help='SQUAD server')

args = parser.parse_args()

SquadApi.configure(url=args.server, token=args.token)

def getid(url):
    matches = re.search('^.*/(\d+)/$', url)
    try:
        _id = int(matches.group(1))
        return _id
    except ValueError:
        print('Could not get id for %s' % url)
        return -1

group = Squad().group(args.group)
project = group.project(args.project)
environments = project.environments(count=ALL)
suites = project.suites(count=ALL)
build = project.build(args.build)
testruns = build.testruns(fields='id,environment')
tests = build.tests(fields='id,short_name,status,environment,suite,test_run').values()
metrics = Squad().metrics(fields='id,short_name,result,test_run,suite', count=ALL, test_run__build=build.id).values()

env_summaries = {e.slug: {'pass': 0, 'fail': 0, 'xfail': 0, 'skip': 0} for e in environments.values()}
overall_summary = {'pass': 0, 'fail': 0, 'xfail': 0, 'skip': 0}
table = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for test in sorted(tests, key=lambda obj: obj.short_name):
    env = environments[getid(test.environment)].slug
    suite = suites[getid(test.suite)].slug
    table[env]['tests'][suite].append(test)

    env_summaries[env][test.status] += 1
    overall_summary[test.status] += 1

# Sort suites
for env in table.keys():
    __suites = table[env]['tests']
    table[env]['tests'] = {s: __suites[s] for s in sorted(__suites)}



# TODO: add build and env to metrics table as well
for metric in metrics:
    testrun = testruns[getid(metric.test_run)]
    env = environments[getid(testrun.environment)].slug
    suite = suites[getid(metric.suite)].slug

    table[env]['metrics'][suite].append(metric)

intro = None
if args.intro:
    with open(args.intro, 'r') as f:
        intro = f.read()

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader, trim_blocks=True, lstrip_blocks=True)
templateEnv.filters['getid'] = getid
template = templateEnv.get_template(args.template)
outputText = template.render(group=group, project=project, build=build,
                             intro=intro, server=args.server,
                             env_summaries=env_summaries, table=table)
with open(args.output, 'w') as reportFile:
    reportFile.write(outputText)
