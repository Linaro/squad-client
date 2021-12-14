import json
import uuid
from itertools import groupby
from collections import OrderedDict


from .api import SquadApi, ApiException
from squad_client.exceptions import InvalidSquadObject, InvalidSquadLookup
from squad_client.utils import first, parse_test_name, parse_metric_name, to_json, get_class_name
from squad_client import settings
from squad_client import logging


logger = logging.getLogger(__name__)

DEFAULT_COUNT = settings.DEFAULT_NUM_OF_OBJECTS
ALL = -1


class SquadObjectException(Exception):
    pass


class SquadObjectJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, TestRunMetadata):
            d = {k: v for k, v in o.__dict__.items() if k != "id"}
            return d
        else:
            return json.JSONEncoder.default(self, o)


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
            if attr in result.keys():
                setattr(obj, attr.replace(' ', '_').replace('/', '_').replace('-', '_'), result[attr])

    def __fill__(self, klass, results):

        objects = {}
        for result in results:
            obj = klass()
            self.__fill_object__(result, obj)
            objects[obj.__id__] = obj

        return objects

    def __str__(self):
        class_name = get_class_name(self)
        attrs_str = []
        for attr in self.attrs:
            attrs_str.append('%s: "%s"' % (attr, getattr(self, attr) if hasattr(self, attr) else None))

        return '%s(%s)' % (class_name, ', '.join(attrs_str))

    def __fetch__(self, klass=None, filters=None, count=DEFAULT_COUNT, endpoint=None):
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
        url = endpoint or klass.endpoint
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

    def pre_save(self):
        pass

    def post_save(self):
        pass

    def save(self):
        self.pre_save()

        data = {}
        class_name = get_class_name(self)

        for attr in self.attrs:
            if not hasattr(self, attr):
                continue

            value = getattr(self, attr, None)
            if value is None:
                continue

            if isinstance(value, SquadObject):
                # value is a relation object
                if not hasattr(value, 'id'):
                    raise SquadObjectException('Failed to save %s: %s has no id' % (class_name, attr))
                # TODO: some objects have url as reference to other objects, ex:
                # project.group is a group url, instead of id
                # we need to standardize it
                # For now, only projects can be created this way
                data[attr] = value.url
            else:
                data[attr] = value

        endpoint = self.endpoint
        request = SquadApi.post
        if hasattr(self, 'id') and type(self.id) is not uuid.UUID:
            endpoint = '%s%s/' % (endpoint, self.id)
            request = SquadApi.patch

        try:
            response = request(endpoint, data=data)
            if response.status_code in [400, 401, 405]:
                raise SquadObjectException('Failed to save %s: %s' % (class_name, response.text))

            self.__fill_object__(response.json())
            self.post_save()

        except ApiException as e:
            logger.error(e)
            raise SquadObjectException(str(e))

    def delete(self):
        class_name = get_class_name(self)

        if not hasattr(self, 'id') or type(self.id) is uuid.UUID:
            raise SquadObjectException('Failed to delete %s: it must contain a valid "id"' % class_name)

        endpoint = '%s%s/' % (self.endpoint, self.id)

        try:
            response = SquadApi.delete(endpoint)
            if response.status_code in [400, 401, 405]:
                raise SquadObjectException('Failed to delete %s: %s' % (class_name, response.text))

        except ApiException as e:
            logger.error(e)
            raise SquadObjectException(str(e))


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

    def metrics(self, count=DEFAULT_COUNT, **filters):
        return self.__fetch__(Metric, filters, count)

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
            data['metadata'] = json.dumps(metadata, cls=SquadObjectJSONEncoder)
        if log:
            data['log'] = log

        logger.info('Submitting %i tests, %i metrics' % (num_tests, num_metrics))

        # TODO handle attachments
        response = SquadApi.post(path, data=data)
        status_code = response.status_code
        if status_code not in [200, 201, 500]:
            logger.error('Failed to submit results: %s' % response.text)
        return response.ok

    def submitjob(self, group=None, project=None, build=None, environment=None,
                  backend=None, definition=None):

        path = '/api/submitjob/%s/%s/%s/%s' % (group.slug, project.slug, build.version, environment.slug)

        data = {
            'backend': backend.name,
            'definition': definition,
        }

        logger.info('Submitting job request %s' % (path))

        response = SquadApi.post(path, data=data)
        status_code = response.status_code
        if status_code not in [200, 201, 500]:
            logger.error('Failed to submit job request: %s' % response.text)
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

    def create_project(self, slug=None, plugins_list=None):
        new_project = Project()
        new_project.slug = slug
        new_project.group = self
        new_project.enabled_plugins_list = plugins_list or ['linux-log-parser']
        new_project.save()

    def __repr__(self):
        return self.slug


