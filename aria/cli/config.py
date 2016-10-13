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
CLI configuration
"""

import os
import logging
from getpass import getuser
from tempfile import gettempdir

from yaml import safe_load

from .storage import config_file_path

# path to a file where cli logs will be saved.
logging_filename = os.path.join(gettempdir(), 'aria_cli_{0}.log'.format(getuser()))
# loggers log level to show
logger_level = logging.INFO
# loggers log level to show
colors = True

import_resolver = None


def load_configurations():
    """
    Dynamically load attributes into the config module from the ``config.yaml`` defined in the user
    configuration directory
    """
    config_path = config_file_path()
    with open(config_path) as config_file:
        globals().update(safe_load(config_file) or {})
