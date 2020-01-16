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
    def get(endpoint, params):
        url = endpoint if SquadApi.url in endpoint else SquadApi.url + endpoint #cursor or base url
        logger.debug("GET %s (%s)" % (url, params))
        return requests.get(url=url, params=params)


class SquadBase:
    endpoint = None
    attrs = []

    def __fill__(self, klass, results):
        objects = []
        for result in results:
            obj = klass()
            for attr in klass.attrs:
                setattr(obj, attr, result[attr])
            objects.append(obj)

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

        objects = []
        url = klass.endpoint
        while url:
            response = SquadApi.get(url, filters)
            result = response.json()
            objects += self.__fill__(klass, result["results"])
            url = result["next"]
        return objects


class Squad(SquadBase):

    def groups(self, **filters):
        return self.__get__(Group, filters)

    def group(self, slug, **filters):
        filters.update({"slug": slug})
        objects = self.groups(**filters)
        return objects[0]


class Group(SquadBase):

    endpoint = "api/groups/"
    attrs = ["id", "url", "slug", "name", "description"]

    def projects(self, **filters):
        filters.update({"group": self.id})
        return self.__get__(Project, filters)

    def project(self, slug):
        filters = {"slug": slug}
        objects = self.projects(**filters)
        return objects[0]

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
        return self.__get__(Build, filters)

    def build(self, version):
        filters = {"version": version}
        objects = self.builds(**filters)
        return objects[0]

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
        "patch_baseline",
    ]

    def testruns(self, **filters):
        filters.update({"build": self.id})
        return self.__get__(TestRun, filters)

    def __repr__(self):
        return "%s" % self.version


class TestRun(SquadBase):

    endpoint = ""
