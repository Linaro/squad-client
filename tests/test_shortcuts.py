import logging
from unittest import TestCase


from . import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad
from squad_client.utils import first
from squad_client.shortcuts import (
    retrieve_latest_builds,
    retrieve_build_results,
    submit_results,
    submit_job,
    create_or_update_project,
)


class ShortcutsTest(TestCase):
    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(url="http://localhost:%s" % settings.DEFAULT_SQUAD_PORT)

    def test_retrieve_latest_builds(self):
        builds = retrieve_latest_builds("my_group/my_project", count=5)
        self.assertEqual(5, len(builds))

    def test_retrieve_build_results(self):
        results = retrieve_build_results("my_group/my_project/build/my_build")
        self.assertIsNotNone(results)


class SubmitResultsShortcutTest(TestCase):
    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(
            url="http://localhost:%s" % settings.DEFAULT_SQUAD_PORT,
            token="193cd8bb41ab9217714515954e8724f651ef8601",
        )

    def test_basic(self):
        metadata = {"job_id": "12345", "a-metadata-field": "value"}
        tests = {"testa": "pass", "testb": {"result": "pass", "log": "the log"}}
        metrics = {"metrica": 42}
        success = submit_results(
            group_project_slug="my_group/my_project",
            build_version="my_build",
            env_slug="my_env",
            tests=tests,
            metrics=metrics,
            metadata=metadata,
        )

        results = self.squad.tests(name="testa")
        self.assertTrue(len(results) > 0)
        self.assertTrue(success)

    def test_malformed_data(self):
        # job_id already exists
        metadata = {"job_id": "12345", "a-metadata-field": "value"}
        tests = {
            "test-malformed": "pass",
            "testb": {"result": "pass", "log": "the log"},
        }
        metrics = {"metrica": 42}

        with self.assertLogs(logger='squad_client.core.models', level=logging.ERROR) as cm:
            success = submit_results(
                group_project_slug="my_group/my_project",
                build_version="my_build",
                env_slug="my_env",
                tests=tests,
                metrics=metrics,
                metadata=metadata,
            )

            self.assertIn(
                'ERROR:squad_client.core.models:Failed to submit results: There is already a test run with job_id 12345',
                cm.output
            )

        results = self.squad.tests(name="test-malformed")
        self.assertTrue(len(results) == 0)
        self.assertFalse(success)


class SubmitJobShortcutTest(TestCase):
    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(
            url="http://localhost:%s" % settings.DEFAULT_SQUAD_PORT,
            token="193cd8bb41ab9217714515954e8724f651ef8601",
        )

    def test_basic(self):
        success = submit_job(
            group_project_slug="my_group/my_project",
            build_version="my_build",
            env_slug="my_submitted_env",
            backend_name="my_backend",
            definition="tests/data/dummy-definition.yaml",
        )

        self.assertTrue(success)
        results = self.squad.testjobs()
        self.assertTrue(len(results) > 0)

        for testjob in results.values():
            if testjob.environment == "my_submitted_env":
                return

        self.assertTrue(False)


