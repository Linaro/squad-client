import os
import re
import sys
from setuptools import setup, find_packages


__version__ = None
exec(open('squad_client/version.py').read())


def valid_requirement(req):
    return not (re.match(r'^\s*$', req) or re.match('^#', req))


requirements_txt = open('requirements.txt').read().splitlines()
requirements = [req for req in requirements_txt if valid_requirement(req)]
if os.getenv('REQ_IGNORE_VERSIONS'):
    requirements = [req.split('>=')[0] for req in requirements]


if len(sys.argv) > 1 and sys.argv[1] in ['sdist', 'bdist', 'bdist_wheel'] and not os.getenv('SQUAD_CLIENT_RELEASE'):
    raise RuntimeError('Please use scripts/release to make releases!')

setup(
    name='squad-client',
    version=__version__,
    author='Charles Oliveira',
    author_email='charles.oliveira@linaro.org',
    url='https://github.com/Linaro/squad-client',
    packages=find_packages(exclude=['test*']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'squad-client=squad_client.manage:main',
        ]
    },
    install_requires=requirements,
    license='MIT',
    description="Client for SQUAD",
    long_description="Client for SQUAD",
    platforms='any',
    python_requires='>=3.6',
)
