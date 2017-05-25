#!/usr/bin/env python
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop


_PACKAGE_NAME = 'aria'
_PYTHON_SUPPORTED_VERSIONS = [(2, 6), (2, 7)]
_EXTENSION_DIR = 'extensions'
_EXTENSION_NAMES = [
    'aria_extension_tosca'
]

if (sys.version_info[0], sys.version_info[1]) not in _PYTHON_SUPPORTED_VERSIONS:
    raise NotImplementedError(
        '{0} Package support Python version 2.6 & 2.7 Only'.format(
            _PACKAGE_NAME))

root_dir = os.path.dirname(__file__)

with open(os.path.join(root_dir, 'VERSION')) as version_file:
    __version__ = version_file.read().strip()

install_requires = []
extras_require = {}

# We need to parse the requirements for the conditional dependencies to work for wheels and
# standard installation
try:
    with open(os.path.join(root_dir, 'requirements.in')) as requirements:
        for requirement in requirements.readlines():
            install_requires.append(requirement.strip())
        # We are using the install_requires mechanism in order to specify
        # conditional dependencies since reading them from a file in their
        # standard ';' from does silently nothing.
        extras_require = {":python_version<'2.7'": ['importlib',
                                                    'ordereddict',
                                                     'total-ordering',
                                                     ],
                          ":sys_platform=='win32'": 'pypiwin32'}
except IOError:
    install_requires = []
    extras_require = {}


console_scripts = ['aria = aria.cli.main:main']


def _generate_user_options(command):
    return command.user_options + [
        ('skip-ctx', None, 'Install with or without the ctx (Defaults to False)')
    ]


def _generate_boolean_options(command):
    return command.boolean_options + ['skip-ctx']


def _initialize_options(custom_cmd):
    custom_cmd.command.initialize_options(custom_cmd)
    custom_cmd.skip_ctx = False


def _run(custom_cmd):
    if custom_cmd.skip_ctx is False:
        console_scripts.append('ctx = aria.orchestrator.execution_plugin.ctx_proxy.client:main')
    custom_cmd.command.run(custom_cmd)


class InstallCommand(install):
    command = install

    user_options = _generate_user_options(install)
    boolean_options = _generate_boolean_options(install)
    initialize_options = _initialize_options
    run = _run


class DevelopCommand(develop):
    command = develop

    user_options = _generate_user_options(develop)
    boolean_options = _generate_boolean_options(develop)
    initialize_options = _initialize_options
    run = _run

setup(
    name=_PACKAGE_NAME,
    version=__version__,
    description='ARIA',
    license='Apache License 2.0',
    author='aria',
    author_email='dev@ariatosca.incubator.apache.org',
    url='http://ariatosca.org',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration'],
    packages=find_packages(include=['aria*']) +
             find_packages(where=_EXTENSION_DIR,
                           include=['{0}*'.format(name) for name in _EXTENSION_NAMES]),
    package_dir=dict((name, '{0}/{1}'.format(_EXTENSION_DIR, name)) for name in _EXTENSION_NAMES),
    package_data={
        'aria': [
            'cli/config/config_template.yaml'
        ],
        'aria_extension_tosca': [
            'profiles/tosca-simple-1.0/**',
            'profiles/tosca-simple-nfv-1.0/**',
            'profiles/aria-1.0/**'
        ]
    },
    platforms=['any'],
    zip_safe=False,
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        'console_scripts': console_scripts
    },
    cmdclass={
        'install': InstallCommand,      # used in pip install ...
        'develop': DevelopCommand       # used in pip install -e ...
    }
)
