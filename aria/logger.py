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
Logging related mixins and functions
"""

import logging
from logging import handlers as logging_handlers
from datetime import datetime

_base_logger = logging.getLogger('aria')


class LoggerMixin(object):
    """
    Mixin Logger Class
    configuration (class members):
        logger_name: logger name [default: <class_name>]
        logger_level: logger level [default: logging.DEBUG]
        base_logger: This Mixing will create child logger from this base_logger
                    [default: root logger]
    """
    logger_name = None
    logger_level = logging.DEBUG

    def __init__(self, *args, **kwargs):
        self.logger_name = self.logger_name or self.__class__.__name__
        self.logger = logging.getLogger('{0}.{1}'.format(_base_logger.name, self.logger_name))
        self.logger.setLevel(self.logger_level)
        super(LoggerMixin, self).__init__(*args, **kwargs)

    @classmethod
    def with_logger(
            cls,
            logger_name=None,
            logger_level=logging.DEBUG,
            base_logger=logging.getLogger(),
            **kwargs):
        """
        Set the logger used by the consuming class
        """
        cls.logger_name = logger_name
        cls.logger_level = logger_level
        cls.base_logger = base_logger
        return cls(**kwargs)

    def __getstate__(self):
        obj_dict = vars(self).copy()
        del obj_dict['logger']
        return obj_dict

    def __setstate__(self, obj_dict):
        vars(self).update(
            logger=logging.getLogger('{0}.{1}'.format(_base_logger.name, obj_dict['logger_name'])),
            **obj_dict)


def create_logger(logger=_base_logger, handlers=(), **configs):
    """

    :param logging.Logger logger: The logger name [default: aria logger]
    :param list handlers: The logger handlers
    :param configs: The logger configurations
    :return: logger
    """
    logger.handlers = []
    for handler in handlers:
        logger.addHandler(handler)

    logger.setLevel(configs.get('level', logging.DEBUG))
    logger.debug('Logger {0} configured'.format(logger.name))
    return logger


def create_console_log_handler(level=logging.DEBUG, formatter=None):
    """

    :param level:
    :param formatter:
    :return:
    """
    console = logging.StreamHandler()
    console.setLevel(level)
    console.formatter = formatter or _DefaultConsoleFormat()
    return console


def create_sqla_log_handler(session, engine, log_cls, execution_id, level=logging.DEBUG):

    # This is needed since the engine and session are entirely new we need to reflect the db
    # schema of the logging model into the engine and session.
    log_cls.__table__.create(bind=engine, checkfirst=True)

    return _SQLAlchemyHandler(session=session,
                              engine=engine,
                              log_cls=log_cls,
                              execution_id=execution_id,
                              level=level)


class _DefaultConsoleFormat(logging.Formatter):
    """
    _DefaultConsoleFormat class
    Console logger formatter
     info level logs format: '%(message)s'
     every other log level are formatted: '%(levelname)s: %(message)s'
    """
    def format(self, record):
        try:
            if hasattr(record, 'prefix'):
                self._fmt = '<%(asctime)s: [%(levelname)s] @%(prefix)s> %(message)s'
            else:
                self._fmt = '<%(asctime)s: [%(levelname)s]> %(message)s'

        except AttributeError:
            return record.message
        return logging.Formatter.format(self, record)


def create_file_log_handler(
        file_path,
        level=logging.DEBUG,
        max_bytes=5 * 1000 * 1024,
        backup_count=10,
        formatter=None):
    """
    Create a logging.handlers.RotatingFileHandler
    """
    rotating_file = logging_handlers.RotatingFileHandler(
        filename=file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        delay=True,
    )
    rotating_file.setLevel(level)
    rotating_file.formatter = formatter or _default_file_formatter
    return rotating_file


class _SQLAlchemyHandler(logging.Handler):

    def __init__(self, session, engine, log_cls, execution_id, **kwargs):
        logging.Handler.__init__(self, **kwargs)
        self._session = session
        self._engine = engine
        self._cls = log_cls
        self._execution_id = execution_id

    def emit(self, record):
        created_at = datetime.strptime(logging.Formatter('%(asctime)s').formatTime(record),
                                       '%Y-%m-%d %H:%M:%S,%f')
        log = self._cls(
            execution_fk=self._execution_id,
            task_fk=record.task_id,
            actor=record.prefix,
            level=record.levelname,
            msg=str(record.msg),
            created_at=created_at,
        )
        self._session.add(log)

        try:
            self._session.commit()
        except BaseException:
            self._session.rollback()
            raise


_default_file_formatter = logging.Formatter(
    '%(asctime)s [%(name)s:%(levelname)s] %(message)s <%(pathname)s:%(lineno)d>')
