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
Sub-process task executor.
"""

# pylint: disable=wrong-import-position

import os
import sys

# As part of the process executor implementation, subprocess are started with this module as their
# entry point. We thus remove this module's directory from the python path if it happens to be
# there

import signal
from collections import namedtuple

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

import psutil
import jsonpickle

import aria
from aria.orchestrator.workflows.executor import base
from aria.extension import process_executor
from aria.utils import (
    imports,
    exceptions,
    process as process_utils
)


_INT_FMT = 'I'
_INT_SIZE = struct.calcsize(_INT_FMT)
UPDATE_TRACKED_CHANGES_FAILED_STR = \
    'Some changes failed writing to storage. For more info refer to the log.'


_Task = namedtuple('_Task', 'proc, ctx')


class ProcessExecutor(base.BaseExecutor):
    """
    Sub-process task executor.
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

        for task_id in self._tasks:
            self.terminate(task_id)

    def terminate(self, task_id):
        task = self._remove_task(task_id)
        # The process might have managed to finish, thus it would not be in the tasks list
        if task:
            try:
                parent_process = psutil.Process(task.proc.pid)
                for child_process in reversed(parent_process.children(recursive=True)):
                    try:
                        child_process.send_signal(signal.SIGKILL)
                    except BaseException:
                        pass
                parent_process.send_signal(signal.SIGKILL)
            except BaseException:
                pass

    def _execute(self, ctx):
        self._check_closed()

        # Temporary file used to pass arguments to the started subprocess
        file_descriptor, arguments_json_path = tempfile.mkstemp(prefix='executor-', suffix='.json')
        os.close(file_descriptor)
        with open(arguments_json_path, 'wb') as f:
            f.write(pickle.dumps(self._create_arguments_dict(ctx)))

        env = self._construct_subprocess_env(task=ctx.task)
        # Asynchronously start the operation in a subprocess
        proc = subprocess.Popen(
            [
                sys.executable,
                os.path.expanduser(os.path.expandvars(__file__)),
                os.path.expanduser(os.path.expandvars(arguments_json_path))
            ],
            env=env)

        self._tasks[ctx.task.id] = _Task(ctx=ctx, proc=proc)

    def _remove_task(self, task_id):
        return self._tasks.pop(task_id, None)

    def _check_closed(self):
        if self._stopped:
            raise RuntimeError('Executor closed')

    def _create_arguments_dict(self, ctx):
        return {
            'task_id': ctx.task.id,
            'function': ctx.task.function,
            'operation_arguments': dict(arg.unwrapped for arg in ctx.task.arguments.values()),
            'port': self._server_port,
            'context': ctx.serialization_dict,
        }

    def _construct_subprocess_env(self, task):
        env = os.environ.copy()

        if task.plugin_fk and self._plugin_manager:
            # If this is a plugin operation,
            # load the plugin on the subprocess env we're constructing
            self._plugin_manager.load_plugin(task.plugin, env=env)

        # Add user supplied directories to injected PYTHONPATH
        if self._python_path:
            process_utils.append_to_pythonpath(*self._python_path, env=env)

        return env

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
                    task_id = request['task_id']
                    request_handler(task_id=task_id, request=request, response=response)
            except BaseException as e:
                self.logger.debug('Error in process executor listener: {0}'.format(e))

    @contextlib.contextmanager
    def _accept_request(self):
        with contextlib.closing(self._server_socket.accept()[0]) as connection:
            message = _recv_message(connection)
            response = {}
            try:
                yield message, response
            except BaseException as e:
                response['exception'] = exceptions.wrap_if_needed(e)
                raise
            finally:
                _send_message(connection, response)

    def _handle_task_started_request(self, task_id, **kwargs):
        self._task_started(self._tasks[task_id].ctx)

    def _handle_task_succeeded_request(self, task_id, **kwargs):
        task = self._remove_task(task_id)
        if task:
            self._task_succeeded(task.ctx)

    def _handle_task_failed_request(self, task_id, request, **kwargs):
        task = self._remove_task(task_id)
        if task:
            self._task_failed(
                task.ctx, exception=request['exception'], traceback=request['traceback'])


def _send_message(connection, message):

    # Packing the length of the entire msg using struct.pack.
    # This enables later reading of the content.
    def _pack(data):
        return struct.pack(_INT_FMT, len(data))

    data = jsonpickle.dumps(message)
    msg_metadata = _pack(data)
    connection.send(msg_metadata)
    connection.sendall(data)


def _recv_message(connection):
    # Retrieving the length of the msg to come.
    def _unpack(conn):
        return struct.unpack(_INT_FMT, _recv_bytes(conn, _INT_SIZE))[0]

    msg_metadata_len = _unpack(connection)
    msg = _recv_bytes(connection, msg_metadata_len)
    return jsonpickle.loads(msg)


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

    def succeeded(self):
        """Task succeeded message"""
        self._send_message(type='succeeded')

    def failed(self, exception):
        """Task failed message"""
        self._send_message(type='failed', exception=exception)

    def closed(self):
        """Executor closed message"""
        self._send_message(type='closed')

    def _send_message(self, type, exception=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', self.port))
        try:
            _send_message(sock, {
                'type': type,
                'task_id': self.task_id,
                'exception': exceptions.wrap_if_needed(exception),
                'traceback': exceptions.get_exception_as_string(*sys.exc_info()),
            })
            response = _recv_message(sock)
            response_exception = response.get('exception')
            if response_exception:
                raise response_exception
        finally:
            sock.close()


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

    function = arguments['function']
    operation_arguments = arguments['operation_arguments']
    context_dict = arguments['context']

    try:
        ctx = context_dict['context_cls'].instantiate_from_dict(**context_dict['context'])
    except BaseException as e:
        messenger.failed(e)
        return

    try:
        messenger.started()
        task_func = imports.load_attribute(function)
        aria.install_aria_extensions()
        for decorate in process_executor.decorate():
            task_func = decorate(task_func)
        task_func(ctx=ctx, **operation_arguments)
        ctx.close()
        messenger.succeeded()
    except BaseException as e:
        ctx.close()
        messenger.failed(e)

if __name__ == '__main__':
    _main()
