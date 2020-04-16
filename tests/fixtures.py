# This file is supposed to run in a squad instance for squad-client tests
#
# Some guidance to maintain this file:
#  - try to keep all values here
#  - do not delete any of the data anywhere (if deletion tests are needed, create one for the specific test)
#

from squad.core import models as m
from squad.core.tasks import RecordTestRunStatus
from squad.ci import models as mci

from rest_framework.authtoken.models import Token

user = m.User.objects.create(username='admin_user', is_superuser=True)
token = Token.objects.create(user=user, key='193cd8bb41ab9217714515954e8724f651ef8601')

group = m.Group.objects.create(slug='my_group')
group2 = m.Group.objects.create(slug='my_other_group')

project = group.projects.create(slug='my_project')
project_private = group.projects.create(slug='my_private_project', is_public=False)

build = project.builds.create(version='my_build')
build2 = project.builds.create(version='my_build2')
build3 = project.builds.create(version='my_build3')
build4 = project.builds.create(version='my_build4')
build5 = project.builds.create(version='my_build5')
build6 = project.builds.create(version='my_build6')

environment = project.environments.create(slug='my_env')
suite = project.suites.create(slug='my_suite')

testrun = build.test_runs.create(environment=environment)
passed_test = testrun.tests.create(suite=suite, result=True, name='my_passed_test')
failed_test = testrun.tests.create(suite=suite, result=False, name='my_failed_test')
xfailed_test = testrun.tests.create(suite=suite, result=True, name='my_xfailed_test', has_known_issues=True)
skipped_test = testrun.tests.create(suite=suite, result=None, name='my_skipped_test')

RecordTestRunStatus()(testrun)

backend = mci.Backend.objects.create()
testjob = testrun.test_jobs.create(backend=backend, target=project, target_build=build)

emailtemplate = m.EmailTemplate.objects.create(name='my_emailtemplate')
suitemetadata = m.SuiteMetadata.objects.create(name='my_suitemetadata')
metricthreshold = m.MetricThreshold.objects.create(environment=environment, value=42)
report = build.delayed_reports.create()
