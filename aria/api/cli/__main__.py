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
CLI Entry point
"""

import logging

from aria import install_aria_extensions

from ...logger import (
    create_logger,
    create_console_log_handler,
    create_file_log_handler
)
from ..components import StdOutReceiver
from .args_parser import config_parser
from .components import AriaCliApi


__version__ = '0.1.0'


def _setup_loggers():
    create_logger(
        handlers=[
            create_console_log_handler(level=logging.WARN),
            create_file_log_handler(file_path='/tmp/aria_cli.log'),
        ],
        level=logging.INFO)


def main():
    """
    CLI entry point
    """
    install_aria_extensions()
    _setup_loggers()

    with AriaCliApi(StdOutReceiver(), config_parser()) as aria:
        aria.run()


if __name__ == '__main__':
    main()
