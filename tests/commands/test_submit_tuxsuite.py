from unittest import TestCase
from unittest.mock import patch, Mock
import subprocess as sp


from tests import settings
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad
from squad_client.commands.submit_tuxsuite import SubmitTuxSuiteCommand


class SubmitTuxSuiteTest(TestCase):
    def setUp(self):
        self.squad = Squad()
        self.base_args = {
            'group': 'my_group',
            'project': 'my_project',
            'build': 'my_tuxsuite_build',
            'backend': 'my_tuxsuite_backend',
        }

        self.testing_server = 'http://localhost:%s' % settings.DEFAULT_SQUAD_PORT
        self.testing_token = '193cd8bb41ab9217714515954e8724f651ef8601'
        SquadApi.configure(self.testing_server, self.testing_token)

    def manage_submit_tuxsuite(self, group=None, project=None, build=None, backend=None, json_file=None, fetch_now=None):

        argv = ['./manage.py', '--squad-host', self.testing_server, '--squad-token', self.testing_token, 'submit-tuxsuite']
        if group:
            argv += ['--group', group]
        if project:
            argv += ['--project', project]
        if build:
            argv += ['--build', build]
        if backend:
            argv += ['--backend', backend]
        if json_file:
            argv += ['--json', json_file]
        if fetch_now:
            argv += ['--fetch-now']

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
        proc = self.manage_submit_tuxsuite()
        self.assertFalse(proc.ok)
        self.assertIn('the following arguments are required: --group, --project', proc.err)

    def test_basics(self):
        results = [
            'tests/data/sample_tuxsuite_builds.json',
            'tests/data/sample_tuxsuite_tests.json',
            'tests/data/sample_tuxsuite_tuxplan.json'
        ]

        for results_file in results:
            args = dict(list(self.base_args.items()) + [('json_file', results_file)])
            proc = self.manage_submit_tuxsuite(**args)
            self.assertTrue(proc.ok)

        job_ids = [
            'BUILD:linaro@lkft#2843VDPeVhg4yaTkgTur0T3ykmq',  # from sample_tuxsuite_builds.json
            'OEBUILD:linaro@lkft#2UGxUanGQ1QysqrOm4hn2xZ2U9n',  # from sample_tuxsuite_builds.json, but it's an oe build
            'TEST:linaro@lkft#1yPYGuuaUxuH42KrjEiokDrGRSQ',   # from sample_tuxsuite_tests.json
            'BUILD:linaro@lkft#1yPYDyGoF449fDc374OsaWJVVzl',  # both below from sample_tuxsuite_tuxplan.json
            'TEST:linaro@lkft#1yPYDsKqAtxplNqXIg6shMtrDvj',
        ]
        for job_id in job_ids:
            testjob = self.squad.testjobs(job_id=job_id)
            self.assertIsNotNone(testjob)

    @patch("squad_client.commands.submit_tuxsuite.watchjob")
    def test_fetch_now_disabled_by_default(self, watchjob_mock):
        args = Mock()
        for k, v in self.base_args.items():
            setattr(args, k, v)
        args.json = 'tests/data/sample_tuxsuite_tuxplan.json'
        args.fetch_now = False
        command = SubmitTuxSuiteCommand()
        command.run(args)

        watchjob_mock.assert_called_with(
            group_project_slug='%s/%s' % (self.base_args['group'], self.base_args['project']),
            build_version=self.base_args['build'],
            env_slug='qemu-i386',
            backend_name=self.base_args['backend'],
            testjob_id='TEST:linaro@lkft#1yPYGaOEPNwr2pCqBgONY43zORp',
            delay_fetch=True,
        )
