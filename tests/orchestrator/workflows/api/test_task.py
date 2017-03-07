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


import pytest

from aria.orchestrator import context
from aria.orchestrator.workflows import api
from aria.modeling import models

from tests import mock, storage


@pytest.fixture
def ctx(tmpdir):
    """
    Create the following graph in storage:
    dependency_node <------ dependent_node
    :return:
    """
    simple_context = mock.context.simple(str(tmpdir), inmemory=False)
    simple_context.model.execution.put(mock.models.create_execution(simple_context.service))
    yield simple_context
    storage.release_sqlite_storage(simple_context.model)


class TestOperationTask(object):

    def test_node_operation_task_creation(self, ctx):
        interface_name = 'test_interface'
        operation_name = 'create'

        plugin = mock.models.create_plugin('package', '0.1')
        plugin.name = 'test_plugin'

        interface = mock.models.create_interface(
            ctx.service,
            interface_name,
            operation_name,
            operation_kwargs=dict(plugin=plugin, implementation='op_path'))

        node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)
        node.interfaces = {interface.name: interface}
        node.plugins = [plugin]
        ctx.model.node.update(node)
        inputs = {'test_input': True}
        max_attempts = 10
        retry_interval = 10
        ignore_failure = True

        with context.workflow.current.push(ctx):
            api_task = api.task.OperationTask.for_node(
                node=node,
                interface_name=interface_name,
                operation_name=operation_name,
                inputs=inputs,
                max_attempts=max_attempts,
                retry_interval=retry_interval,
                ignore_failure=ignore_failure)

        assert api_task.name == api.task.OperationTask.NAME_FORMAT.format(
            type='node',
            id=node.id,
            interface=interface_name,
            operation=operation_name
        )
        assert api_task.implementation == 'op_path'
        assert api_task.actor == node
        assert api_task.inputs['test_input'].value is True
        assert api_task.retry_interval == retry_interval
        assert api_task.max_attempts == max_attempts
        assert api_task.ignore_failure == ignore_failure
        assert api_task.plugin.name == 'test_plugin'
        assert api_task.runs_on == models.Task.RUNS_ON_NODE

    def test_source_relationship_operation_task_creation(self, ctx):
        interface_name = 'test_interface'
        operation_name = 'preconfigure'

        plugin = mock.models.create_plugin('package', '0.1')
        plugin.name = 'test_plugin'

        interface = mock.models.create_interface(
            ctx.service,
            interface_name,
            operation_name,
            operation_kwargs=dict(plugin=plugin, implementation='op_path')
        )

        relationship = ctx.model.relationship.list()[0]
        relationship.interfaces[interface.name] = interface
        relationship.source_node.plugins = [plugin]
        inputs = {'test_input': True}
        max_attempts = 10
        retry_interval = 10

        with context.workflow.current.push(ctx):
            api_task = api.task.OperationTask.for_relationship(
                relationship=relationship,
                interface_name=interface_name,
                operation_name=operation_name,
                inputs=inputs,
                max_attempts=max_attempts,
                retry_interval=retry_interval)

        assert api_task.name == api.task.OperationTask.NAME_FORMAT.format(
            type='relationship',
            id=relationship.id,
            interface=interface_name,
            operation=operation_name
        )
        assert api_task.implementation == 'op_path'
        assert api_task.actor == relationship
        assert api_task.inputs['test_input'].value is True
        assert api_task.retry_interval == retry_interval
        assert api_task.max_attempts == max_attempts
        assert api_task.plugin.name == 'test_plugin'
        assert api_task.runs_on == models.Task.RUNS_ON_SOURCE

    def test_target_relationship_operation_task_creation(self, ctx):
        interface_name = 'test_interface'
        operation_name = 'preconfigure'

        plugin = mock.models.create_plugin('package', '0.1')
        plugin.name = 'test_plugin'

        interface = mock.models.create_interface(
            ctx.service,
            interface_name,
            operation_name,
            operation_kwargs=dict(plugin=plugin, implementation='op_path')
        )

        relationship = ctx.model.relationship.list()[0]
        relationship.interfaces[interface.name] = interface
        relationship.target_node.plugins = [plugin]
        inputs = {'test_input': True}
        max_attempts = 10
        retry_interval = 10

        with context.workflow.current.push(ctx):
            api_task = api.task.OperationTask.for_relationship(
                relationship=relationship,
                interface_name=interface_name,
                operation_name=operation_name,
                inputs=inputs,
                max_attempts=max_attempts,
                retry_interval=retry_interval,
                runs_on=models.Task.RUNS_ON_TARGET)

        assert api_task.name == api.task.OperationTask.NAME_FORMAT.format(
            type='relationship',
            id=relationship.id,
            interface=interface_name,
            operation=operation_name
        )
        assert api_task.implementation == 'op_path'
        assert api_task.actor == relationship
        assert api_task.inputs['test_input'].value is True
        assert api_task.retry_interval == retry_interval
        assert api_task.max_attempts == max_attempts
        assert api_task.plugin.name == 'test_plugin'
        assert api_task.runs_on == models.Task.RUNS_ON_TARGET

    def test_operation_task_default_values(self, ctx):
        dependency_node = ctx.model.node.get_by_name(
            mock.models.DEPENDENCY_NODE_NAME)

        with context.workflow.current.push(ctx):
            task = api.task.OperationTask(
                name='stub',
                implementation='',
                actor=dependency_node)

        assert task.inputs == {}
        assert task.retry_interval == ctx._task_retry_interval
        assert task.max_attempts == ctx._task_max_attempts
        assert task.ignore_failure == ctx._task_ignore_failure
        assert task.plugin is None
        assert task.runs_on is None


class TestWorkflowTask(object):

    def test_workflow_task_creation(self, ctx):

        workspace = {}

        mock_class = type('mock_class', (object,), {'test_attribute': True})

        def sub_workflow(**kwargs):
            workspace.update(kwargs)
            return mock_class

        with context.workflow.current.push(ctx):
            workflow_task = api.task.WorkflowTask(sub_workflow, kwarg='workflow_kwarg')
            assert workflow_task.graph is mock_class
            assert workflow_task.test_attribute is True
