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
from datetime import (
    datetime,
    timedelta
)

import pytest

from aria.orchestrator.context import workflow as workflow_context
from aria.orchestrator.workflows import (
    api,
    core,
    exceptions,
)

from tests import mock, storage


@pytest.fixture
def ctx(tmpdir):
    context = mock.context.simple(storage.get_sqlite_api_kwargs(str(tmpdir)))
    yield context
    storage.release_sqlite_storage(context.model)


class TestOperationTask(object):

    def _create_operation_task(self, ctx, node_instance):
        with workflow_context.current.push(ctx):
            api_task = api.task.OperationTask.node_instance(
                instance=node_instance,
                name='aria.interfaces.lifecycle.create')
            core_task = core.task.OperationTask(api_task=api_task)
        return api_task, core_task

    def test_operation_task_creation(self, ctx):
        storage_plugin = mock.models.get_plugin(package_name='p1', package_version='0.1')
        storage_plugin_other = mock.models.get_plugin(package_name='p0', package_version='0.0')
        ctx.model.plugin.put(storage_plugin_other)
        ctx.model.plugin.put(storage_plugin)
        node_instance = \
            ctx.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
        node = node_instance.node
        node.plugins = [{'name': 'plugin1',
                         'package_name': 'p1',
                         'package_version': '0.1'}]
        node.operations['aria.interfaces.lifecycle.create'] = {'plugin': 'plugin1'}
        api_task, core_task = self._create_operation_task(ctx, node_instance)
        storage_task = ctx.model.task.get_by_name(core_task.name)
        assert storage_task.execution_id == ctx.execution.id
        assert core_task.model_task == storage_task
        assert core_task.name == api_task.name
        assert core_task.operation_mapping == api_task.operation_mapping
        assert core_task.actor == api_task.actor == node_instance
        assert core_task.inputs == api_task.inputs == storage_task.inputs
        assert core_task.plugin == storage_plugin

    def test_operation_task_edit_locked_attribute(self, ctx):
        node_instance = \
            ctx.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)

        _, core_task = self._create_operation_task(ctx, node_instance)
        now = datetime.utcnow()
        with pytest.raises(exceptions.TaskException):
            core_task.status = core_task.STARTED
        with pytest.raises(exceptions.TaskException):
            core_task.started_at = now
        with pytest.raises(exceptions.TaskException):
            core_task.ended_at = now
        with pytest.raises(exceptions.TaskException):
            core_task.retry_count = 2
        with pytest.raises(exceptions.TaskException):
            core_task.due_at = now

    def test_operation_task_edit_attributes(self, ctx):
        node_instance = \
            ctx.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)

        _, core_task = self._create_operation_task(ctx, node_instance)
        future_time = datetime.utcnow() + timedelta(seconds=3)

        with core_task._update():
            core_task.status = core_task.STARTED
            core_task.started_at = future_time
            core_task.ended_at = future_time
            core_task.retry_count = 2
            core_task.due_at = future_time
            assert core_task.status != core_task.STARTED
            assert core_task.started_at != future_time
            assert core_task.ended_at != future_time
            assert core_task.retry_count != 2
            assert core_task.due_at != future_time

        assert core_task.status == core_task.STARTED
        assert core_task.started_at == future_time
        assert core_task.ended_at == future_time
        assert core_task.retry_count == 2
        assert core_task.due_at == future_time
