#!/usr/bin/env python3
import argparse
import jinja2
import sys
sys.path.append('..')

from itertools import groupby
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad, SquadObject, TestRun, ALL

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
group = Squad().group(args.group)
project = group.project(args.project)
build = project.build(args.build)

squad_envs = Squad().environments(project=project.id)
squad_suites = Squad().suites(project=project.id, count=-1)
envs = {}
envs_summaries = {}
testruns = {}
for env in squad_envs.values():
    suites = {}
    test_runs = set()
    envs.update({env.slug: suites})
    envs_summaries.update({env.slug: {'pass': 0, 'fail': 0, 'xfail': 0, 'skip': 0}})
    tests = Squad().tests(count=ALL, test_run__environment=env.id, test_run__build=build.id)
    metrics = Squad().metrics(count=ALL, test_run__environment=env.id, test_run__build=build.id)

    for test in tests.values():
        if test.test_run not in test_runs:
            test_runs.add(test.test_run)

        suite_name = squad_suites[test.suite].slug
        if suite_name in suites.keys():
            suites[suite_name].append(test)
        else:
            suites.update({suite_name: [test]})

    for metric in metrics.values():
        if metric.test_run not in test_runs:
            test_runs.add(metric.test_run)

        suite_name = squad_suites[metric.suite].slug
        if suite_name in suites.keys():
            suites[suite_name].append(metric)
        else:
            suites.update({suite_name: [metric]})

    for tr in test_runs:
        testrun = TestRun(tr)
        testrun_summary = testrun.summary()
        envs_summaries[env.slug]['pass'] += testrun_summary.tests_pass
        envs_summaries[env.slug]['fail'] += testrun_summary.tests_fail
        envs_summaries[env.slug]['xfail'] += testrun_summary.tests_xfail
        envs_summaries[env.slug]['skip'] += testrun_summary.tests_skip
        testruns[tr] = testrun.id

intro = None
if args.intro:
    with open(args.intro, 'r') as f:
        intro = f.read()

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
template = templateEnv.get_template(args.template)
outputText = template.render(group=group, project=project,
                             build=build, environments=envs,
                             intro=intro, server=args.server,
                             testruns=testruns, envs_summaries=envs_summaries)
with open(args.output, 'w') as reportFile:
    reportFile.write(outputText)
