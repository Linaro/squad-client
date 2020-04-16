import logging
import uuid
from itertools import groupby


from .api import SquadApi
from squad_client.exceptions import InvalidSquadObject
from squad_client.utils import first, parse_test_name, parse_metric_name, to_json
from squad_client import settings


logger = logging.getLogger()

DEFAULT_COUNT = settings.DEFAULT_NUM_OF_OBJECTS
ALL = -1


class SquadObject:
    endpoint = None
    attrs = []
    types = None

    def __init__(self, _id=None):
        if _id:
            self.endpoint += str(_id)
            self.__fetch__()

    @classmethod
    def get_type(cls, _type):
        if SquadObject.types is None:
            SquadObject.types = {c.__name__: c for c in SquadObject.__subclasses__() if c is not Squad}

        returned_type = SquadObject.types.get(_type)
        if returned_type is None:
            raise InvalidSquadObject('There is no SquadObject of type "%s"' % _type)

        return returned_type

    @property
    def __id__(self):
        if not hasattr(self, 'id'):
            setattr(self, 'id', None)

        if self.id is None:
            self.id = uuid.uuid1()

        return self.id

    def __fill_object__(self, result, obj=None):

        if obj is None:
            obj = self

        attrs = obj.attrs if len(obj.attrs) else [attr for attr in result.keys()]
        for attr in attrs:
            setattr(obj, attr.replace(' ', '_').replace('/', '_').replace('-', '_'), result[attr])

    def __fill__(self, klass, results):

        objects = {}
        for result in results:
            obj = klass()
            self.__fill_object__(result, obj)
            objects[obj.__id__] = obj

        return objects

    def __str__(self):
        class_name = self.__class__.__name__
        attrs_str = []
        for attr in self.attrs:
            attrs_str.append('%s: "%s"' % (attr, getattr(self, attr)))

        return '%s(%s)' % (class_name, ', '.join(attrs_str))

    def __fetch__(self, klass=None, filters=None, count=DEFAULT_COUNT):
        """
            Generic get method to retrieve objects from API
            count: number of objects to fetch, defaults to 50,
                      -1 (ALL) means follow pagination
        """

        if klass is None:
            response = SquadApi.get(self.endpoint)
            result = response.json()
            self.__fill_object__(result)
            return

        if count == ALL:
            count = settings.MAX_NUM_OF_OBJECTS

        filters['limit'] = count if count < settings.SQUAD_MAX_PAGE_LIMIT else settings.SQUAD_MAX_PAGE_LIMIT
        objects = {}
        url = klass.endpoint
        while url and len(objects) < count:
            response = SquadApi.get(url, filters)
            result = response.json()
            url = result['next']
            objects.update(self.__fill__(klass, result['results']))

        if len(objects) > settings.MAX_NUM_OF_OBJECTS:
            logger.warn('Maximum number of objects reached [%d]!' % len(objects))

        return objects

    def get(self, _id):
        count = 1
        result = self.__fetch__(self.__class__, {'id': _id}, count)
        return first(result) if len(result) else None


