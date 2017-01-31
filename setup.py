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

version = '0.1.0'
execfile(os.path.join(root_dir, _PACKAGE_NAME, 'VERSION.py'))


try:
    with open(os.path.join(root_dir, 'requirements.txt')) as requirements:
        install_requires = [requirement.strip() for requirement in requirements.readlines()]
except IOError:
    install_requires = []


console_scripts = ['aria = aria.api.cli.__main__:main']
if os.environ.get('INSTALL_CTX'):
    console_scripts.append('ctx = aria.orchestrator.execution_plugin.ctx_proxy.client:main')


setup(
    name=_PACKAGE_NAME,
    version=version,
    description='ARIA',
    license='Apache License Version 2.0',
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
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration'],
    packages=find_packages(include=['aria*']) +
             find_packages(where=_EXTENSION_DIR,
                           include=['{0}*'.format(name) for name in _EXTENSION_NAMES]),
    package_dir=dict((name, '{0}/{1}'.format(_EXTENSION_DIR, name)) for name in _EXTENSION_NAMES),
    package_data={
        'aria_extension_tosca': [
            'profiles/tosca-simple-1.0/**',
            'profiles/tosca-simple-nfv-1.0/**'
        ]
    },
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        'console_scripts': console_scripts
    }
)