class CreateOrUpdateShortcutTest(TestCase):
    def setUp(self):
        self.squad = Squad()
        SquadApi.configure(
            url="http://localhost:%s" % settings.DEFAULT_SQUAD_PORT,
            token="193cd8bb41ab9217714515954e8724f651ef8601",
        )

        self.group_slug = 'my_group'

    def assertEqualProjects(self, project1, project2):
        self.assertEqual(project1.id, project2.id)
        self.assertEqual(project1.name, project2.name)
        self.assertEqual(project1.description, project2.description)
        self.assertEqual(project1.is_public, project2.is_public)
        self.assertEqual(project1.html_mail, project2.html_mail)
        self.assertEqual(project1.moderate_notifications, project2.moderate_notifications)
        self.assertEqual(project1.is_archived, project2.is_archived)
        self.assertEqual(project1.enabled_plugins_list, project2.enabled_plugins_list)
        self.assertEqual(project1.important_metadata_keys, project2.important_metadata_keys)
        self.assertEqual(project1.wait_before_notification, project2.wait_before_notification)
        self.assertEqual(project1.notification_timeout, project2.notification_timeout)
        self.assertEqual(project1.data_retention_days, project2.data_retention_days)

    def test_minimum_parameters(self):
        project_slug = 'project-with-minimum-parameteres'
        project, errors = create_or_update_project(
            group_slug=self.group_slug,
            slug=project_slug,
        )

        self.assertIsNotNone(project)
        self.assertEqual(0, len(errors))

        check_project = first(self.squad.projects(group__slug=self.group_slug, slug=project_slug))
        self.assertEqual(check_project.id, project.id)

        project.delete()

    def test_all_parameters(self):
        project_slug = 'project-with-all-parameteres'
        project, errors = create_or_update_project(
            group_slug=self.group_slug,
            slug=project_slug,
            name='project name',
            description='project description',
            settings='{"SETTING_KEY": "SETTING VALUE"}',
            is_public=True,
            html_mail=False,
            moderate_notifications=False,
            is_archived=False,
            plugins=['linux-log-parser'],
            important_metadata_keys="important-key-1,important key 2",
            wait_before_notification_timeout=60,
            notification_timeout=120,
            data_retention=1,
        )

        self.assertIsNotNone(project)
        self.assertEqual(0, len(errors))

        check_project = first(self.squad.projects(group__slug=self.group_slug, slug=project_slug))
        self.assertEqualProjects(check_project, project)

        project.delete()

    def test_overwrite(self):
        project_slug = 'project-with-overwritten-data'
        project, errors = create_or_update_project(
            group_slug=self.group_slug,
            slug=project_slug,
            name='new name',
        )

        self.assertIsNotNone(project)
        self.assertEqual(0, len(errors))

        check_project = first(self.squad.projects(group__slug=self.group_slug, slug=project_slug))
        self.assertEqual(check_project.id, project.id)
        self.assertEqual(check_project.name, project.name)

        project_edited, errors = create_or_update_project(
            group_slug=self.group_slug,
            slug=project_slug,
            name='new name edited',
            overwrite=True,
        )

        self.assertIsNotNone(project_edited)
        self.assertEqual(0, len(errors))

        check_project = first(self.squad.projects(group__slug=self.group_slug, slug=project_slug))
        self.assertEqual(check_project.id, project_edited.id)
        self.assertEqual(check_project.name, project_edited.name)

        project_edited.delete()

    def test_overwrite_selected_fields_only(self):
        project_slug = 'project-with-overwritten-data-specific-fields-only'
        description = 'project description'
        settings = '{"SETTING_KEY": "SETTING VALUE"}'
        is_public = True
        html_mail = False
        moderate_notifications = False
        is_archived = False
        plugins = ['linux-log-parser']
        important_metadata_keys = 'important-key-1,important key 2'
        wait_before_notification_timeout = 60
        notification_timeout = 120
        data_retention = 1

        project, errors = create_or_update_project(
            group_slug=self.group_slug,
            slug=project_slug,
            name='new name',
            description=description,
            settings=settings,
            is_public=is_public,
            html_mail=html_mail,
            moderate_notifications=moderate_notifications,
            is_archived=is_archived,
            plugins=plugins,
            important_metadata_keys=important_metadata_keys,
            wait_before_notification_timeout=wait_before_notification_timeout,
            notification_timeout=notification_timeout,
            data_retention=data_retention,
        )

        self.assertIsNotNone(project)
        self.assertEqual(0, len(errors))

        check_project = first(self.squad.projects(group__slug=self.group_slug, slug=project_slug))
        self.assertEqualProjects(check_project, project)

        project_edited, errors = create_or_update_project(
            group_slug=self.group_slug,
            slug=project_slug,
            name='new name edited',
            overwrite=True,
        )

        self.assertIsNotNone(project_edited)
        self.assertEqual(0, len(errors))

        check_project = first(self.squad.projects(group__slug=self.group_slug, slug=project_slug))
        self.assertEqualProjects(check_project, project_edited)
        self.assertEqual(description, project_edited.description)
        self.assertEqual(is_public, project_edited.is_public)
        self.assertEqual(html_mail, project_edited.html_mail)
        self.assertEqual(moderate_notifications, project_edited.moderate_notifications)
        self.assertEqual(is_archived, project_edited.is_archived)
        self.assertEqual(plugins, project_edited.enabled_plugins_list)
        self.assertEqual(important_metadata_keys, project_edited.important_metadata_keys)
        self.assertEqual(wait_before_notification_timeout, project_edited.wait_before_notification)
        self.assertEqual(notification_timeout, project_edited.notification_timeout)
        self.assertEqual(data_retention, project_edited.data_retention_days)

        project_edited.delete()

    def test_no_overwrite(self):
        project_slug = 'project-without-overwritten-data'
        project, errors = create_or_update_project(
            group_slug=self.group_slug,
            slug=project_slug,
            name='new name',
        )

        self.assertIsNotNone(project)
        self.assertEqual(0, len(errors))

        check_project = first(self.squad.projects(group__slug=self.group_slug, slug=project_slug))
        self.assertEqual(check_project.id, project.id)
        self.assertEqual(check_project.name, project.name)

        project_edited, errors = create_or_update_project(
            group_slug=self.group_slug,
            slug=project_slug,
            name='new name edited',
            overwrite=False,
        )

        self.assertIsNone(project_edited)
        self.assertEqual(1, len(errors))
        self.assertEqual(['Project exists already'], errors)

        project.delete()
