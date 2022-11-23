import logging
import re
from collections import defaultdict

from .core.models import ALL, Squad, Group, Project, Build, Environment, Test, Metric, MetricThreshold, TestRun, TestJob, Backend, SquadObjectException
from .utils import split_build_url, first, split_group_project_slug, getid


squad = Squad()
logger = logging.getLogger(__name__)


def compare_builds(baseline_id, build_id, by="tests", force=False):
    return Project.compare_builds(baseline_id, build_id, by, force)


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

    metrics = build.metrics(fields='id,short_name,result,suite,environment').values()
    for metric in metrics:
        env = environments[getid(metric.environment)]
        suite = suites[getid(metric.suite)]
        results[env]['metrics'][suite][metric.short_name] = metric.result

    return results


def submit_results(group_project_slug=None, build_version=None, env_slug=None, tests={}, metrics={}, log=None, metadata={}, attachments=None):
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


def submit_job(group_project_slug=None, build_version=None, env_slug=None, backend_name=None, definition=None):
    group_slug, project_slug = split_group_project_slug(group_project_slug)

    group = Group()
    project = Project()
    build = Build()
    testjob = TestJob()
    environment = Environment()
    backend = Backend()

    group.slug = group_slug
    project.group = group
    project.slug = project_slug
    backend.name = backend_name
    environment.slug = env_slug
    build.version = build_version

    testjob.target_build = build
    testjob.target = project
    testjob.backend = backend
    testjob.definition = definition
    testjob.environment = environment

    return testjob.submit()


def create_or_update_project(group_slug=None, slug=None, name=None, description=None, settings=None,
                             is_public=None, html_mail=None, moderate_notifications=None, is_archived=None,
                             email_template=None, plugins=None, important_metadata_keys=None,
                             wait_before_notification_timeout=None, notification_timeout=None,
                             data_retention=None, overwrite=False, thresholds=None,
                             force_finishing_builds_on_timeout=None,
                             build_confidence_count=None, build_confidence_threshold=None):
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
    if force_finishing_builds_on_timeout is not None:
        project.force_finishing_builds_on_timeout = force_finishing_builds_on_timeout

    if build_confidence_count is not None:
        project.build_confidence_count = build_confidence_count
    if build_confidence_threshold is not None:
        project.build_confidence_threshold = build_confidence_threshold

    try:
        project.save()
    except SquadObjectException as e:
        errors.append(str(e))

    if len(errors):
        return None, errors

    # For now, this function only support project-wide, null-valued, lower-is-better metric thresholds
    if thresholds:
        project_thresholds = project.thresholds().values()
        existing_thresholds = [t.name for t in project_thresholds if [t.environment, t.value, t.is_higher_better] == [None, None, False]]
        for threshold in thresholds:
            if threshold in existing_thresholds:
                print('Threshold "%s" already exists, skip adding it' % threshold)
                continue

            # Create a metric threshold
            new_threshold = MetricThreshold()
            new_threshold.name = threshold
            new_threshold.project = project

            try:
                new_threshold.save()
                print('MetricThreshold saved: %s' % new_threshold.url)
            except SquadObjectException as e:
                errors.append(str(e))

    return project, errors


def watchjob(group_project_slug=None, build_version=None, env_slug=None, backend_name=None, testjob_id=None):
    group_slug, project_slug = split_group_project_slug(group_project_slug)

    group = Group()
    project = Project()
    build = Build()
    testjob = TestJob()
    environment = Environment()
    backend = Backend()

    group.slug = group_slug
    project.group = group
    project.slug = project_slug
    backend.name = backend_name
    environment.slug = env_slug
    build.version = build_version

    testjob.target_build = build
    testjob.target = project
    testjob.backend = backend
    testjob.job_id = testjob_id
    testjob.environment = environment

    return testjob.watch()


