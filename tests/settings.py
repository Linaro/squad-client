import os


from squad_client.settings import *  # noqa


tests_dir = os.path.dirname(os.path.abspath(__file__))


DEFAULT_SQUAD_PORT = 9000
DEFAULT_SQUAD_DATABASE_NAME = os.path.join(tests_dir, 'squad.sqlite3')
DEFAULT_SQUAD_DATABASE_CONFIG = 'ENGINE=django.db.backends.sqlite3:NAME=%s' % DEFAULT_SQUAD_DATABASE_NAME
