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

from StringIO import StringIO

from . import logger
from .env import env

DEFAULT_FORMATTING = {
    logger.NO_VERBOSE: {'message': '{item.msg}'},
    logger.LOW_VERBOSE: {
        'message': '{timestamp} | {item.level[0]} | {item.msg}',
        'timestamp': '%H:%M:%S'
    },
    logger.MEDIUM_VERBOSE: {
        'message': '{timestamp} | {item.level[0]} | {implementation} | {item.msg} ',
        'timestamp': '%H:%M:%S'
    },
    logger.HIGH_VERBOSE: {
        'message': '{timestamp} | {item.level[0]} | {implementation}({inputs}) | {item.msg} ',
        'timestamp': '%H:%M:%S'
    },
}


def _str(item, formats=None):
    # If no formats are passed we revert to the default formats (per level)
    formats = formats or {}
    formatting = formats.get(env.logging.verbosity_level,
                             DEFAULT_FORMATTING[env.logging.verbosity_level])
    msg = StringIO()

    formatting_kwargs = dict(item=item)

    if item.task:
        formatting_kwargs['implementation'] = item.task.implementation
        formatting_kwargs['inputs'] = dict(i.unwrap() for i in item.task.inputs.values())
    else:
        formatting_kwargs['implementation'] = item.execution.workflow_name
        formatting_kwargs['inputs'] = dict(i.unwrap() for i in item.execution.inputs.values())

    if 'timestamp' in formatting:
        formatting_kwargs['timestamp'] = item.created_at.strftime(formatting['timestamp'])
    else:
        formatting_kwargs['timestamp'] = item.created_at

    msg.write(formatting['message'].format(**formatting_kwargs))

    # Add the exception and the error msg.
    if item.traceback and env.logging.verbosity_level >= logger.MEDIUM_VERBOSE:
        for line in item.traceback.splitlines(True):
            msg.write('\t' + '|' + line)

    return msg.getvalue()


def log(item, *args, **kwargs):
    return getattr(env.logging.logger, item.level.lower())(_str(item), *args, **kwargs)


def log_list(iterator):
    any_logs = False
    for item in iterator:
        log(item)
        any_logs = True
    return any_logs
