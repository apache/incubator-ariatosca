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

from mock import MagicMock

from ..mock import models as mock_models


def setup_logger(logger_name,
                 level=logging.INFO,
                 handlers=None,
                 remove_existing_handlers=True,
                 logger_format=None,
                 propagate=True):
    """
    :param logger_name: Name of the logger.
    :param level: Level for the logger (not for specific handler).
    :param handlers: An optional list of handlers (formatter will be
                     overridden); If None, only a StreamHandler for
                     sys.stdout will be used.
    :param remove_existing_handlers: Determines whether to remove existing
                                     handlers before adding new ones
    :param logger_format: the format this logger will have.
    :param propagate: propagate the message the parent logger.
    :return: A logger instance.
    :rtype: logging.Logger
    """

    logger = logging.getLogger(logger_name)

    if remove_existing_handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    for handler in handlers:
        if logger_format:
            formatter = logging.Formatter(fmt=logger_format)
            handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    if not propagate:
        logger.propagate = False

    return logger


class MockStorage(object):

    def __init__(self):
        self.type_definition = MockTypeDefinitionStorage()
        self.service_template = MockServiceTemplateStorage()
        self.service = MockServiceStorage()
        self.node_template = MockNodeTemplateStorage()
        self.node = MockNodeStorage()

class MockTypeDefinitionStorage(object):

    def __init__(self):
        self.td = mock_models.load_type_definition()
        self.list = MagicMock(return_value=[self.td])
        self.get = MagicMock(return_value=self.td)
        self._get_query = MagicMock()
        self.delete = MagicMock()

class MockServiceTemplateStorage(object):

    def __init__(self):
        self.list = MagicMock(return_value=[mock_models.create_service_template()])
        self.get_by_name = MagicMock(return_value=mock_models.create_service_template())


class MockServiceStorage(object):

    def __init__(self):

        self.s = mock_models.create_service_with_dependencies()

        self.list = MagicMock(return_value=[self.s])
        self.create = MagicMock(return_value=self.s)
        self.get = MagicMock(
            return_value=mock_models.create_service_with_dependencies(include_node=True))
        self.get_by_name = MagicMock(return_value=self.s)
        self.delete = MagicMock()


class MockNodeTemplateStorage(object):
    def __init__(self):
        self.get = MagicMock(return_value=mock_models.create_node_template_with_dependencies())
        self.list = MagicMock(return_value=[mock_models.create_node_template_with_dependencies()])


class MockNodeStorage(object):
    def __init__(self):
        self.get = MagicMock(return_value=mock_models.create_node_with_dependencies())
        self.list = MagicMock(return_value=[mock_models.create_node_with_dependencies()])
