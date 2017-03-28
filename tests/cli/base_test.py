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

import logging
from StringIO import StringIO

import pytest

from . import runner
from . import utils


@pytest.fixture
def mock_storage():
    return utils.MockStorage()


@pytest.mark.usefixtures("redirect_logger")
class TestCliBase(object):

    @staticmethod
    @pytest.fixture(scope="class")
    def redirect_logger():

        utils.setup_logger(logger_name='aria.cli.main',
                           handlers=[logging.StreamHandler(TestCliBase._logger_output)],
                           logger_format='%(message)s')
        yield
        utils.setup_logger(logger_name='aria.cli.main',
                           handlers=_default_logger_config['handlers'],
                           level=_default_logger_config['level'])

    _logger_output = StringIO()

    def invoke(self, command):
        self._logger_output.truncate(0)
        return runner.invoke(command)

    @property
    def logger_output_string(self):
        return self._logger_output.getvalue()


def assert_exception_raised(outcome, expected_exception, expected_msg=''):
    assert isinstance(outcome.exception, expected_exception)
    assert expected_msg in str(outcome.exception)


# This exists as I wanted to mocked a function using monkeypatch to return a function that raises an
# exception. I tried doing that using a lambda in-place, but this can't be accomplished in a trivial
# way it seems. So I wrote this silly function instead
def raise_exception(exception, msg=''):

    def inner(*args, **kwargs):
        raise exception(msg)

    return inner


def get_default_logger_config():
    logger = logging.getLogger('aria.cli.main')
    return {'handlers': logger.handlers,
            'level': logger.level}

_default_logger_config = get_default_logger_config()
