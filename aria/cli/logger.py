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
Centralized logging configuration and formatting.
"""

import os
import copy
import logging
from logutils import dictconfig

HIGH_VERBOSE = 3
MEDIUM_VERBOSE = 2
LOW_VERBOSE = 1
NO_VERBOSE = 0

LOGGER_CONFIG_TEMPLATE = {
    "version": 1,
    "formatters": {
        "file": {
            "format": "%(asctime)s [%(levelname)s] %(message)s"
        },
        "console": {
            "format": "%(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "file",
            "maxBytes": "5000000",
            "backupCount": "20"
        },
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "console"
        }
    },
    "disable_existing_loggers": False
}


class Logging(object):

    def __init__(self, config):
        self._log_file = None
        self._verbosity_level = NO_VERBOSE
        self._all_loggers_names = []
        self._configure_loggers(config)
        self._lgr = logging.getLogger('aria.cli.main')

    @property
    def logger(self):
        return self._lgr

    @property
    def log_file(self):
        return self._log_file

    @property
    def verbosity_level(self):
        return self._verbosity_level

    @verbosity_level.setter
    def verbosity_level(self, level):
        self._verbosity_level = level
        if self.is_high_verbose_level():
            for logger_name in self._all_loggers_names:
                logging.getLogger(logger_name).setLevel(logging.DEBUG)

    def is_high_verbose_level(self):
        return self.verbosity_level == HIGH_VERBOSE

    def _configure_loggers(self, config):
        loggers_config = config.logging.loggers
        logfile = config.logging.filename

        logger_dict = copy.deepcopy(LOGGER_CONFIG_TEMPLATE)
        if logfile:
            # set filename on file handler
            logger_dict['handlers']['file']['filename'] = logfile
            logfile_dir = os.path.dirname(logfile)
            if not os.path.exists(logfile_dir):
                os.makedirs(logfile_dir)
            self._log_file = logfile
        else:
            del logger_dict['handlers']['file']

        # add handlers to all loggers
        loggers = {}
        for logger_name in loggers_config:
            loggers[logger_name] = dict(handlers=list(logger_dict['handlers'].keys()))
            self._all_loggers_names.append(logger_name)
        logger_dict['loggers'] = loggers

        # set level for all loggers
        for logger_name, logging_level in loggers_config.iteritems():
            log = logging.getLogger(logger_name)
            level = logging._levelNames[logging_level.upper()]
            log.setLevel(level)

        dictconfig.dictConfig(logger_dict)


class ModelLogIterator(object):

    def __init__(self, model_storage, execution_id, filters=None, sort=None, offset=0):
        self._last_visited_id = offset
        self._model_storage = model_storage
        self._execution_id = execution_id
        self._additional_filters = filters or {}
        self._sort = sort or {}

    def __iter__(self):
        filters = dict(execution_fk=self._execution_id, id=dict(gt=self._last_visited_id))
        filters.update(self._additional_filters)

        for log in self._model_storage.log.iter(filters=filters, sort=self._sort):
            self._last_visited_id = log.id
            yield log
