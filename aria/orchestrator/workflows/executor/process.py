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

import os
import sys

# As part of the process executor implementation, subprocess are started with this module as their
# entry point. We thus remove this module's directory from the python path if it happens to be
# there
script_dir = os.path.dirname(__file__)
if script_dir in sys.path:
    sys.path.remove(script_dir)

import contextlib
import io
import threading
import socket
import struct
import subprocess
import tempfile
import Queue
import pickle

import jsonpickle

import aria
from aria.extension import process_executor
from aria.utils import imports
from aria.utils import exceptions
from aria.orchestrator.workflows.executor import base
from aria.storage import instrumentation
from aria.storage.modeling import type as storage_type

_IS_WIN = os.name == 'nt'

_INT_FMT = 'I'
_INT_SIZE = struct.calcsize(_INT_FMT)
UPDATE_TRACKED_CHANGES_FAILED_STR = \
    'Some changes failed writing to storage. For more info refer to the log.'


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

        self._request_handlers = {
            'started': self._handle_task_started_request,
            'succeeded': self._handle_task_succeeded_request,
            'failed': self._handle_task_failed_request,
            'apply_tracked_changes': self._handle_apply_tracked_changes_request
        }

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
            f.write(pickle.dumps(self._create_arguments_dict(task)))

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

    def _check_closed(self):
        if self._stopped:
            raise RuntimeError('Executor closed')

    def _create_arguments_dict(self, task):
        return {
            'task_id': task.id,
            'implementation': task.implementation,
            'operation_inputs': task.inputs,
            'port': self._server_port,
            'context': task.context.serialization_dict,
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

    def _listener(self):
        # Notify __init__ method this thread has actually started
        self._listener_started.put(True)
        while not self._stopped:
            try:
                with self._accept_request() as (request, response):
                    request_type = request['type']
                    if request_type == 'closed':
                        break
                    request_handler = self._request_handlers.get(request_type)
                    if not request_handler:
                        raise RuntimeError('Invalid request type: {0}'.format(request_type))
                    request_handler(task_id=request['task_id'], request=request, response=response)
            except BaseException as e:
                self.logger.debug('Error in process executor listener: {0}'.format(e))

    @contextlib.contextmanager
    def _accept_request(self):
        with contextlib.closing(self._server_socket.accept()[0]) as connection:
            message = _recv_message(connection)
            response = {}
            yield message, response
            _send_message(connection, response)

    def _handle_task_started_request(self, task_id, **kwargs):
        self._task_started(self._tasks[task_id])

    def _handle_task_succeeded_request(self, task_id, request, **kwargs):
        task = self._remove_task(task_id)
        try:
            self._apply_tracked_changes(task, request)
        except BaseException as e:
            e.message += UPDATE_TRACKED_CHANGES_FAILED_STR
            self._task_failed(task, exception=e)
        else:
            self._task_succeeded(task)

    def _handle_task_failed_request(self, task_id, request, **kwargs):
        task = self._remove_task(task_id)
        try:
            self._apply_tracked_changes(task, request)
        except BaseException as e:
            e.message += 'Task failed due to {0}.'.format(request['exception']) + \
                         UPDATE_TRACKED_CHANGES_FAILED_STR
            self._task_failed(task, exception=e)
        else:
            self._task_failed(task, exception=request['exception'])

    def _handle_apply_tracked_changes_request(self, task_id, request, response):
        task = self._tasks[task_id]
        try:
            self._apply_tracked_changes(task, request)
        except BaseException as e:
            response['exception'] = exceptions.wrap_if_needed(e)

    @staticmethod
    def _apply_tracked_changes(task, request):
        instrumentation.apply_tracked_changes(
            tracked_changes=request['tracked_changes'],
            model=task.context.model)


def _send_message(connection, message):
    data = jsonpickle.dumps(message)
    connection.send(struct.pack(_INT_FMT, len(data)))
    connection.sendall(data)


def _recv_message(connection):
    message_len, = struct.unpack(_INT_FMT, _recv_bytes(connection, _INT_SIZE))
    return jsonpickle.loads(_recv_bytes(connection, message_len))


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

    def apply_tracked_changes(self, tracked_changes):
        self._send_message(type='apply_tracked_changes', tracked_changes=tracked_changes)

    def closed(self):
        """Executor closed message"""
        self._send_message(type='closed')

    def _send_message(self, type, tracked_changes=None, exception=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', self.port))
        try:
            _send_message(sock, {
                'type': type,
                'task_id': self.task_id,
                'exception': exceptions.wrap_if_needed(exception),
                'tracked_changes': tracked_changes
            })
            response = _recv_message(sock)
            response_exception = response.get('exception')
            if response_exception:
                raise response_exception
        finally:
            sock.close()


def _patch_session(ctx, messenger, instrument):
    # model will be None only in tests that test the executor component directly
    if not ctx.model:
        return

    # We arbitrarily select the ``node`` mapi to extract the session from it.
    # could have been any other mapi just as well
    session = ctx.model.node._session
    original_refresh = session.refresh

    def patched_refresh(target):
        instrument.clear(target)
        original_refresh(target)

    def patched_commit():
        messenger.apply_tracked_changes(instrument.tracked_changes)
        instrument.clear()

    def patched_rollback():
        # Rollback is performed on parent process when commit fails
        pass

    # when autoflush is set to true (the default), refreshing an object will trigger
    # an auto flush by sqlalchemy, this autoflush will attempt to commit changes made so
    # far on the session. this is not the desired behavior in the subprocess
    session.autoflush = False

    session.commit = patched_commit
    session.rollback = patched_rollback
    session.refresh = patched_refresh


def _main():
    arguments_json_path = sys.argv[1]
    with open(arguments_json_path) as f:
        arguments = pickle.loads(f.read())

    # arguments_json_path is a temporary file created by the parent process.
    # so we remove it here
    os.remove(arguments_json_path)

    task_id = arguments['task_id']
    port = arguments['port']
    messenger = _Messenger(task_id=task_id, port=port)
    messenger.started()

    implementation = arguments['implementation']
    operation_inputs = arguments['operation_inputs']
    context_dict = arguments['context']

    # This is required for the instrumentation work properly.
    # See docstring of `remove_mutable_association_listener` for further details
    storage_type.remove_mutable_association_listener()
    with instrumentation.track_changes() as instrument:
        try:
            ctx = context_dict['context_cls'].deserialize_from_dict(**context_dict['context'])
            _patch_session(ctx=ctx, messenger=messenger, instrument=instrument)
            task_func = imports.load_attribute(implementation)
            aria.install_aria_extensions()
            for decorate in process_executor.decorate():
                task_func = decorate(task_func)
            task_func(ctx=ctx, **operation_inputs)
            messenger.succeeded(tracked_changes=instrument.tracked_changes)
        except BaseException as e:
            messenger.failed(exception=e, tracked_changes=instrument.tracked_changes)


if __name__ == '__main__':
    _main()
