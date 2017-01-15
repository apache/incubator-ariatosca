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
Subprocess based executor
"""

# pylint: disable=wrong-import-position

import sys
import os

# As part of the process executor implementation, subprocess are started with this module as their
# entry point. We thus remove this module's directory from the python path if it happens to be
# there
script_dir = os.path.dirname(__file__)
if script_dir in sys.path:
    sys.path.remove(script_dir)

import io
import threading
import socket
import struct
import subprocess
import tempfile
import Queue

import jsonpickle

from aria.utils import imports
from aria.orchestrator.workflows.executor import base
from aria.orchestrator.context import serialization
from aria.storage import instrumentation
from aria.storage import type as storage_type

_IS_WIN = os.name == 'nt'

_INT_FMT = 'I'
_INT_SIZE = struct.calcsize(_INT_FMT)


class ProcessExecutor(base.BaseExecutor):
    """
    Executor which runs tasks in a subprocess environment
    """

    def __init__(self, plugin_manager=None, python_path=None, *args, **kwargs):
        super(ProcessExecutor, self).__init__(*args, **kwargs)
        self._plugin_manager = plugin_manager

        # Optional list of additional directories that should be added to
        # subprocesses python path
        self._python_path = python_path or []

        # Flag that denotes whether this executor has been stopped
        self._stopped = False

        # Contains reference to all currently running tasks
        self._tasks = {}

        # Server socket used to accept task status messages from subprocesses
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('localhost', 0))
        self._server_socket.listen(10)
        self._server_port = self._server_socket.getsockname()[1]

        # Used to send a "closed" message to the listener when this executor is closed
        self._messenger = _Messenger(task_id=None, port=self._server_port)

        # Queue object used by the listener thread to notify this constructed it has started
        # (see last line of this __init__ method)
        self._listener_started = Queue.Queue()

        # Listener thread to handle subprocesses task status messages
        self._listener_thread = threading.Thread(target=self._listener)
        self._listener_thread.daemon = True
        self._listener_thread.start()

        # Wait for listener thread to actually start before returning
        self._listener_started.get(timeout=60)

    def close(self):
        if self._stopped:
            return
        self._stopped = True
        # Listener thread may be blocked on "accept" call. This will wake it up with an explicit
        # "closed" message
        self._messenger.closed()
        self._server_socket.close()
        self._listener_thread.join(timeout=60)

    def execute(self, task):
        self._check_closed()
        self._tasks[task.id] = task

        # Temporary file used to pass arguments to the started subprocess
        file_descriptor, arguments_json_path = tempfile.mkstemp(prefix='executor-', suffix='.json')
        os.close(file_descriptor)
        with open(arguments_json_path, 'wb') as f:
            f.write(jsonpickle.dumps(self._create_arguments_dict(task)))

        env = os.environ.copy()
        # See _update_env for plugin_prefix usage
        if task.plugin_fk and self._plugin_manager:
            plugin_prefix = self._plugin_manager.get_plugin_prefix(task.plugin)
        else:
            plugin_prefix = None
        self._update_env(env=env, plugin_prefix=plugin_prefix)
        # Asynchronously start the operation in a subprocess
        subprocess.Popen(
            '{0} {1} {2}'.format(sys.executable, __file__, arguments_json_path),
            env=env,
            shell=True)

    def _remove_task(self, task_id):
        return self._tasks.pop(task_id)

    def _listener(self):
        # Notify __init__ method this thread has actually started
        self._listener_started.put(True)
        while not self._stopped:
            try:
                # Accept messages written to the server socket
                message = self._recv_message()
                message_type = message['type']
                if message_type == 'closed':
                    break
                task_id = message['task_id']
                if message_type == 'started':
                    self._task_started(self._tasks[task_id])
                elif message_type == 'succeeded':
                    task = self._remove_task(task_id)
                    instrumentation.apply_tracked_changes(
                        tracked_changes=message['tracked_changes'],
                        model=task.context.model)
                    self._task_succeeded(task)
                elif message_type == 'failed':
                    task = self._remove_task(task_id)
                    instrumentation.apply_tracked_changes(
                        tracked_changes=message['tracked_changes'],
                        model=task.context.model)
                    self._task_failed(task, exception=message['exception'])
                else:
                    raise RuntimeError('Invalid state')
            except BaseException as e:
                self.logger.debug('Error in process executor listener: {0}'.format(e))

    def _recv_message(self):
        connection, _ = self._server_socket.accept()
        try:
            message_len, = struct.unpack(_INT_FMT, self._recv_bytes(connection, _INT_SIZE))
            return jsonpickle.loads(self._recv_bytes(connection, message_len))
        finally:
            connection.close()

    @staticmethod
    def _recv_bytes(connection, count):
        result = io.BytesIO()
        while True:
            if not count:
                return result.getvalue()
            read = connection.recv(count)
            if not read:
                return result.getvalue()
            result.write(read)
            count -= len(read)

    def _check_closed(self):
        if self._stopped:
            raise RuntimeError('Executor closed')

    def _create_arguments_dict(self, task):
        return {
            'task_id': task.id,
            'operation_mapping': task.operation_mapping,
            'operation_inputs': task.inputs,
            'port': self._server_port,
            'context': serialization.operation_context_to_dict(task.context),
        }

    def _update_env(self, env, plugin_prefix):
        pythonpath_dirs = []
        # If this is a plugin operation, plugin prefix will point to where
        # This plugin is installed.
        # We update the environment variables that the subprocess will be started with based on it
        if plugin_prefix:

            # Update PATH environment variable to include plugin's bin dir
            bin_dir = 'Scripts' if _IS_WIN else 'bin'
            env['PATH'] = '{0}{1}{2}'.format(
                os.path.join(plugin_prefix, bin_dir),
                os.pathsep,
                env.get('PATH', ''))

            # Update PYTHONPATH environment variable to include plugin's site-packages
            # directories
            if _IS_WIN:
                pythonpath_dirs = [os.path.join(plugin_prefix, 'Lib', 'site-packages')]
            else:
                # In some linux environments, there will be both a lib and a lib64 directory
                # with the latter, containing compiled packages.
                pythonpath_dirs = [os.path.join(
                    plugin_prefix, 'lib{0}'.format(b),
                    'python{0}.{1}'.format(sys.version_info[0], sys.version_info[1]),
                    'site-packages') for b in ['', '64']]

        # Add used supplied directories to injected PYTHONPATH
        pythonpath_dirs.extend(self._python_path)

        if pythonpath_dirs:
            env['PYTHONPATH'] = '{0}{1}{2}'.format(
                os.pathsep.join(pythonpath_dirs),
                os.pathsep,
                env.get('PYTHONPATH', ''))


class _Messenger(object):

    def __init__(self, task_id, port):
        self.task_id = task_id
        self.port = port

    def started(self):
        """Task started message"""
        self._send_message(type='started')

    def succeeded(self, tracked_changes):
        """Task succeeded message"""
        self._send_message(type='succeeded', tracked_changes=tracked_changes)

    def failed(self, tracked_changes, exception):
        """Task failed message"""
        self._send_message(type='failed', tracked_changes=tracked_changes, exception=exception)

    def closed(self):
        """Executor closed message"""
        self._send_message(type='closed')

    def _send_message(self, type, tracked_changes=None, exception=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', self.port))
        try:
            data = jsonpickle.dumps({
                'type': type,
                'task_id': self.task_id,
                'exception': exception,
                'tracked_changes': tracked_changes
            })
            sock.send(struct.pack(_INT_FMT, len(data)))
            sock.sendall(data)
        finally:
            sock.close()


def _main():
    arguments_json_path = sys.argv[1]
    with open(arguments_json_path) as f:
        arguments = jsonpickle.loads(f.read())

    # arguments_json_path is a temporary file created by the parent process.
    # so we remove it here
    os.remove(arguments_json_path)

    task_id = arguments['task_id']
    port = arguments['port']
    messenger = _Messenger(task_id=task_id, port=port)
    messenger.started()

    operation_mapping = arguments['operation_mapping']
    operation_inputs = arguments['operation_inputs']
    context_dict = arguments['context']

    # This is required for the instrumentation work properly.
    # See docstring of `remove_mutable_association_listener` for further details
    storage_type.remove_mutable_association_listener()

    with instrumentation.track_changes() as instrument:
        try:
            ctx = serialization.operation_context_from_dict(context_dict)
            task_func = imports.load_attribute(operation_mapping)
            task_func(ctx=ctx, **operation_inputs)
            messenger.succeeded(tracked_changes=instrument.tracked_changes)
        except BaseException as e:
            messenger.failed(exception=e, tracked_changes=instrument.tracked_changes)

if __name__ == '__main__':
    _main()
