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
Formatting for ``executions`` sub-commands.
"""

import os
import re
from StringIO import StringIO
from functools import partial

from . import (
    logger,
    color
)
from .env import env


FIELD_TYPE = 'field_type'
LEVEL = 'level'
TIMESTAMP = 'timestamp'
MESSAGE = 'message'
IMPLEMENTATION = 'implementation'
INPUTS = 'inputs'
TRACEBACK = 'traceback'
MARKER = 'marker'

FINAL_STATES = 'final_states'
SUCCESS_STATE = 'succeeded'
CANCEL_STATE = 'canceled'
FAIL_STATE = 'failed'

_EXECUTION_PATTERN = "\'.*\' workflow execution {0}".format
# In order to be able to format a string into this regex pattern, we need to provide support
# in adding this string into double curly brackets. This is an issue with python format, so we add
# this via format itself.
_FIELD_TYPE_PATTERN = partial('.*({starting}{0}{closing}).*'.format, starting='{', closing='.*?}')

_PATTERNS = {
    FINAL_STATES: {
        SUCCESS_STATE: re.compile(_EXECUTION_PATTERN(SUCCESS_STATE)),
        CANCEL_STATE: re.compile(_EXECUTION_PATTERN(CANCEL_STATE)),
        FAIL_STATE: re.compile(_EXECUTION_PATTERN(FAIL_STATE)),
    },
    FIELD_TYPE: {
        IMPLEMENTATION: re.compile(_FIELD_TYPE_PATTERN(IMPLEMENTATION)),
        LEVEL: re.compile(_FIELD_TYPE_PATTERN(LEVEL)),
        MESSAGE: re.compile(_FIELD_TYPE_PATTERN(MESSAGE)),
        INPUTS: re.compile(_FIELD_TYPE_PATTERN(INPUTS)),
        TIMESTAMP: re.compile(_FIELD_TYPE_PATTERN(TIMESTAMP))
    }
}

_FINAL_STATES = {
    SUCCESS_STATE: color.Colors.Fore.GREEN,
    CANCEL_STATE: color.Colors.Fore.YELLOW,
    FAIL_STATE: color.Colors.Fore.RED
}

_DEFAULT_COLORS = {
    LEVEL: {
        'default': {'fore': 'lightmagenta_ex'},
        'error': {'fore': 'red', 'style': 'bright'},
    },
    TIMESTAMP: {
        'default': {'fore': 'lightmagenta_ex'},
        'error': {'fore': 'red', 'style': 'bright'},
    },
    MESSAGE: {
        'default': {'fore': 'lightblue_ex'},
        'error': {'fore': 'red', 'style': 'bright'},
    },
    IMPLEMENTATION:{
        'default': {'fore': 'lightblack_ex'},
        'error': {'fore': 'red', 'style': 'bright'},
    },
    INPUTS: {
        'default': {'fore': 'blue'},
        'error': {'fore': 'red', 'style': 'bright'},
    },
    TRACEBACK: {'default': {'fore': 'red'}},

    MARKER: 'lightyellow_ex'
}

_DEFAULT_FORMATS = {
    logger.NO_VERBOSE: '{message}',
    logger.LOW_VERBOSE: '{timestamp:%H:%M:%S} | {level[0]} | {message}',
    logger.MEDIUM_VERBOSE: '{timestamp:%H:%M:%S} | {level[0]} | {implementation} | {message}',
    logger.HIGH_VERBOSE:
        '{timestamp:%H:%M:%S} | {level[0]} | {implementation} | {inputs} | {message}'
}


def stylize_log(item, mark_pattern):

    # implementation
    if item.task:
        # operation task
        implementation = item.task.function
        inputs = dict(arg.unwrapped for arg in item.task.arguments.values())
    else:
        # execution task
        implementation = item.execution.workflow_name
        inputs = dict(inp.unwrapped for inp in item.execution.inputs.values())

    stylized_str = color.StringStylizer(_get_format())
    _populate_level(stylized_str, item)
    _populate_timestamp(stylized_str, item)
    _populate_message(stylized_str, item, mark_pattern)
    _populate_inputs(stylized_str, inputs, item, mark_pattern)
    _populate_implementation(stylized_str, implementation, item, mark_pattern)

    msg = StringIO()
    msg.write(str(stylized_str))
    # Add the exception and the error msg.
    if item.traceback and env.logging.verbosity_level >= logger.MEDIUM_VERBOSE:
        msg.write(os.linesep)
        msg.writelines(_color_traceback('\t' + '|' + line, item, mark_pattern)
                       for line in item.traceback.splitlines(True))

    return msg.getvalue()


def log(item, mark_pattern=None, *args, **kwargs):
    leveled_log = getattr(env.logging.logger, item.level.lower())
    return leveled_log(stylize_log(item, mark_pattern), *args, **kwargs)


def log_list(iterator, mark_pattern=None):
    any_logs = False
    for item in iterator:
        log(item, mark_pattern)
        any_logs = True
    return any_logs


def _get_format():
    return (env.config.logging.execution.formats.get(env.logging.verbosity_level) or
            _DEFAULT_FORMATS.get(env.logging.verbosity_level))


def _get_styles(field_type):
    return env.config.logging.execution.colors[field_type]


def _is_color_enabled():
    # If styling is enabled and the current log_item isn't final string
    return env.config.logging.execution.colors_enabled


def _get_marker_schema():
    return color.ColorSpec(back=_get_styles(MARKER))


def _populate_implementation(str_, implementation, log_item, mark_pattern=None):
    _stylize(str_, implementation, log_item, IMPLEMENTATION, mark_pattern)


def _populate_inputs(str_, inputs, log_item, mark_pattern=None):
    _stylize(str_, inputs, log_item, INPUTS, mark_pattern)


def _populate_timestamp(str_, log_item):
    _stylize(str_, log_item.created_at, log_item, TIMESTAMP)


def _populate_message(str_, log_item, mark_pattern=None):
    _stylize(str_, log_item.msg, log_item, MESSAGE, mark_pattern)


def _populate_level(str_, log_item):
    _stylize(str_, log_item.level[0], log_item, LEVEL)


def _stylize(stylized_str, msg, log_item, msg_type, mark_pattern=None):
    match = re.match(_PATTERNS[FIELD_TYPE][msg_type], stylized_str._str)
    if not match:
        return
    matched_substr = match.group(1)

    substring = color.StringStylizer(matched_substr)

    # handle format
    substring.format(**{msg_type: msg})

    if _is_color_enabled():
        # handle color
        substring.color(_resolve_schema(msg_type, log_item))
        if not _is_end_execution_log(log_item):
            # handle highlighting
            substring.highlight(mark_pattern, _get_marker_schema())

    stylized_str.replace(matched_substr, substring)


def _color_traceback(traceback, log_item, mark_pattern):
    if _is_color_enabled():
        stylized_string = color.StringStylizer(traceback, _resolve_schema(TRACEBACK, log_item))
        stylized_string.highlight(mark_pattern, _get_marker_schema())
        return stylized_string
    return traceback


def _is_end_execution_log(log_item):
    return not log_item.task and bool(_end_execution_schema(log_item))


def _end_execution_schema(log_item):
    for state, pattern in _PATTERNS[FINAL_STATES].items():
        if re.match(pattern, log_item.msg):
            return _FINAL_STATES[state]


def _resolve_schema(msg_type, log_item):
    if _is_end_execution_log(log_item):
        return _end_execution_schema(log_item)
    else:
        return color.ColorSpec(
            **(
                # retrieve the schema from the user config according to the level
                _get_styles(msg_type).get(log_item.level.lower()) or
                # retrieve the default schema from the user config
                _get_styles(msg_type).get('default') or
                # retrieve the schema from the aria default config according to the level
                _DEFAULT_COLORS[msg_type].get(log_item.level.lower()) or
                # retrieve the default schema from the aria default config
                _DEFAULT_COLORS[msg_type].get('default')
            )
        )
