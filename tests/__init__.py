import subprocess as sp
import os

from .squad_service import SquadService


def run(coverage=False, tests=['discover'], verbose=False):
    squad_service = SquadService()
    if not squad_service.start() or not squad_service.apply_fixtures('tests/fixtures.py'):
        print('Aborting tests!')
        return False

    argv = ['-m', 'unittest'] + tests

    if len(tests) == 0:
        argv += ['discover']

    if verbose:
        argv += ['-v']

    if coverage:
        print('\t --coverage is enabled, run `coverage report -m` to view coverage report')
        argv = ['coverage', 'run', '--source', 'squad_client'] + argv
    else:
        argv = ['python3'] + argv

    env = os.environ.copy()
    env['LOG_LEVEL'] = 'ERROR'
    proc = sp.Popen(argv, env=env)
    proc.wait()

    squad_service.stop()
    return proc.returncode == 0