class Project(SquadObject):

    endpoint = '/api/projects/'
    attrs = ['id', 'custom_email_template', 'data_retention_days', 'description',
             'enabled_plugins_list', 'full_name', 'group', 'html_mail', 'important_metadata_keys',
             'is_archived', 'is_public', 'moderate_notifications', 'name', 'notification_timeout',
             'slug', 'url', 'wait_before_notification']

    def builds(self, count=DEFAULT_COUNT, **filters):
        filters.update({'project': self.id})
        return self.__fetch__(Build, filters, count)

    def build(self, version):
        filters = {'version': version}
        objects = self.builds(count=1, **filters)
        return first(objects)

    def environments(self, count=DEFAULT_COUNT, **filters):
        filters.update({'project': self.id})
        return self.__fetch__(Environment, filters, count)

    def environment(self, slug):
        filters = {'slug': slug}
        objects = self.environments(count=1, **filters)
        return first(objects)

    def suites(self, count=DEFAULT_COUNT, **filters):
        filters.update({'project': self.id})
        return self.__fetch__(Suite, filters, count)

    def suite(self, suite_slug):
        filters = {'slug': suite_slug}
        objects = self.suites(count=1, **filters)
        return first(objects)

    def thresholds(self, count=DEFAULT_COUNT, **filters):
        filters.update({'project': self.id})
        return self.__fetch__(MetricThreshold, filters, count)

    def __repr__(self):
        return self.slug

    @staticmethod
    def compare_builds(baseline_id, build_id, by="tests", force=False):
        try:
            int(baseline_id)
            int(build_id)
        except ValueError:
            raise ValueError("IDs must be valid integers")
        baseline = Build(baseline_id)
        to_compare = Build(build_id)
        if baseline.id and to_compare.id:
            proj_id = baseline.project.split("/")[-2]
            if proj_id != to_compare.project.split("/")[-2]:
                raise InvalidSquadLookup("Argument builds must belong to same project")
            url = ''.join([Project.endpoint, str(proj_id), '/compare_builds'])
            params = {'baseline': baseline_id, 'to_compare': build_id, 'by': by}
            if force:
                params['force'] = '1'
            return SquadApi.get(url, params).json()

    def pre_save(self):
        self.attrs.append('project_settings')

        if not hasattr(self, 'enabled_plugins_list'):
            # TODO: make enabled_plugins_list optional
            self.enabled_plugins_list = ['linux-log-parser']


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

    __tests__ = {}

    def tests(self, count=ALL, **filters):
        filters['count'] = count
        filters_str = str(OrderedDict(filters))
        if self.__tests__.get(filters_str) is None:
            endpoint = '%s%d/tests/' % (self.endpoint, self.id)
            self.__tests__[filters_str] = self.__fetch__(Test, filters, count, endpoint=endpoint)
        return self.__tests__[filters_str]

    __metrics__ = {}

    def metrics(self, count=ALL, **filters):
        filters['count'] = count
        filters_str = str(OrderedDict(filters))
        if self.__metrics__.get(filters_str) is None:
            endpoint = '%s%d/metrics/' % (self.endpoint, self.id)
            self.__metrics__[filters_str] = self.__fetch__(Metric, filters, count, endpoint=endpoint)
        return self.__metrics__[filters_str]

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

    def submit(self):
        squad = Squad()
        return squad.submitjob(
            group=self.target.group,
            project=self.target,
            build=self.target_build,
            environment=self.environment,
            backend=self.backend,
            definition=self.definition,)


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
    endpoint = '/api/metrics/'
    attrs = ['url', 'id', 'name', 'short_name', 'measurement_list', 'result', 'unit', 'is_outlier', 'test_run', 'suite', 'metadata', 'build', 'environment']


