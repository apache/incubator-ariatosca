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
Argument parsing configuration and functions
"""

import argparse
from functools import partial

from ..utils.argparse import ArgumentParser

NO_VERBOSE = 0


class SmartFormatter(argparse.HelpFormatter):
    """
    TODO: what is this?
    """
    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return super(SmartFormatter, self)._split_lines(text, width)


def sub_parser_decorator(func=None, **parser_settings):
    """
    Decorated for sub_parser argument definitions
    """
    if not func:
        return partial(sub_parser_decorator, **parser_settings)

    def _wrapper(parser):
        sub_parser = parser.add_parser(**parser_settings)
        sub_parser.add_argument(
            '-v', '--verbose',
            dest='verbosity',
            action='count',
            default=NO_VERBOSE,
            help='Set verbosity level (can be passed multiple times)')
        func(sub_parser)
        return sub_parser
    return _wrapper


def config_parser(parser=None):
    """
    Top level argparse configuration
    """
    parser = parser or ArgumentParser(
        prog='ARIA',
        description="ARIA's Command Line Interface",
        formatter_class=SmartFormatter)
    parser.add_argument('-v', '--version', action='version')
    sub_parser = parser.add_subparsers(title='Commands', dest='command')
    add_init_parser(sub_parser)
    add_execute_parser(sub_parser)
    add_parse_parser(sub_parser)
    add_spec_parser(sub_parser)
    return parser


@sub_parser_decorator(
    name='init',
    help='Initialize environment',
    formatter_class=SmartFormatter)
def add_init_parser(init):
    """
    ``init`` command parser configuration
    """
    init.add_argument(
        '-d', '--deployment-id',
        required=True,
        help='A unique ID for the deployment')
    init.add_argument(
        '-p', '--blueprint-path',
        dest='blueprint_path',
        required=True,
        help='The path to the desired blueprint')
    init.add_argument(
        '-i', '--inputs',
        dest='input',
        action='append',
        help='R|Inputs for the local workflow creation \n'
             '(Can be provided as wildcard based paths (*.yaml, etc..) to YAML files, \n'
             'a JSON string or as "key1=value1;key2=value2"). \n'
             'This argument can be used multiple times')
    init.add_argument(
        '-b', '--blueprint-id',
        dest='blueprint_id',
        required=True,
        help='The blueprint ID'
    )


@sub_parser_decorator(
    name='execute',
    help='Execute a workflow',
    formatter_class=SmartFormatter)
def add_execute_parser(execute):
    """
    ``execute`` command parser configuration
    """
    execute.add_argument(
        '-d', '--deployment-id',
        required=True,
        help='A unique ID for the deployment')
    execute.add_argument(
        '-w', '--workflow',
        dest='workflow_id',
        help='The workflow to execute')
    execute.add_argument(
        '-p', '--parameters',
        dest='parameters',
        action='append',
        help='R|Parameters for the workflow execution\n'
             '(Can be provided as wildcard based paths (*.yaml, etc..) to YAML files,\n'
             'a JSON string or as "key1=value1;key2=value2").\n'
             'This argument can be used multiple times.')
    execute.add_argument(
        '--task-retries',
        dest='task_retries',
        type=int,
        help='How many times should a task be retried in case of failure')
    execute.add_argument(
        '--task-retry-interval',
        dest='task_retry_interval',
        default=1,
        type=int,
        help='How many seconds to wait before each task is retried')


@sub_parser_decorator(
    name='parse',
    help='Parse a blueprint',
    formatter_class=SmartFormatter)
def add_parse_parser(parse):
    """
    ``parse`` command parser configuration
    """
    parse.add_argument(
        'uri',
        help='URI or file path to profile')
    parse.add_argument(
        'consumer',
        nargs='?',
        default='instance',
        help='consumer class name (full class path or short name)')
    parse.add_argument(
        '--loader-source',
        default='aria.parser.loading.DefaultLoaderSource',
        help='loader source class for the parser')
    parse.add_argument(
        '--reader-source',
        default='aria.parser.reading.DefaultReaderSource',
        help='reader source class for the parser')
    parse.add_argument(
        '--presenter-source',
        default='aria.parser.presentation.DefaultPresenterSource',
        help='presenter source class for the parser')
    parse.add_argument(
        '--presenter',
        help='force use of this presenter class in parser')
    parse.add_argument(
        '--prefix', nargs='*',
        help='prefixes for imports')
    parse.add_flag_argument(
        'debug',
        help_true='print debug info',
        help_false='don\'t print debug info')
    parse.add_flag_argument(
        'cached-methods',
        help_true='enable cached methods',
        help_false='disable cached methods',
        default=True)


@sub_parser_decorator(
    name='spec',
    help='Specification tool',
    formatter_class=SmartFormatter)
def add_spec_parser(spec):
    """
    ``spec`` command parser configuration
    """
    spec.add_argument(
        '--csv',
        action='store_true',
        help='output as CSV')
