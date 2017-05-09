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
import Queue

import pytest

import aria
from aria.orchestrator import events
from aria.utils.plugin import create as create_plugin
from aria.orchestrator.workflows.executor import process

import tests.storage
import tests.resources
from tests.fixtures import (  # pylint: disable=unused-import
    plugins_dir,
    plugin_manager,
    fs_model as model
)
from . import MockTask


class TestProcessExecutor(object):

    def test_plugin_execution(self, executor, mock_plugin, storage):
        task = MockTask('mock_plugin1.operation', plugin=mock_plugin, storage=storage)

        queue = Queue.Queue()

        def handler(_, exception=None, **kwargs):
            queue.put(exception)

        events.on_success_task_signal.connect(handler)
        events.on_failure_task_signal.connect(handler)
        try:
            executor.execute(task)
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
        finally:
            events.on_success_task_signal.disconnect(handler)
            events.on_failure_task_signal.disconnect(handler)

    def test_closed(self, executor):
        executor.close()
        with pytest.raises(RuntimeError) as exc_info:
            executor.execute(task=MockTask(implementation='some.implementation'))
        assert 'closed' in exc_info.value.message


@pytest.fixture
def executor(plugin_manager):
    result = process.ProcessExecutor(plugin_manager=plugin_manager)
    yield result
    result.close()


@pytest.fixture
def mock_plugin(plugin_manager, tmpdir):
    source = os.path.join(tests.resources.DIR, 'plugins', 'mock-plugin1')
    plugin_path = create_plugin(source=source, destination_dir=str(tmpdir))
    return plugin_manager.install(source=plugin_path)


@pytest.fixture
def storage(tmpdir):
    return aria.application_model_storage(
        aria.storage.sql_mapi.SQLAlchemyModelAPI,
        initiator_kwargs=dict(base_dir=str(tmpdir))
    )