class Squad(SquadObject):

    def fetch(self, klass, count=ALL, **filters):
        return self.__fetch__(klass, filters, count)

    def groups(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Group, filters, count)

    def group(self, slug, **filters):
        filters.update({'slug': slug})
        objects = self.groups(count=1, **filters)
        return first(objects)

    def projects(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Project, filters, count)

    def builds(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Build, filters, count)

    def testjobs(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(TestJob, filters, count)

    def testruns(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(TestRun, filters, count)

    def tests(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Test, filters, count)

    def suites(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Suite, filters, count)

    def environments(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Environment, filters, count)

    def backends(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Backend, filters, count)

    def emailtemplates(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(EmailTemplate, filters, count)

    def knownissues(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(KnownIssue, filters, count)

    def suitemetadata(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(SuiteMetadata, filters, count)

    def annotations(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Annotation, filters, count)

    def metricthresholds(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(MetricThreshold, filters, count)

    def reports(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Report, filters, count)

    def submit(self, group=None, project=None, build=None, environment=None,
               tests=None, metrics=None, metadata=None, log=None, attachments=None):

        path = '/api/submit/%s/%s/%s/%s' % (group.slug, project.slug, build.version, environment.slug)
        num_tests = 0
        num_metrics = 0

        data = {}
        if tests:
            tests_dict = {}
            for test in tests.values():
                if hasattr(test, 'log') and test.log is not None and len(test.log):
                    value = {'log': test.log, 'result': test.status}
                else:
                    value = test.status
                tests_dict[test.name] = value
            num_tests = len(tests_dict)
            data['tests'] = to_json(tests_dict)
        if metrics:
            metrics_dict = {metric.name: metric.result for metric in metrics.values()}
            num_metrics = len(metrics_dict)
            data['metrics'] = to_json(metrics_dict)
        if metadata:
            data['metadata'] = to_json(metadata)
        if log:
            data['log'] = log

        logger.info('Submitting %i tests, %i metrics' % (num_tests, num_metrics))

        # TODO handle attachments
        response = SquadApi.post(path, data=data)
        status_code = response.status_code
        if status_code not in [200, 201, 500]:
            logger.error('Failed to submit results: %s' % response.text)
        return response.ok


class Group(SquadObject):

    endpoint = '/api/groups/'
    attrs = ['id', 'url', 'slug', 'name', 'description']

    def projects(self, count=DEFAULT_COUNT, **filters):
        filters.update({'group': self.id})
        return self.__fetch__(Project, filters, count)

    def project(self, slug):
        filters = {'slug': slug}
        objects = self.projects(count=1, **filters)
        return first(objects)

    def __repr__(self):
        return self.slug


class Project(SquadObject):

    endpoint = '/api/projects/'
    attrs = ['id', 'custom_email_template', 'data_retention_days', 'description',
             'enabled_plugins_list', 'full_name', 'group', 'html_mail', 'important_metadata_keys',
             'is_archived', 'is_public', 'moderate_notifications', 'name', 'notification_timeout',
             'project_settings', 'slug', 'url', 'wait_before_notification']

    def builds(self, count=DEFAULT_COUNT, **filters):
        filters.update({'project': self.id})
        return self.__fetch__(Build, filters, count)

    def build(self, version):
        filters = {'version': version}
        objects = self.builds(count=1, **filters)
        return first(objects)

    def __repr__(self):
        return self.slug


class Build(SquadObject):

    endpoint = '/api/builds/'
    attrs = ['url', 'id', 'testjobs', 'finished',
             'version', 'created_at', 'datetime', 'patch_id', 'keep_data', 'project',
             'patch_source', 'patch_baseline']

    def testruns(self, count=ALL, bucket_suites=False, **filters):
        filters.update({'build': self.id})
        testruns = self.__fetch__(TestRun, filters, count)

        if bucket_suites:
            for _id in testruns.keys():
                testruns[_id].bucket_metric_and_test_suites()

        return testruns

    __metadata__ = None
    __status__ = None

    @property
    def metadata(self):
        if self.__metadata__ is None:
            endpoint = '%s%d/metadata' % (self.endpoint, self.id)
            response = SquadApi.get(endpoint)
            objects = self.__fill__(BuildMetadata, [response.json()])
            self.__metadata__ = first(objects)
        return self.__metadata__

    @property
    def status(self):
        if self.__status__ is None:
            endpoint = '%s%d/status' % (self.endpoint, self.id)
            response = SquadApi.get(endpoint)
            objects = self.__fill__(BuildStatus, [response.json()])
            self.__status__ = first(objects)
        return self.__status__

    def __repr__(self):
        return self.version


class BuildMetadata(SquadObject):
    pass


class BuildStatus(SquadObject):
    pass


class TestJob(SquadObject):

    endpoint = '/api/testjobs/'
    attrs = ['url', 'external_url', 'definition', 'name', 'environment', 'created_at',
             'submitted_at', 'fetched_at', 'submitted', 'fetched', 'fetch_attempts',
             'last_fetch_attempt', 'failure', 'can_resubmit', 'resubmitted_count',
             'job_id', 'job_status', 'backend', 'testrun', 'target', 'target_build',
             'parent_job']


class MetricSuite:
    name = ''
    __metrics__ = {}

    def add_metric(self, metric):
        if self.__metric__ is None:
            self.__metric__ = {}
        self.__metrics__[metric.id] = metric

    @property
    def metrics(self):
        return self.__metrics__


class Metric(SquadObject):
    pass


class TestRunStatus(SquadObject):
    attrs = ['id', 'tests_pass', 'tests_fail', 'tests_xfail',
             'tests_skip', 'metrics_summary', 'has_metrics',
             'suite', 'suite_version']


class TestRun(SquadObject):

    endpoint = '/api/testruns/'
    attrs = ['url', 'id', 'metadata_file', 'log_file',
             'created_at', 'completed', 'datetime', 'build_url',
             'job_id', 'job_status', 'job_url', 'resubmit_url',
             'data_processed', 'status_recorded', 'build',
             'environment']
    metadata = None
    attachments = None
    log = None

    def __setattr__(self, attr, value):
        if attr == 'environment' and type(value) is str and value.startswith('http'):
            response = SquadApi.get(value)
            objs = self.__fill__(Environment, [response.json()])
            value = first(objs)
        super(TestRun, self).__setattr__(attr, value)

    __tests__ = None

    def add_test(self, test):
        if self.__tests__ is None:
            self.__tests__ = {}
        self.__tests__[test.__id__] = test

    def tests(self, count=ALL, **filters):
        if self.__tests__ is None and hasattr(self, 'id') and self.id is not None:
            filters.update({'test_run': self.id})
            self.__tests__ = self.__fetch__(Test, filters, count)
        return self.__tests__

    __metrics__ = None

    def add_metric(self, metric):
        if self.__metrics__ is None:
            self.__metrics__ = {}
        self.__metrics__[metric.__id__] = metric

    def metrics(self, count=ALL, **filters):
        if self.__metrics__ is None and hasattr(self, 'id') and self.id is not None:
            Metric.endpoint = '%s%d/metrics' % (self.endpoint, self.id)
            self.__metrics__ = self.__fetch__(Metric, filters, count)
        return self.__metrics__

    test_suites = []
    metric_suites = []

    def bucket_metric_and_test_suites(self):
        all_tests = self.tests()
        self.test_suites = []
        if len(all_tests):
            for suite_name, tests in groupby(sorted(all_tests.values(), key=lambda t: t.name), lambda t: parse_test_name(t.name)[0]):
                test_suite = Suite()
                test_suite.name = suite_name
                self.test_suites.append(test_suite)
                for test in tests:
                    test_suite.add_test(test)

        all_metrics = self.metrics()
        if len(all_metrics):
            self.metric_suites = []
            for suite_name, metrics in groupby(sorted(all_metrics.values(), key=lambda m: m.name), lambda m: parse_metric_name(m.name)[0]):
                metric_suite = MetricSuite()
                metric_suite.name = suite_name
                [metric_suite.add_metric(m) for m in metrics]
                self.metric_suites.append(metric_suite)

    def submit_results(self):
        squad = Squad()
        return squad.submit(
            group=self.build.project.group,
            project=self.build.project,
            build=self.build,
            environment=self.environment,
            tests=self.tests(),
            metrics=self.metrics(),
            metadata=self.metadata,
            log=self.log,
            attachments=self.attachments)

    __summary__ = None

    def summary(self):
        if self.__summary__ is None:
            self.__summary__ = first(self.statuses(suite__isnull=True))
        return self.__summary__

    def statuses(self, count=ALL, **filters):
        TestRunStatus.endpoint = '%s%d/status' % (self.endpoint, self.id)
        return self.__fetch__(TestRunStatus, filters, count)


class Test(SquadObject):

    endpoint = '/api/tests/'
    attrs = ['id', 'name', 'short_name', 'status', 'result', 'test_run', 'log', 'has_known_issues',
             'suite', 'known_issues']


class Suite(SquadObject):

    endpoint = '/api/suites/'
    attrs = ['id', 'slug', 'name', 'project']

    __tests__ = {}

    def add_test(self, test):
        if self.__tests__ is None:
            self.__tests__ = {}
        self.__tests__[test.id] = test

    @property
    def tests(self):
        return self.__tests__


class Environment(SquadObject):

    endpoint = '/api/environments/'
    attrs = ['url', 'id', 'slug', 'name', 'expected_test_runs', 'description', 'project']


class Backend(SquadObject):

    endpoint = '/api/backends/'
    attrs = ['id', 'name', 'url', 'username', 'implementation_type', 'backend_settings',
             'poll_interval', 'max_fetch_attempts', 'poll_enabled', 'listen_enabled']


class EmailTemplate(SquadObject):

    endpoint = '/api/emailtemplates/'
    attrs = ['url', 'id', 'name', 'subject', 'plain_text', 'html']


class KnownIssue(SquadObject):

    endpoint = '/api/knownissues/'
    attrs = ['url', 'id', 'title', 'test_name', 'notes', 'active', 'intermittent', 'environments']


class SuiteMetadata(SquadObject):

    endpoint = '/api/suitemetadata/'
    attrs = ['id', 'name', 'suite', 'kind', 'description', 'instructions_to_reproduce']


class Annotation(SquadObject):

    endpoint = '/api/annotations/'
    attrs = ['id', 'description', 'build']


class MetricThreshold(SquadObject):

    endpoint = '/api/metricthresholds/'
    attrs = ['url', 'id', 'name', 'value', 'is_higher_better', 'environment']


class Report(SquadObject):

    endpoint = '/api/reports/'
    attrs = ['url', 'id', 'baseline', 'output_format', 'email_recipient', 'email_recipient_notified',
             'callback', 'callback_notified', 'data_retention_days', 'output_subject', 'output_text',
             'output_html', 'error_message', 'status_code', 'created_at', 'build', 'template']
