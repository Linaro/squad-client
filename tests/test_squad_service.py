from unittest import TestCase
import uuid


from .squad_service import SquadAdmin, SquadService


DB_NAME = str(uuid.uuid4())


class SquadServiceTest(TestCase):

    def setUp(self):
        self.squad_service = SquadService(port=9001)
        self.squad_service.squad_admin.env['DATABASE'] = 'ENGINE=django.db.backends.sqlite3:NAME=/tmp/%s.sqlite3' % DB_NAME

    def test_start(self):
        self.squad_service.start()
        self.assertTrue(self.squad_service.is_running())

        self.squad_service.stop()
        self.assertFalse(self.squad_service.is_running())

    def test_fixtures(self):
        self.squad_service.start()
        self.assertTrue(self.squad_service.is_running())

        ok = self.squad_service.apply_fixtures('tests/fixtures.py')
        self.assertTrue(ok)

        self.squad_service.stop()
        self.assertFalse(self.squad_service.is_running())


class SquadAdminTest(TestCase):

    def setUp(self):
        self.squad_admin = SquadAdmin()
        self.squad_admin.env['DATABASE'] = 'ENGINE=django.db.backends.sqlite3:NAME=/tmp/%s.sqlite3' % DB_NAME

    def tearDown(self):
        self.squad_admin.__truncate_database__()

    def test_migration(self):
        status = self.squad_admin.migrate()
        self.assertTrue(status.ok)

    def test_runserver(self):
        migrate_status = self.squad_admin.migrate()
        self.assertTrue(migrate_status.ok)

        service = self.squad_admin.runserver(port=9002)
        self.assertTrue(service.ok)

        service.kill()
        service.wait(timeout=5)

    def test_shell(self):
        migrate_status = self.squad_admin.migrate()
        self.assertTrue(migrate_status.ok)

        shell_status = self.squad_admin.shell(b'print(')
        self.assertFalse(shell_status.ok)

        shell_status = self.squad_admin.shell(b'print()')
        self.assertTrue(shell_status.ok)

        shell_status = self.squad_admin.shell(b'from squad.core.models import Group; Group.objects.create(slug="agroup")')
        self.assertTrue(shell_status.ok)
