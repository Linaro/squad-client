import os
import sys
import subprocess as sp
import time
import requests
import socket


from . import settings
from squad_client import logging

# Possible outcomes of running squad-admin process
OK = 0  # all good, exited with 0
TIMEOUT = 1  # as name says, squad-admin timed out
ERROR = 2  # squad-admin didn't time out but returned non-zero status


base_path = os.path.dirname(__file__)
squad_settings_file_path = os.path.join(base_path, 'squad_settings.py')


class SquadAdmin:
    def __init__(self, env={'DATABASE': settings.DEFAULT_SQUAD_DATABASE_CONFIG, 'SQUAD_EXTRA_SETTINGS': squad_settings_file_path, 'SQUAD_STORAGE_DIR': '/tmp/squad_storage'}):
        self.cmd = ['squad-admin']
        self.env = os.environ.copy()
        self.env.update(env)
        self.__truncate_database__()
        self.logger = logging.getLogger('squad-admin')
        self.daemons = []

    def __del__(self):
        if len(self.daemons):
            self.logger.info('Terminating daemons')

        for daemon in self.daemons:
            if daemon.poll() is None:
                daemon.kill()

    def __truncate_database__(self):
        if os.path.isfile(settings.DEFAULT_SQUAD_DATABASE_NAME):
            os.remove(settings.DEFAULT_SQUAD_DATABASE_NAME)

    def __run_process__(self, args, timeout=10, daemon=False, input=None, stdin=sp.DEVNULL, stdout=sp.DEVNULL, stderr=sp.DEVNULL):
        proc = sp.Popen(self.cmd + args, env=self.env, stdin=stdin, stdout=stdout, stderr=stderr)
        proc.ok = False

        if not daemon:
            try:
                proc.out, proc.err = proc.communicate(input=input, timeout=timeout)
                proc.ok = (proc.returncode == 0)
            except sp.TimeoutExpired:
                self.logger.error('Running "%s" time out after %i seconds!' % (' '.join(self.cmd + args), timeout))
                proc.kill()
                proc.out, proc.err = proc.communicate()
        else:
            self.daemons.append(proc)

        return proc

    def migrate(self):
        proc = self.__run_process__(['migrate'], stderr=sp.PIPE)
        if not proc.ok:
            self.logger.error('Failed to migrate!')
            print(proc.err.decode('utf-8'), file=sys.stderr)
        return proc

    def runserver(self, port=8000):
        # --noreload forces single threaded server. Ref: https://docs.djangoproject.com/en/dev/ref/django-admin/#cmdoption-runserver-noreload
        proc = self.__run_process__(['runserver', '--noreload', str(port)], daemon=True)

        attempts = 5
        while attempts > 0:
            attempts -= 1
            try:
                response = requests.get('http://localhost:%s' % str(port))
                if response.ok:
                    self.logger.debug('`squad-admin runserver` has started successfully!')
                    proc.ok = True
            except requests.exceptions.ConnectionError:
                self.logger.debug('Checking if `squad-admin runserver` is running... attempt %s' % str(attempts))
                time.sleep(1)

        if not proc.ok:
            self.logger.error('Failed to start `squad-admin runserver`!')
        return proc

    def shell(self, input=None):
        proc = self.__run_process__(['shell'], input=input, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        return proc


class SquadService:

    def __init__(self, port=settings.DEFAULT_SQUAD_PORT):
        self.port = port
        self.host = 'http://localhost:%s' % str(self.port)
        self.service = None
        self.squad_admin = SquadAdmin()
        self.logger = logging.getLogger('squad-service')

    def __del__(self):
        self.stop()

    def __port_in_use__(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', self.port)) == 0

    def start(self):
        self.logger.info('Starting a fresh squad instance on port %s' % self.port)

        if self.__port_in_use__():
            self.logger.error('... port already in use!')
            return False

        self.logger.info('Creating database schema')
        proc = self.squad_admin.migrate()
        if not proc.ok:
            return False

        self.service = self.squad_admin.runserver(port=self.port)
        if not self.service.ok:
            self.logger.error('Failed to start squad service "%s"' % self.service.stderr.read().decode())
            return False

        return True

    def is_running(self):
        return self.service is not None and self.service.poll() is None

    def apply_fixtures(self, fixtures_path):
        self.logger.info('Applying %s' % fixtures_path)

        with open(fixtures_path, 'rb') as f:
            fixtures_content = f.read()

        proc = self.squad_admin.shell(fixtures_content)
        if not proc.ok:
            error_message = proc.out + proc.err
            self.logger.error(error_message.decode())

        return proc.ok

    def stop(self):
        if self.is_running():
            self.logger.debug('Terminating Squad')
            self.service.kill()
            self.service.wait(timeout=5)
