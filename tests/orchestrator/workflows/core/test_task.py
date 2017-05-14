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

NODE_INTERFACE_NAME = 'Standard'
NODE_OPERATION_NAME = 'create'
RELATIONSHIP_INTERFACE_NAME = 'Configure'
RELATIONSHIP_OPERATION_NAME = 'pre_configure'


@pytest.fixture
def ctx(tmpdir):
    context = mock.context.simple(str(tmpdir))

    relationship = context.model.relationship.list()[0]
    interface = mock.models.create_interface(
        relationship.source_node.service,
        RELATIONSHIP_INTERFACE_NAME,
        RELATIONSHIP_OPERATION_NAME,
        operation_kwargs={'implementation': 'test'}
    )
    relationship.interfaces[interface.name] = interface
    context.model.relationship.update(relationship)

    node = context.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    interface = mock.models.create_interface(
        node.service,
        NODE_INTERFACE_NAME,
        NODE_OPERATION_NAME,
        operation_kwargs={'implementation': 'test'}
    )
    node.interfaces[interface.name] = interface
    context.model.node.update(node)

    yield context
    storage.release_sqlite_storage(context.model)


class TestOperationTask(object):

    def _create_node_operation_task(self, ctx, node):
        with workflow_context.current.push(ctx):
            api_task = api.task.OperationTask(
                node,
                interface_name=NODE_INTERFACE_NAME,
                operation_name=NODE_OPERATION_NAME)
            core_task = core.task.OperationTask(api_task=api_task, executor=None)
        return api_task, core_task

    def _create_relationship_operation_task(self, ctx, relationship):
        with workflow_context.current.push(ctx):
            api_task = api.task.OperationTask(
                relationship,
                interface_name=RELATIONSHIP_INTERFACE_NAME,
                operation_name=RELATIONSHIP_OPERATION_NAME)
            core_task = core.task.OperationTask(api_task=api_task, executor=None)
        return api_task, core_task

    def test_node_operation_task_creation(self, ctx):
        storage_plugin = mock.models.create_plugin('p1', '0.1')
        storage_plugin_other = mock.models.create_plugin('p0', '0.0')
        ctx.model.plugin.put(storage_plugin)
        ctx.model.plugin.put(storage_plugin_other)
        node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
        interface = mock.models.create_interface(
            node.service,
            NODE_INTERFACE_NAME,
            NODE_OPERATION_NAME,
            operation_kwargs=dict(plugin=storage_plugin, implementation='test')
        )
        node.interfaces[interface.name] = interface
        ctx.model.node.update(node)
        api_task, core_task = self._create_node_operation_task(ctx, node)
        storage_task = ctx.model.task.get_by_name(core_task.name)
        assert storage_task.plugin is storage_plugin
        assert storage_task.execution_name == ctx.execution.name
        assert storage_task.actor == core_task.context.node._original_model
        assert core_task.model_task == storage_task
        assert core_task.name == api_task.name
        assert core_task.implementation == api_task.implementation
        assert core_task.actor == api_task.actor == node
        assert core_task.inputs == api_task.inputs == storage_task.inputs
        assert core_task.plugin == storage_plugin

    def test_relationship_operation_task_creation(self, ctx):
        relationship = ctx.model.relationship.list()[0]
        ctx.model.relationship.update(relationship)
        _, core_task = self._create_relationship_operation_task(
            ctx, relationship)
        assert core_task.model_task.actor == relationship

    def test_operation_task_edit_locked_attribute(self, ctx):
        node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)

        _, core_task = self._create_node_operation_task(ctx, node)
        now = datetime.utcnow()
        with pytest.raises(exceptions.TaskException):
            core_task.status = core_task.STARTED
        with pytest.raises(exceptions.TaskException):
            core_task.started_at = now
        with pytest.raises(exceptions.TaskException):
            core_task.ended_at = now
        with pytest.raises(exceptions.TaskException):
            core_task.attempts_count = 2
        with pytest.raises(exceptions.TaskException):
            core_task.due_at = now

    def test_operation_task_edit_attributes(self, ctx):
        node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)

        _, core_task = self._create_node_operation_task(ctx, node)
        future_time = datetime.utcnow() + timedelta(seconds=3)

        with core_task._update():
            core_task.status = core_task.STARTED
            core_task.started_at = future_time
            core_task.ended_at = future_time
            core_task.attempts_count = 2
            core_task.due_at = future_time
            assert core_task.status != core_task.STARTED
            assert core_task.started_at != future_time
            assert core_task.ended_at != future_time
            assert core_task.attempts_count != 2
            assert core_task.due_at != future_time

        assert core_task.status == core_task.STARTED
        assert core_task.started_at == future_time
        assert core_task.ended_at == future_time
        assert core_task.attempts_count == 2
        assert core_task.due_at == future_time
