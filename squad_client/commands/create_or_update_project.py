import sys

from squad_client import logging
from squad_client.shortcuts import create_or_update_project
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger(__name__)


class CreateOrUpdateProjectCommand(SquadClientCommand):
    command = "create-or-update-project"
    help_text = "Create or update a project in SQUAD"

    def register(self, subparser):
        parser = super(CreateOrUpdateProjectCommand, self).register(subparser)
        parser.add_argument(
            "--group",
            help="SQUAD group where results are stored",
            required=True,
        )
        parser.add_argument(
            "--slug",
            help="SQUAD project slug",
            required=True,
        )
        parser.add_argument(
            "--name",
            help="Project name",
        )
        parser.add_argument(
            "--description",
            help="Project description",
        )
        parser.add_argument(
            '--settings',
            help="Project settings in yaml/json",
        )

        privacy = parser.add_mutually_exclusive_group()
        privacy.add_argument('--is-public', action='store_true', help='Project is public')
        privacy.add_argument('--is-private', action='store_true', help='Project is private')

        html_emails = parser.add_mutually_exclusive_group()
        html_emails.add_argument('--html-mail', action='store_true', help='Enable html emails')
        html_emails.add_argument('--no-html-mail', action='store_true', help='Disable html emails')

        moderate_notifications = parser.add_mutually_exclusive_group()
        moderate_notifications.add_argument('--moderate-notifications', action='store_true', help='Enable moderating notifications')
        moderate_notifications.add_argument('--no-moderate-notifications', action='store_true', help='Disable moderating notifications')

        parser.add_argument(
            "--email-template",
            help="Email template name to use, use SQUAD's default if none is given",
        )
        parser.add_argument(
            "--plugins",
            help="Plugins to enable separated by comma: [ ltp | linux-log-parser | tradefed ]",
            # TODO: auto-generate list of available plugins using squadplugins
        )
        parser.add_argument(
            "--important-metadata-keys",
            help="Important metadata keys separated by comma",
        )
        parser.add_argument(
            "--wait-before-notification-timeout",
            help="Wait this many seconds before sending notifications",
            type=int,
        )
        parser.add_argument(
            "--notification-timeout",
            help="Force sending build notifications after this many seconds",
            type=int,
        )
        parser.add_argument(
            "--data-retention",
            help="Delete builds older than this number of days. Set to 0 or any negative number to disable",
            type=int,
            default=0,
        )
        parser.add_argument(
            '--is-archived',
            action='store_true',
            default=False,
            help="Makes the project hidden from the group page by default",
        )
        parser.add_argument(
            '--no-overwrite',
            action='store_true',
            default=False,
            help="Command will fail if trying to update a project that already exists",
        )
        parser.add_argument(
            '--silent',
            action='store_true',
            default=False,
            help="Return with exit code only, do not print errors whatsoever",
        )
        parser.add_argument(
            "--thresholds",
            nargs="*",
            help='Metric thresholds of the project. Exaple "build/*-warnings"',
        )

    def resolve_boolean_flag(self, flag, no_flag):
        if flag:
            return True
        if no_flag:
            return False
        return None

    def run(self, args):
        is_public = self.resolve_boolean_flag(args.is_public, args.is_private)
        html_mail = self.resolve_boolean_flag(args.html_mail, args.no_html_mail)
        moderate_notifications = self.resolve_boolean_flag(args.moderate_notifications, args.no_moderate_notifications)
        plugins = args.plugins.split(',') if args.plugins else None
        important_metadata_keys = args.important_metadata_keys.split(',') if args.important_metadata_keys else None
        thresholds = args.thresholds

        project, errors = create_or_update_project(
            group_slug=args.group,
            slug=args.slug,
            name=args.name,
            settings=args.settings,
            is_public=is_public,
            html_mail=html_mail,
            is_archived=args.is_archived,
            description=args.description,
            plugins=plugins,
            data_retention=args.data_retention,
            notification_timeout=args.notification_timeout,
            moderate_notifications=moderate_notifications,
            important_metadata_keys=important_metadata_keys,
            wait_before_notification_timeout=args.wait_before_notification_timeout,
            overwrite=(not args.no_overwrite),
            thresholds=thresholds,
        )

        if project is None:
            if not args.silent:
                for error in errors:
                    print(error, file=sys.stderr)
            return False
        else:
            if not args.silent:
                print('Project saved: %s' % project.url)
                if len(errors):
                    print('But some errors were found: %s' % errors, file=sys.stderr)
                    return False
            return True
