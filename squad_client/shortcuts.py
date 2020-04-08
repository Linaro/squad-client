from .core.models import Squad, Group, Project, Build, Environment, Test, Metric, TestRun
from .utils import split_build_url, first, split_group_project_slug


squad = Squad()


def retrieve_latest_builds(project_full_name, count=10):
    return squad.builds(count=count, project__full_name=project_full_name)


def retrieve_build_results(build_url):
    group_slug, project_slug, build_version = split_build_url(build_url)
    project_full_name = '%s/%s' % (group_slug, project_slug)
    builds = squad.builds(count=1, project__full_name=project_full_name, version=build_version)
    build = first(builds)

    if not build:
        return None

    results = {}
    testruns = build.testruns(bucket_suites=True)
    if len(testruns):
        for _id in testruns.keys():
            testrun = testruns[_id]
            test_suites = {}
            for suite in testrun.test_suites:
                test_suites[suite.name] = {t.short_name: t.status for t in suite.tests.values()}

            metric_suites = {}
            for suite in testrun.metric_suites:
                metric_suites[suite.name] = {m.name: m.result for m in suite.metrics.values()}

            results[testrun.environment.slug] = {'tests': test_suites, 'metrics': metric_suites}

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

    testrun.submit_results()