def get_build(build_version, project):
    """
        Any of the following formats are accepted for build_version
        - latest              latest build (finished or not)
        - latest+N            latest build (finished or not) "+N" is ignored
        - latest-N            latest Nth build (finished or not)
        - latest-finished     latest build that is finished
        - latest-finished+N   latest build that is finished "+N" is ignored
        - latest-finished-N   latest Nth build that is finished
        - v1.2.3              build that has version matching "v1.2.3"
        - v1.2.3+N            Nth build after "v1.2.3"
        - v1.2.3-N            Nth build prior to "v1.2.3"
    """

    # This regex HAS to match
    regex = r'^(.*?)([-+]\d+)?$'
    matches = re.search(regex, build_version)
    if matches is None:
        logger.error(f'Unknown behavior: {regex} is supposed to match any string > 0, including build version {build_version}')
        return None

    build_version = matches.group(1)
    nth_build = matches.group(2)
    logger.debug(f'Build version {build_version}, Nth build {nth_build}')

    # Filters that serve for all cases
    filters = {
        'count': 1,
        'ordering': '-1',
    }

    look_forward = False
    offset = None
    if nth_build is not None:
        # For previous Nth builds, offset is enough to handle it
        offset = int(nth_build[1:])
        look_forward = (nth_build[0] == '+')

    if build_version in ['latest', 'latest-finished']:
        if offset:
            filters['offset'] = offset

        if build_version == 'latest-finished':
            filters['status_finished'] = True

        logger.debug(f'Fetching {build_version} build with filters = {filters}')
        return first(project.builds(**filters))

    # User specified an actual build version
    filters['version'] = build_version

    logger.debug(f'Fetching {build_version} build with filters = {filters}')
    build = first(project.builds(**filters))
    if build is None or offset is None:
        return build

    # Check if user wants N forward or backward builds
    if look_forward:
        # Retrieving the Nth-forward build
        # my-build+5 (the 5th build that happened after "my-build")
        filters['id__gt'] = build.id
        filters['ordering'] = 'id'
    else:
        filters['id__lt'] = build.id

    # The 1 is because offset=0 is already the build right after/before the current one
    filters['offset'] = offset - 1

    # Reset version filter
    del filters['version']

    logger.debug(f'Fetching build with filters = {filters}')
    return first(project.builds(**filters))


def download_tests(project, build, filter_envs=None, filter_suites=None, format_string=None, output_filename=None):
    all_environments = project.environments(count=ALL)
    all_suites = project.suites(count=ALL)
    all_testruns = build.testruns(count=ALL, prefetch_metadata=True)

    filters = {
        'count': ALL,
        'fields': 'id,name,status,environment,suite,test_run,build',
    }

    envs = None
    if filter_envs:
        filters['environment__id__in'] = ','.join([str(e.id) for e in filter_envs])
        envs = ','.join([e.slug for e in filter_envs])

    suites = None
    if filter_suites:
        filters['suite__id__in'] = ','.join([str(s.id) for s in filter_suites])
        suites = ','.join([s.slug for s in filter_suites])

    filename = output_filename or f'{build.version}.txt'
    logger.info(f'Downloading test results for {project.slug}/{build.version}/{envs or "(all envs)"}/{suites or "(all suites)"} to {filename}')

    if format_string is None:
        format_string = '{test.environment.slug}/{test.name} {test.status}'

    tests = build.tests(**filters)
    output = []
    for test in tests.values():
        test.build = build
        test.environment = all_environments[getid(test.environment)]
        test.suite = all_suites[getid(test.suite)]
        test.test_run = all_testruns[getid(test.test_run)]
        output.append(format_string.format(test=test))

    output.sort()

    with open(filename, 'w') as fp:
        for line in output:
            fp.write(line + '\n')

    return True


def register_callback(group_slug=None, project_slug=None, build_version=None, url=None, record_response=False):

    errors = []

    group = squad.group(group_slug)
    if group is None:
        errors.append('Group "%s" not found' % group_slug)
        return False, errors

    project = group.project(project_slug)
    if project is None:
        errors.append('Project %s not found in %s' % (project_slug, group_slug))
        return False, errors

    build = project.build(build_version)
    if build is None:
        errors.append('Build %s not found in %s' % (build_version, project_slug))
        return False, errors

    return build.register_callback(url, record_response=record_response), errors
