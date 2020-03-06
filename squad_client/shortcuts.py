from .core.models import Squad
from .utils import split_build_url, first

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
                test_suites[suite.name] = {t.short_name: t.status for t in suite.tests}

            metric_suites = {}
            for suite in testrun.metric_suites:
                metric_suites[suite.name] = {m.name: m.result for m in suite.metrics}

            results[testrun.environment.slug] = {'tests': test_suites, 'metrics': metric_suites}

    return results    
