from StringIO import StringIO
import logging

import pytest

import tests.cli.runner as runner
from tests.cli.utils import setup_logger, MockStorage


@pytest.fixture
def mock_storage():
    return MockStorage()


@pytest.mark.usefixtures("redirect_logger")
class TestCliBase(object):

    @staticmethod
    @pytest.fixture(scope="class")
    def redirect_logger():

        setup_logger(logger_name='aria.cli.main',
                     handlers=[logging.StreamHandler(TestCliBase._logger_output)],
                     logger_format='%(message)s')
        yield
        setup_logger(logger_name='aria.cli.main',
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
    assert expected_msg == str(outcome.exception)


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
