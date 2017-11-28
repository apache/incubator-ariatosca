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
import sys
import time
import Queue
import subprocess

import pytest
import psutil
import retrying

import aria

from aria import operation
from aria.modeling import models
from aria.orchestrator import events
from aria.utils.plugin import create as create_plugin
from aria.orchestrator.workflows.executor import process

import tests.storage
import tests.resources
from tests.fixtures import (  # pylint: disable=unused-import
    plugins_dir,
    plugin_manager,
)
from tests.helpers import FilesystemDataHolder
from ..helpers import disconnect_event_handlers
from . import MockContext


class TestProcessExecutor(object):

    def test_plugin_execution(self, executor, mock_plugin, model, queue):
        ctx = MockContext(
            model,
            task_kwargs=dict(function='mock_plugin1.operation', plugin_fk=mock_plugin.id)
        )
        executor.execute(ctx)
        error = queue.get(timeout=60)
        # tests/resources/plugins/mock-plugin1 is the plugin installed
        # during this tests setup. The module mock_plugin1 contains a single
        # operation named "operation" which calls an entry point defined in the plugin's
        # setup.py. This entry points simply prints 'mock-plugin-output' to stdout.
        # The "operation" operation that called this subprocess, then raises a RuntimeError
        # with that subprocess output as the error message.
        # This is what we assert here. This tests checks that both the PYTHONPATH (operation)
        # and PATH (entry point) are properly updated in the subprocess in which the task is
        # running.
        assert isinstance(error, RuntimeError)
        assert error.message == 'mock-plugin-output'

    def test_closed(self, executor, model):
        executor.close()
        with pytest.raises(RuntimeError) as exc_info:
            executor.execute(MockContext(model, task_kwargs=dict(function='some.function')))
        assert 'closed' in exc_info.value.message

    def test_process_termination(self, executor, model, fs_test_holder, tmpdir):
        freeze_script_path = str(tmpdir.join('freeze_script'))
        with open(freeze_script_path, 'w+b') as f:
            f.write(
                '''import time
while True:
    time.sleep(5)
                '''
            )
        holder_path_argument = models.Argument.wrap('holder_path', fs_test_holder._path)
        script_path_argument = models.Argument.wrap('freezing_script_path',
                                                    str(tmpdir.join('freeze_script')))

        model.argument.put(holder_path_argument)
        model.argument.put(script_path_argument)
        ctx = MockContext(
            task_kwargs=dict(
                function='{0}.{1}'.format(__name__, freezing_task.__name__),
                arguments=dict(holder_path=holder_path_argument,
                               freezing_script_path=script_path_argument)),
        )

        executor.execute(ctx)

        @retrying.retry(retry_on_result=lambda r: r is False, stop_max_delay=60000, wait_fixed=500)
        def wait_for_extra_process_id():
            return fs_test_holder.get('subproc', False)

        task_pid = executor._tasks[ctx.task.id].proc.pid
        extra_process_pid = wait_for_extra_process_id()

        assert set([task_pid, extra_process_pid]).issubset(set(psutil.pids()))
        executor.terminate(ctx.task.id)

        # Give a chance to the processes to terminate
        time.sleep(2)

        # all processes should be either zombies or non existent
        pids = [task_pid, extra_process_pid]
        for pid in pids:
            if pid in psutil.pids():
                assert psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
            else:
                # making the test more readable
                assert pid not in psutil.pids()


@pytest.fixture
def queue():
    _queue = Queue.Queue()

    def handler(_, exception=None, **kwargs):
        _queue.put(exception)

    with disconnect_event_handlers():

        events.on_success_task_signal.connect(handler)
        events.on_failure_task_signal.connect(handler)
        try:
            yield _queue
        finally:
            events.on_success_task_signal.disconnect(handler)
            events.on_failure_task_signal.disconnect(handler)


@pytest.fixture
def fs_test_holder(tmpdir):
    dataholder_path = str(tmpdir.join('dataholder'))
    holder = FilesystemDataHolder(dataholder_path)
    return holder


@pytest.fixture
def executor(plugin_manager):
    result = process.ProcessExecutor(plugin_manager=plugin_manager, python_path=[tests.ROOT_DIR])
    try:
        yield result
    finally:
        result.close()


@pytest.fixture
def mock_plugin(plugin_manager, tmpdir):
    source = os.path.join(tests.resources.DIR, 'plugins', 'mock-plugin1')
    plugin_path = create_plugin(source=source, destination_dir=str(tmpdir))
    return plugin_manager.install(source=plugin_path)


@pytest.fixture
def model(tmpdir):
    _storage = aria.application_model_storage(aria.storage.sql_mapi.SQLAlchemyModelAPI,
                                              initiator_kwargs=dict(base_dir=str(tmpdir)))
    yield _storage
    tests.storage.release_sqlite_storage(_storage)


@operation
def freezing_task(holder_path, freezing_script_path, **_):
    holder = FilesystemDataHolder(holder_path)
    holder['subproc'] = subprocess.Popen([sys.executable, freezing_script_path], shell=True).pid
    while True:
        time.sleep(5)
