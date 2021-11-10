from unittest import TestCase
import subprocess as sp


from tests import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad
from squad_client.utils import first


class CreateOrUpdateProjectTest(TestCase):
    def setUp(self):
        self.squad = Squad()

        self.testing_server = 'http://localhost:%s' % settings.DEFAULT_SQUAD_PORT
        self.testing_token = '193cd8bb41ab9217714515954e8724f651ef8601'
        SquadApi.configure(self.testing_server, self.testing_token)

        self.group = 'my_group'
        self.slug = 'create-project-via-cmdline'

    def manage_create_or_update_project(self, group=None, slug=None, name=None, description=None, settings=None, is_public=None, html_mail=None,
                                        moderate_notifications=None, is_archived=None, email_template=None,
                                        plugins=None, important_metadata_keys=None, wait_before_notification_timeout=None,
                                        notification_timeout=None, data_retention=None, no_overwrite=False, thresholds=None):
        argv = ['./manage.py', '--squad-host', self.testing_server, '--squad-token', self.testing_token,
                'create-or-update-project']

        if group:
            argv += ['--group', group]
        if slug:
            argv += ['--slug', slug]
        if name:
            argv += ['--name', name]
        if description:
            argv += ['--description', description]
        if settings:
            argv += ['--settings', settings]
        if is_public is not None:
            argv += ['--is-public'] if is_public else ['--is-private']
        if html_mail is not None:
            argv += ['--html-mail'] if html_mail else ['--no-html-mail']
        if moderate_notifications is not None:
            argv += ['--moderate-notifications'] if moderate_notifications else ['--no-moderate-notifications']
        if is_archived is not None and is_archived:
            argv += ['--is-archived']
        if email_template:
            argv += ['--email-template', email_template]
        if plugins and len(plugins):
            argv += ['--plugins', ','.join(plugins)]
        if important_metadata_keys and len(important_metadata_keys):
            argv += ['--important-metadata-keys', ','.join(important_metadata_keys)]
        if wait_before_notification_timeout is not None:
            argv += ['--wait-before-notification-timeout', str(wait_before_notification_timeout)]
        if notification_timeout is not None:
            argv += ['--notification-timeout', str(notification_timeout)]
        if data_retention is not None:
            argv += ['--data-retention', str(data_retention)]
        if no_overwrite:
            argv += ['--no-overwrite']
        if thresholds:
            argv += ['--thresholds'] + thresholds

        proc = sp.Popen(argv, stdout=sp.PIPE, stderr=sp.PIPE)
        proc.ok = False

        try:
            out, err = proc.communicate()
            proc.ok = (proc.returncode == 0)
        except sp.TimeoutExpired:
            self.logger.error('Running "%s" time out after %i seconds!' % ' '.join(argv))
            proc.kill()
            out, err = proc.communicate()

        proc.out = out.decode('utf-8')
        proc.err = err.decode('utf-8')
        return proc

    def test_empty(self):
        proc = self.manage_create_or_update_project()
        self.assertFalse(proc.ok)
        self.assertIn('the following arguments are required: --group, --slug', proc.err)

    def test_basics(self):
        proc = self.manage_create_or_update_project(group=self.group, slug=self.slug)
        self.assertTrue(proc.ok)

        project = first(self.squad.projects(group__slug=self.group, slug=self.slug))
        self.assertIsNotNone(project)
        self.assertIn('Project saved', proc.out)

    def test_no_overwrite(self):
        proc = self.manage_create_or_update_project(group=self.group, slug=self.slug)
        self.assertTrue(proc.ok)

        proc = self.manage_create_or_update_project(group=self.group, slug=self.slug, name='trying to edit', no_overwrite=True)
        self.assertFalse(proc.ok)
        self.assertIn('Project exists already', proc.err)

    def test_all_parameters(self):
        name = 'new name'
        description = 'project description'
        settings = '{"SETTING_KEY": "SETTING VALUE"}'
        is_public = True
        html_mail = False
        moderate_notifications = False
        is_archived = False
        plugins = ['linux-log-parser']
        important_metadata_keys = ['important-key-1', 'important key 2']
        wait_before_notification_timeout = 60
        notification_timeout = 120
        data_retention = 1
        thresholds = ["my-threshold"]

        proc = self.manage_create_or_update_project(
            group=self.group,
            slug=self.slug,
            name=name,
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
            thresholds=thresholds,
        )
        self.assertTrue(proc.ok)

        project = first(self.squad.projects(group__slug=self.group, slug=self.slug))
        self.assertIsNotNone(project)
        self.assertIn('Project saved', proc.out)
        self.assertIn('MetricThreshold saved', proc.out)

        self.assertEqual(description, project.description)
        self.assertEqual(settings, project.project_settings)
        self.assertEqual(is_public, project.is_public)
        self.assertEqual(html_mail, project.html_mail)
        self.assertEqual(moderate_notifications, project.moderate_notifications)
        self.assertEqual(is_archived, project.is_archived)
        self.assertEqual(plugins, project.enabled_plugins_list)
        self.assertEqual('\n'.join(important_metadata_keys), project.important_metadata_keys)
        self.assertEqual(wait_before_notification_timeout, project.wait_before_notification)
        self.assertEqual(notification_timeout, project.notification_timeout)
        self.assertEqual(data_retention, project.data_retention_days)
        self.assertEqual(1, len(project.thresholds().values()))
        threshold = first(project.thresholds())
        self.assertEqual(thresholds[0], threshold.name)