class TestRunStatus(SquadObject):
    attrs = ['url', 'id', 'tests_pass', 'tests_fail', 'tests_xfail',
             'tests_skip', 'metrics_summary', 'has_metrics',
             'suite', 'suite_version']


class TestRunMetadata(SquadObject):
    pass


class TestRun(SquadObject):

    endpoint = '/api/testruns/'
    attrs = ['url', 'id', 'metadata_file', 'log_file',
             'created_at', 'completed', 'datetime', 'build_url',
             'job_id', 'job_status', 'job_url', 'resubmit_url',
             'data_processed', 'status_recorded', 'build',
             'environment']
    attachments = None
    log = None

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
            filters.update({'test_run': self.id})
            self.__metrics__ = self.__fetch__(Metric, filters, count)
        return self.__metrics__

    __metadata__ = None

    @property
    def metadata(self):
        if self.__metadata__ is None:
            response = SquadApi.get(self.metadata_file)

            if response.text == "None":
                self.__metadata__ = None
            else:
                objects = self.__fill__(TestRunMetadata, [response.json()])
                self.__metadata__ = first(objects)

        return self.__metadata__

    @metadata.setter
    def metadata(self, new_metadata):
        objects = self.__fill__(TestRunMetadata, [new_metadata])
        self.__metadata__ = first(objects)

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
        TestRunStatus.endpoint = '/'.join([TestRun.endpoint[:-1], str(self.id), 'status'])
        return self.__fetch__(TestRunStatus, filters, count)


class Test(SquadObject):

    endpoint = '/api/tests/'
    attrs = ['url', 'id', 'name', 'short_name', 'status', 'result', 'test_run', 'log', 'has_known_issues',
             'suite', 'known_issues', 'build', 'environment']

    def __repr__(self):
        return self.short_name


class Suite(SquadObject):

    endpoint = '/api/suites/'
    attrs = ['url', 'id', 'slug', 'name', 'project']

    __tests__ = None

    def add_test(self, test):
        if self.__tests__ is None:
            self.__tests__ = {}
        self.__tests__[test.__id__] = test

    def tests(self, count=ALL, **filters):
        if self.__tests__ is None and hasattr(self, 'id') and self.id is not None:
            endpoint = '%s%d/tests' % (self.endpoint, self.id)
            self.__tests__ = self.__fetch__(Test, filters, count, endpoint=endpoint)
        return self.__tests__

    def __repr__(self):
        return self.slug


class Environment(SquadObject):

    endpoint = '/api/environments/'
    attrs = ['url', 'id', 'slug', 'name', 'expected_test_runs', 'description', 'project']

    def __repr__(self):
        return self.slug


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
    attrs = ['url', 'id', 'name', 'suite', 'kind', 'description', 'instructions_to_reproduce']


class Annotation(SquadObject):

    endpoint = '/api/annotations/'
    attrs = ['url', 'id', 'description', 'build']


class MetricThreshold(SquadObject):

    endpoint = '/api/metricthresholds/'
    attrs = ['url', 'id', 'name', 'value', 'is_higher_better', 'environment', 'project']


class Report(SquadObject):

    endpoint = '/api/reports/'
    attrs = ['url', 'id', 'baseline', 'output_format', 'email_recipient', 'email_recipient_notified',
             'callback', 'callback_notified', 'data_retention_days', 'output_subject', 'output_text',
             'output_html', 'error_message', 'status_code', 'created_at', 'build', 'template']
