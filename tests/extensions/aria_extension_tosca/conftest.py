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

"""
PyTest configuration module.

Add support for a "--tosca-parser" CLI option.

For more information on PyTest hooks, see the `PyTest documentation
<https://docs.pytest.org/en/latest/writing_plugins.html#pytest-hook-reference>`__.
"""

import pytest

from ...mechanisms.parsing.aria import AriaParser


def pytest_addoption(parser):
    parser.addoption('--tosca-parser', action='store', default='aria', help='TOSCA parser')


def pytest_report_header(config):
    tosca_parser = config.getoption('--tosca-parser')
    return 'tosca-parser: {0}'.format(tosca_parser)


@pytest.fixture(scope='session')
def parser(request):
    tosca_parser = request.config.getoption('--tosca-parser')
    verbose = request.config.getoption('verbose') > 0
    if tosca_parser == 'aria':
        with AriaParser() as p:
            p.verbose = verbose
            yield p
    else:
        pytest.fail('configured tosca-parser not supported: {0}'.format(tosca_parser))
