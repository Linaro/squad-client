from collections import defaultdict

from .core.models import ALL, Squad, Group, Project, Build, Environment, Test, Metric, TestRun, SquadObjectException
from .utils import split_build_url, first, split_group_project_slug, getid


squad = Squad()


def compare_builds(baseline_id, build_id):
    return Project.compare_builds(baseline_id, build_id)


def retrieve_latest_builds(project_full_name, count=10):
    return squad.builds(count=count, project__full_name=project_full_name)


def retrieve_build_results(build_url):
    group_slug, project_slug, build_version = split_build_url(build_url)
    group = squad.group(group_slug)
    project = group.project(project_slug)
    environments = project.environments(count=ALL)
    suites = project.suites(count=ALL)
    build = project.build(build_version)

    if not build:
        return None

    results = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))

    tests = build.tests(fields='id,short_name,status,suite,environment').values()
    for test in tests:
        env = environments[getid(test.environment)]
        suite = suites[getid(test.suite)]
        results[env]['tests'][suite][test.short_name] = test.status

    metrics = squad.metrics(test_run__build_id=build.id, fields='id,short_name,result,suite,test_run').values()
    testruns = build.testruns(fields='id,environment')
    for metric in metrics:
        testrun = testruns[getid(metric.test_run)]
        env = environments[getid(testrun.environment)]
        suite = suites[getid(metric.suite)]
        results[env]['metrics'][suite][metric.short_name] = metric.results

    return results


def submit_results(group_project_slug=None, build_version=None, env_slug=None, tests={}, metrics={}, log=None, metadata=None, attachments=None):
    group_slug, project_slug = split_group_project_slug(group_project_slug)

    # TODO: validate input

    group = Group()
    project = Project()
    build = Build()
    testrun = TestRun()
    environment = Environment()

    group.slug = group_slug
    project.group = group
    project.slug = project_slug
    environment.slug = env_slug
    environment.project = project
    build.project = project
    build.version = build_version

    testrun.log = log
    testrun.build = build
    testrun.metadata = metadata
    testrun.attachments = attachments
    testrun.environment = environment

    for test_name in tests.keys():
        test = Test()
        test.name = test_name
        testrun.add_test(test)

        if type(tests[test_name]) is dict:
            test.status = tests[test_name].get('result')  # raise error if result is invalid
            test.log = tests[test_name].get('log')
        else:
            test.status = tests[test_name]

    for metric_name in metrics.keys():
        metric = Metric()
        metric.name = metric_name
        metric.result = metrics[metric_name]
        testrun.add_metric(metric)

    return testrun.submit_results()


def create_or_update_project(group_slug=None, slug=None, name=None, description=None, settings=None,
                             is_public=None, html_mail=None, moderate_notifications=None, is_archived=None,
                             email_template=None, plugins=None, important_metadata_keys=None,
                             wait_before_notification_timeout=None, notification_timeout=None,
                             data_retention=None, overwrite=False):
    errors = []
    group = None
    project = None

    if group_slug is None:
        errors.append('Group slug is required')
        return None, errors

    group = first(squad.groups(slug=group_slug))
    if group is None:
        errors.append('Group "%s" not found' % group_slug)
        return None, errors

    if slug is None:
        errors.append('Project slug is required')
        return None, errors

    project = group.project(slug)
    if project is not None:
        if not overwrite:
            errors.append('Project exists already')
            return None, errors
    else:
        project = Project()
        project.group = group
        project.slug = slug

    if name:
        project.name = name
    if plugins:
        project.enabled_plugins_list = plugins
    if settings:
        project.project_settings = settings
    if html_mail is not None:
        project.html_mail = html_mail
    if is_public is not None:
        project.is_public = is_public
    if is_archived is not None:
        project.is_archived = is_archived
    if description:
        project.description = description
    if data_retention is not None:
        project.data_retention_days = data_retention
    if notification_timeout is not None:
        project.notification_timeout = notification_timeout
    if moderate_notifications is not None:
        project.moderate_notifications = moderate_notifications
    if important_metadata_keys:
        project.important_metadata_keys = '\n'.join(important_metadata_keys) if type(important_metadata_keys) == list else important_metadata_keys
    if wait_before_notification_timeout is not None:
        project.wait_before_notification = wait_before_notification_timeout

    try:
        project.save()
    except SquadObjectException as e:
        errors.append(str(e))

    if len(errors):
        return None, errors
    return project, []
