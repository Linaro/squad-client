#!/usr/bin/env python3
import argparse
import jinja2
import sys
sys.path.append('..')

from itertools import groupby
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
parser.add_argument('--qa-reports',
        dest='server',
        default='https://qa-reports.linaro.org/',
        help='SQUAD authorization token')

args = parser.parse_args()

SquadApi.configure(url=args.server, token=args.token)
group = Squad().group(args.group)
project = group.project(args.project)
build = project.build(args.build)

squad_envs = Squad().environments(project=project.id)
squad_suites = Squad().suites(project=project.id)
envs = {}

for env in squad_envs.values():
    suites = {}
    envs.update({env.slug: suites})
    tests = Squad().tests(count=ALL, test_run__environment=env.id, test_run__build=build.id)
    # group tests by suite
    for test in tests.values():
        suite_name = squad_suites[test.suite].slug
        if suite_name in suites.keys():
            suites[suite_name].append(test)
        else:
            suites.update({suite_name: [test]})

intro = None
if args.intro:
    with open(args.intro, 'r') as f:
        intro = f.read()

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
template = templateEnv.get_template(args.template)
outputText = template.render(group=group, project=project, build=build, environments=envs, intro=intro)
with open(args.output, 'w') as reportFile:
    reportFile.write(outputText)
