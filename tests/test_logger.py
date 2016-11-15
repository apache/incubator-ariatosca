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
import tempfile

from aria.logger import (create_logger,
                         create_console_log_handler,
                         create_file_log_handler,
                         _default_file_formatter,
                         LoggerMixin,
                         _DefaultConsoleFormat)

def test_create_logger():

    logger = create_logger()
    assert logger.name == 'aria'
    assert len(logger.handlers) == 0
    assert logger.level == logging.DEBUG

    custom_logger = logging.getLogger('custom_logger')
    handlers = [logging.FileHandler, logging.StreamHandler]
    logger = create_logger(logger=custom_logger, handlers=handlers, level=logging.INFO)
    assert custom_logger.name == 'custom_logger'
    assert logger.handlers == handlers
    assert logger.level == logging.INFO


def test_create_console_log_handler(capsys):

    debug_test_string = 'debug_create_console_test_string'
    info_test_string = 'info_create_console_test_string'

    # Default handler
    handler = create_console_log_handler()
    assert isinstance(handler, logging.StreamHandler)
    assert isinstance(handler.formatter, _DefaultConsoleFormat)
    assert handler.level == logging.DEBUG

    logger = create_logger(handlers=[handler])

    logger.info(info_test_string)
    logger.debug(debug_test_string)
    _, err = capsys.readouterr()
    assert err.count('DEBUG: {test_string}'.format(test_string=debug_test_string)) == 1
    assert err.count(info_test_string) == 1

    # Custom handler
    custom_handler = create_console_log_handler(level=logging.INFO, formatter=logging.Formatter())
    assert isinstance(custom_handler.formatter, logging.Formatter)
    assert custom_handler.level == logging.INFO

    logger = create_logger(handlers=[custom_handler])

    logger.info(info_test_string)
    _, err = capsys.readouterr()

    assert err.count(info_test_string) == 1


def test_create_file_log_handler():

    test_string = 'create_file_log_test_string'

    with tempfile.NamedTemporaryFile() as temp_file:
        handler = create_file_log_handler(file_path=temp_file.name)
        assert handler.baseFilename == temp_file.name
        assert handler.maxBytes == 5 * 1000 * 1024
        assert handler.backupCount == 10
        assert handler.stream is None
        assert handler.level == logging.DEBUG
        assert handler.formatter == _default_file_formatter

        logger = create_logger(handlers=[handler])
        logger.debug(test_string)
        assert test_string in temp_file.read()

    with tempfile.NamedTemporaryFile() as temp_file:
        handler = create_file_log_handler(
            file_path=temp_file.name,
            level=logging.INFO,
            max_bytes=1000,
            backup_count=2,
            formatter=logging.Formatter()
        )
        assert handler.baseFilename == temp_file.name
        assert handler.level == logging.INFO
        assert handler.maxBytes == 1000
        assert handler.backupCount == 2
        assert isinstance(handler.formatter, logging.Formatter)

        logger = create_logger(handlers=[handler])
        logger.info(test_string)
        assert test_string in temp_file.read()


def test_loggermixin(capsys):

    test_string = 'loggermixing_test_string'

    create_logger(handlers=[create_console_log_handler()])

    custom_class = type('CustomClass', (LoggerMixin,), {}).with_logger()
    custom_class.logger.debug(test_string)

    _, err = capsys.readouterr()
    assert test_string in err

    # TODO: figure out what up with pickle
    # class_pickled = pickle.dumps(custom_class)
    # class_unpickled = pickle.loads(class_pickled)
    #
    # assert vars(class_unpickled) == vars(custom_class)
