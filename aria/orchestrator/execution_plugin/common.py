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
Execution plugin utilities.
"""

import json
import os
import tempfile

import requests

from . import constants
from . import exceptions


def is_windows():
    return os.name == 'nt'


def download_script(ctx, script_path):
    split = script_path.split('://')
    schema = split[0]
    suffix = script_path.split('/')[-1]
    file_descriptor, dest_script_path = tempfile.mkstemp(suffix='-{0}'.format(suffix))
    os.close(file_descriptor)
    try:
        if schema in ('http', 'https'):
            response = requests.get(script_path)
            if response.status_code == 404:
                ctx.task.abort('Failed to download script: {0} (status code: {1})'
                               .format(script_path, response.status_code))
            content = response.text
            with open(dest_script_path, 'wb') as f:
                f.write(content)
        else:
            ctx.download_resource(destination=dest_script_path, path=script_path)
    except:
        os.remove(dest_script_path)
        raise
    return dest_script_path


def create_process_config(script_path, process, operation_kwargs, quote_json_env_vars=False):
    """
    Updates a process with its environment variables, and return it.

    Gets a dict representing a process and a dict representing the environment variables. Converts
    each environment variable to a format of::

        <string representing the name of the variable>:
        <json formatted string representing the value of the variable>.

    Finally, updates the process with the newly formatted environment variables, and return the
    process.

    :param process: dict representing a process
    :type process: dict
    :param operation_kwargs: dict representing environment variables that should exist in the
     process's running environment.
    :type operation_kwargs: dict
    :return: process updated with its environment variables
    :rtype: dict
    """
    process = process or {}
    env_vars = operation_kwargs.copy()
    if 'ctx' in env_vars:
        del env_vars['ctx']
    env_vars.update(process.get('env', {}))
    for k, v in env_vars.items():
        if isinstance(v, (dict, list, tuple, bool, int, float)):
            v = json.dumps(v)
            if quote_json_env_vars:
                v = "'{0}'".format(v)
        if is_windows():
            # These <k,v> environment variables will subsequently
            # be used in a subprocess.Popen() call, as the `env` parameter.
            # In some windows python versions, if an environment variable
            # name is not of type str (e.g. unicode), the Popen call will
            # fail.
            k = str(k)
            # The windows shell removes all double quotes - escape them
            # to still be able to pass JSON in env vars to the shell.
            v = v.replace('"', '\\"')
        del env_vars[k]
        env_vars[k] = str(v)
    process['env'] = env_vars
    args = process.get('args')
    command = script_path
    command_prefix = process.get('command_prefix')
    if command_prefix:
        command = '{0} {1}'.format(command_prefix, command)
    if args:
        command = ' '.join([command] + [str(a) for a in args])
    process['command'] = command
    return process


def patch_ctx(ctx):
    ctx._error = None
    task = ctx.task

    def _validate_legal_action():
        if ctx._error is not None:
            ctx._error = RuntimeError(constants.ILLEGAL_CTX_OPERATION_MESSAGE)
            raise ctx._error

    def abort_operation(message=None):
        _validate_legal_action()
        ctx._error = exceptions.ScriptException(message=message, retry=False)
        return ctx._error
    task.abort = abort_operation

    def retry_operation(message=None, retry_interval=None):
        _validate_legal_action()
        ctx._error = exceptions.ScriptException(message=message,
                                                retry=True,
                                                retry_interval=retry_interval)
        return ctx._error
    task.retry = retry_operation


def check_error(ctx, error_check_func=None, reraise=False):
    _error = ctx._error
    # this happens when a script calls task.abort/task.retry more than once
    if isinstance(_error, RuntimeError):
        ctx.task.abort(str(_error))
    # ScriptException is populated by the ctx proxy server when task.abort or task.retry
    # are called
    elif isinstance(_error, exceptions.ScriptException):
        if _error.retry:
            ctx.task.retry(_error.message, _error.retry_interval)
        else:
            ctx.task.abort(_error.message)
    # local and ssh operations may pass an additional logic check for errors here
    if error_check_func:
        error_check_func()
    # if this function is called from within an ``except`` clause, a re-raise maybe required
    if reraise:
        raise  # pylint: disable=misplaced-bare-raise
    return _error
