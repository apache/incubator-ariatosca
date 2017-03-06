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

import os
import subprocess
import threading
import StringIO

from . import ctx_proxy
from . import exceptions
from . import common
from . import constants
from . import environment_globals
from . import python_script_scope


def run_script(ctx, script_path, process, **kwargs):
    if not script_path:
        ctx.task.abort('Missing script_path')
    process = process or {}
    script_path = common.download_script(ctx, script_path)
    script_func = _get_run_script_func(script_path, process)
    return script_func(
        ctx=ctx,
        script_path=script_path,
        process=process,
        operation_kwargs=kwargs)


def _get_run_script_func(script_path, process):
    if _treat_script_as_python_script(script_path, process):
        return _eval_script_func
    else:
        if _treat_script_as_powershell_script(script_path):
            process.setdefault('command_prefix', constants.DEFAULT_POWERSHELL_EXECUTABLE)
        return _execute_func


def _treat_script_as_python_script(script_path, process):
    eval_python = process.get('eval_python')
    script_extension = os.path.splitext(script_path)[1].lower()
    return (eval_python is True or (script_extension == constants.PYTHON_SCRIPT_FILE_EXTENSION and
                                    eval_python is not False))


def _treat_script_as_powershell_script(script_path):
    script_extension = os.path.splitext(script_path)[1].lower()
    return script_extension == constants.POWERSHELL_SCRIPT_FILE_EXTENSION


def _eval_script_func(script_path, ctx, operation_kwargs, **_):
    with python_script_scope(operation_ctx=ctx, operation_inputs=operation_kwargs):
        execfile(script_path, environment_globals.create_initial_globals(script_path))


def _execute_func(script_path, ctx, process, operation_kwargs):
    os.chmod(script_path, 0755)
    process = common.create_process_config(
        script_path=script_path,
        process=process,
        operation_kwargs=operation_kwargs)
    command = process['command']
    env = os.environ.copy()
    env.update(process['env'])
    ctx.logger.info('Executing: {0}'.format(command))
    with ctx_proxy.server.CtxProxy(ctx, common.patch_ctx) as proxy:
        env[ctx_proxy.client.CTX_SOCKET_URL] = proxy.socket_url
        running_process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=process.get('cwd'),
            bufsize=1,
            close_fds=not common.is_windows())
        stdout_consumer = _OutputConsumer(running_process.stdout)
        stderr_consumer = _OutputConsumer(running_process.stderr)
        exit_code = running_process.wait()
    stdout_consumer.join()
    stderr_consumer.join()
    ctx.logger.info('Execution done (exit_code={0}): {1}'.format(exit_code, command))

    def error_check_func():
        if exit_code:
            raise exceptions.ProcessException(
                command=command,
                exit_code=exit_code,
                stdout=stdout_consumer.read_output(),
                stderr=stderr_consumer.read_output())
    return common.check_error(ctx, error_check_func=error_check_func)


class _OutputConsumer(object):

    def __init__(self, out):
        self._out = out
        self._buffer = StringIO.StringIO()
        self._consumer = threading.Thread(target=self._consume_output)
        self._consumer.daemon = True
        self._consumer.start()

    def _consume_output(self):
        for line in iter(self._out.readline, b''):
            self._buffer.write(line)
        self._out.close()

    def read_output(self):
        return self._buffer.getvalue()

    def join(self):
        self._consumer.join()
