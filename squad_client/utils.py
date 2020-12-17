import json
import re


def first(_dict):
    if _dict is None or len(_dict) == 0:
        return None
    return next(iter(_dict.values()))


def parse_test_name(name):
    suite_name, test_name = name.split('/', 1)
    return (suite_name, test_name)


def parse_metric_name(name):
    return parse_test_name(name)


def split_group_project_slug(group_project_slug):
    group_slug, project_slug = group_project_slug.split('/')
    return (group_slug, project_slug)


def split_build_url(build_slug):
    group_slug, project_slug, _, build_version = build_slug.split('/')
    return (group_slug, project_slug, build_version)


def to_json(thing):
    return json.dumps(thing)


def get_class_name(obj):
    return obj.__class__.__name__


def getid(url):
    matches = re.search(r'^.*/(\d+)/$', url)
    try:
        _id = int(matches.group(1))
        return _id
    except ValueError:
        return -1
