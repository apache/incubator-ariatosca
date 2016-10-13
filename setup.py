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

if (sys.version_info[0], sys.version_info[1]) not in _PYTHON_SUPPORTED_VERSIONS:
    raise NotImplementedError(
        '{0} Package support Python version 2.6 & 2.7 Only'.format(
            _PACKAGE_NAME))

version = '0.0.1'
execfile(os.path.join('.', _PACKAGE_NAME, 'VERSION.py'))


try:
    with open('./requirements.txt') as requirements:
        install_requires = [requirement.strip() for requirement in requirements.readlines()]
except IOError:
    install_requires = []

try:
    import importlib
except ImportError:
    install_requires.append('importlib')

setup(
    name=_PACKAGE_NAME,
    version=version,
    author='aria-core',
    author_email='cosmo-admin@gigaspaces.com',
    packages=find_packages(exclude=('*tests*',)),
    license='LICENSE',
    description='Aria Project',
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'aria = aria.cli.cli:main'
        ]
    }
)
