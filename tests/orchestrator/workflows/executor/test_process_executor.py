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

import logging
import os
import uuid
import Queue
from contextlib import contextmanager

import pytest

from aria import application_model_storage
from aria.storage import models
from aria.utils.plugin import create as create_plugin
from aria.storage.sql_mapi import SQLAlchemyModelAPI
from aria.orchestrator import events
from aria.orchestrator import plugin
from aria.orchestrator.workflows.executor import process


import tests.storage
import tests.resources


class TestProcessExecutor(object):

    def test_plugin_execution(self, executor, mock_plugin):
        task = MockTask(plugin=mock_plugin,
                        operation='mock_plugin1.operation')

        queue = Queue.Queue()

        def handler(_, exception=None):
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
            executor.execute(task=None)
        assert 'closed' in exc_info.value.message


@pytest.fixture
def model(tmpdir):
    api_kwargs = tests.storage.get_sqlite_api_kwargs(str(tmpdir))
    result = application_model_storage(SQLAlchemyModelAPI, api_kwargs=api_kwargs)
    yield result
    tests.storage.release_sqlite_storage(result)


@pytest.fixture
def plugins_dir(tmpdir):
    result = tmpdir.join('plugins')
    result.mkdir()
    return str(result)


@pytest.fixture
def plugin_manager(model, plugins_dir):
    return plugin.PluginManager(model=model, plugins_dir=plugins_dir)


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


class MockTask(object):

    INFINITE_RETRIES = models.Task.INFINITE_RETRIES

    def __init__(self, plugin, operation):
        self.id = str(uuid.uuid4())
        self.operation_mapping = operation
        self.logger = logging.getLogger()
        self.name = operation
        self.inputs = {}
        self.context = None
        self.retry_count = 0
        self.max_attempts = 1
        self.plugin_id = plugin.id
        self.plugin = plugin

        for state in models.Task.STATES:
            setattr(self, state.upper(), state)

    @contextmanager
    def _update(self):
        yield self
