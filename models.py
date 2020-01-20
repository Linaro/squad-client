import requests
import logging

logger = logging.getLogger("models")
logger.setLevel(logging.DEBUG)


class SquadApi:
    url = None
    token = None

    @staticmethod
    def configure(url=None, token=None):
        SquadApi.url = url if url[-1] is "/" else url + "/"
        SquadApi.token = token
        logger.debug(
            'SquadApi: url = "%s" and token = "%s"'
            % (SquadApi.url, "yes" if SquadApi.token else "no")
        )

    @staticmethod
    def get(endpoint, params, cursor=False):
        url = endpoint if SquadApi.url in endpoint else SquadApi.url + endpoint #cursor or base url
        logger.debug("GET %s (%s)" % (url, params))
        if cursor:
            params = None
        return requests.get(url=url, params=params)


class SquadBase:
    endpoint = None
    attrs = []

    def __fill__(self, klass, results):
        objects = {}
        for result in results:
            obj = klass()
            for attr in klass.attrs:
                setattr(obj, attr, result[attr])
            objects.update({result['id']: obj})

        return objects

    def __str__(self):
        class_name = self.__class__.__name__
        attrs_str = []
        for attr in self.attrs:
            attrs_str.append('%s: "%s"' % (attr, getattr(self, attr)))

        return "%s(%s)" % (class_name, ", ".join(attrs_str))

    def __get__(self, klass, filters):
        """
            Generic get method to retrieve objects from API
            how_many: number of objects to fetch, defaults to 50,
                      -1 means follow pagination
        """
        if klass.__name__ == "Metric":
            tr_id = filters.get("testrun_id", None)
            url = Metric.endpoint.format("/".join([TestRun.endpoint, str(self.id)]))
        else:
            url = klass.endpoint
        objects = {}
        limit = filters.get("limit", None)
        count = 0
        cursor = False
        while url:
            if limit and int(limit) != -1:
                if int(limit) == count:
                    break
            response = SquadApi.get(url, filters, cursor)
            result = response.json()
            if not result['results']:
                break
            count += len(result['results'])
            objects.update(self.__fill__(klass, result["results"]))
            url = result["next"]
            cursor = True
        return objects


class Squad(SquadBase):

    def groups(self, **filters):
        groups = self.__get__(Group, filters)
        return list(groups.values())[0] if len(groups) == 1 else groups


class Group(SquadBase):

    endpoint = "api/groups/"
    attrs = ["id", "url", "slug", "name", "description"]

    def projects(self, **filters):
        filters.update({"group": self.id})
        projects = self.__get__(Project, filters)
        return list(projects.values())[0] if len(projects) == 1 else projects

    def __repr__(self):
        return "%s" % self.slug


class Project(SquadBase):

    endpoint = "api/projects/"
    attrs = [
        "id",
        "custom_email_template",
        "data_retention_days",
        "description",
        "enabled_plugins_list",
        "full_name",
        "group",
        "html_mail",
        "important_metadata_keys",
        "is_archived",
        "is_public",
        "moderate_notifications",
        "name",
        "notification_timeout",
        "project_settings",
        "slug",
        "url",
        "wait_before_notification",
    ]

    def builds(self, **filters):
        filters.update({"project": self.id})
        builds = self.__get__(Build, filters)
        return list(builds.values())[0] if len(builds) == 1 else builds

    def __get__(self, klass, filters):
        builds = super().__get__(klass, filters)
        if builds:
            for build in builds:
                build = builds[build]
                result = SquadApi.get(build.status, None)
                status = result.json()
                setattr(build, 'has_metrics', status['has_metrics'])
                setattr(build, 'has_tests', status['has_tests'])
                setattr(build, 'approved', status['approved'])
                setattr(build, 'notified', status['notified'])
        return builds

    def __repr__(self):
        return "%s" % self.slug


class Build(SquadBase):

    endpoint = "/api/builds/"
    attrs = [
        "url",
        "id",
        "testjobs",
        "status",
        "metadata",
        "finished",
        "version",
        "created_at",
        "datetime",
        "patch_id",
        "keep_data",
        "project",
        "patch_source",
        "patch_baseline", #TODO add has_metrics and has_tests and milosz filters here
    ]

    def testruns(self, **filters):
        filters.update({"build": self.id})
        testruns = self.__get__(TestRun, filters)
        return list(testruns.values())[0] if len(testruns) == 1 else testruns

    def __fill__(self, klass, results):
        objects = {}
        attrs = results[0].keys()

        for result in results:
            obj = klass()
            for attr in attrs:
                setattr(obj, attr, result[attr])
            setattr(obj, 'has_metrics', self.has_metrics)
            setattr(obj, 'has_tests', self.has_tests)
            objects.update({result['id']: obj})
        return objects

    def __repr__(self):
        return "%s" % self.version


class TestRun(SquadBase):

    endpoint = "/api/testruns"

    def get_tests(self, **filters):
        filters.update({"test_run": self.id})
        return self.__get__(Test, filters)

    def get_metrics(self, **filters):
        if self.has_metrics:
            filters.update({"testrun_id": self.id})
            return self.__get__(Metric, filters)
        else:
            logger.debug("Testrun %s has no metrics" % self.id)
            print('No Metrics in this testrun')
        return

    def __fill__(self, klass, results):
        objects = {}
        if klass.__name__ == 'Test':
            attrs = ['suite_id', 'suite', 'name']
            attrs.extend(filter(lambda x: (x not in ['short_name', 'name', 'suite']), results[0].keys()))
            for result in results:
                obj = klass()
                for attr in attrs:
                    if attr == 'name':
                        setattr(obj, attr, result['short_name'])
                    elif attr == 'suite':
                        setattr(obj, attr, result['name'].rsplit('/', 1)[0])
                    elif attr == 'suite_id':
                        setattr(obj, attr, result['suite'])
                    else:
                        setattr(obj, attr, result[attr])
                objects.update({result['id']: obj})
        elif klass.__name__ == 'Metric':
            attrs = list()
            attrs.extend(filter(lambda x: (x not in ['name']), results[0].keys()))
            for result in results:
                obj = klass()
                for attr in attrs:
                    setattr(obj, attr, result[attr])
                setattr(obj, "name", result['name'].rsplit('/', 1)[1])
                setattr(obj, "suite", result['name'].rsplit('/', 1)[0])
                objects.update({result['metadata']: obj})
        return objects

    def __repr__(self):
        return "%s" % self.created_at


class Test(SquadBase):
    endpoint = "api/tests"

    def __repr__(self):
        return "%s:%s" % (self.id, self.name)


class Metric(SquadBase):
    endpoint = "{0}/metrics"

    def __repr__(self):
        return "%s:%s" % (self.metadata, self.name)



