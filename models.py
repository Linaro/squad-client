import logging
import uuid


from api import SquadApi
from utils import first
import settings


logger = logging.getLogger('models')
logger.setLevel(logging.DEBUG)

DEFAULT_COUNT = settings.DEFAULT_NUM_OF_OBJECTS


class SquadObject:
    endpoint = None
    attrs = []

    @property
    def __id__(self):
        return self.id if 'id' in self.attrs else uuid.uuid1()

    def __fill__(self, klass, results):
        objects = {}
        for result in results:
            obj = klass()
            for attr in klass.attrs:
                setattr(obj, attr, result[attr])
            objects[obj.__id__] = obj

        return objects

    def __str__(self):
        class_name = self.__class__.__name__
        attrs_str = []
        for attr in self.attrs:
            attrs_str.append('%s: "%s"' % (attr, getattr(self, attr)))

        return '%s(%s)' % (class_name, ', '.join(attrs_str))

    def __fetch__(self, klass, filters, count):
        """
            Generic get method to retrieve objects from API
            count: number of objects to fetch, defaults to 50,
                      -1 means follow pagination
        """

        if count == -1:
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
        result = self.__fetch__(self.__class__, {'id': _id}, 1)
        return first(result) if len(result) else None


class Squad(SquadObject):

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


class Group(SquadObject):

    endpoint = '/api/groups/'
    attrs = ['id', 'url', 'slug', 'name', 'description']

    def projects(self, count=DEFAULT_COUNT, **filters):
        filters.update({'group': self.id})
        self.__fetch__(Project, filters, count)

    def project(self, slug):
        filters = {'slug': slug}
        objects = self.projects(**filters)
        return objects[0]


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
        objects = self.builds(**filters)
        return objects[0]


class Build(SquadObject):

    endpoint = '/api/builds/'
    attrs = ['url', 'id', 'testjobs', 'status', 'metadata', 'finished',
             'version', 'created_at', 'datetime', 'patch_id', 'keep_data', 'project',
             'patch_source', 'patch_baseline']

    def testruns(self, count=DEFAULT_COUNT, **filters):
        filters.update({'build': self.id})
        return self.__fetch__(TestRun, filters, count)


class TestJob(SquadObject):

    endpoint = '/api/testjobs/'
    attrs = ['url', 'external_url', 'definition', 'name', 'environment', 'created_at',
             'submitted_at', 'fetched_at', 'submitted', 'fetched', 'fetch_attempts',
             'last_fetch_attempt', 'failure', 'can_resubmit', 'resubmitted_count',
             'job_id', 'job_status', 'backend', 'testrun', 'target', 'target_build',
             'parent_job']


class TestRun(SquadObject):

    endpoint = '/api/testruns/'
    attrs = ['url', 'id', 'tests_file', 'metrics_file', 'metadata_file', 'log_file',
             'tests', 'metrics', 'created_at', 'completed', 'datetime', 'build_url',
             'job_id', 'job_status', 'job_url', 'resubmit_url', 'data_processed',
             'status_recorded', 'build', 'environment']


class Test(SquadObject):

    endpoint = '/api/tests/'
    attrs = ['id', 'name', 'short_name', 'status', 'result', 'log', 'has_known_issues',
             'suite', 'known_issues']


class Suite(SquadObject):

    endpoint = '/api/suites/'
    attrs = ['id', 'slug', 'name', 'project']


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
    attrs = ['url', 'id', 'name', 'value', 'is_higher_better', 'project']


class Report(SquadObject):

    endpoint = '/api/reports/'
    attrs = ['url', 'id', 'baseline', 'output_format', 'email_recipient', 'email_recipient_notified',
             'callback', 'callback_notified', 'data_retention_days', 'output_subject', 'output_text',
             'output_html', 'error_message', 'status_code', 'created_at', 'build', 'template']
