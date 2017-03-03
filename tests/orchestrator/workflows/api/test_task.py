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
    simple_context.model.execution.put(mock.models.get_execution(simple_context.service_instance))
    yield simple_context
    storage.release_sqlite_storage(simple_context.model)


class TestOperationTask(object):

    def test_node_operation_task_creation(self, ctx):
        operation_name = 'aria.interfaces.lifecycle.create'
        interface = mock.models.get_interface(
            operation_name,
            operation_kwargs=dict(plugin='plugin', implementation='op_path'))

        node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_INSTANCE_NAME)
        node.interfaces = [interface]
        node.plugins = [{'name': 'plugin',
                         'package_name': 'package',
                         'package_version': '0.1'}]
        ctx.model.node_template.update(node)
        inputs = {'name': True}
        max_attempts = 10
        retry_interval = 10
        ignore_failure = True

        with context.workflow.current.push(ctx):
            api_task = api.task.OperationTask.for_node(
                node=node,
                name=operation_name,
                inputs=inputs,
                max_attempts=max_attempts,
                retry_interval=retry_interval,
                ignore_failure=ignore_failure)

        assert api_task.name == '{0}.{1}'.format(operation_name, node.id)
        assert api_task.implementation == 'op_path'
        assert api_task.actor == node
        assert api_task.inputs == inputs
        assert api_task.retry_interval == retry_interval
        assert api_task.max_attempts == max_attempts
        assert api_task.ignore_failure == ignore_failure
        assert api_task.plugin == {'name': 'plugin',
                                   'package_name': 'package',
                                   'package_version': '0.1'}
        assert api_task.runs_on == models.Task.RUNS_ON_NODE

    def test_source_relationship_operation_task_creation(self, ctx):
        operation_name = 'aria.interfaces.relationship_lifecycle.preconfigure'

        interface = mock.models.get_interface(
            operation_name,
            operation_kwargs=dict(implementation='op_path', plugin='plugin'),
            edge='source'
        )

        relationship = ctx.model.relationship.list()[0]
        relationship.interfaces = [interface]
        relationship.source_node.plugins = [{'name': 'plugin',
                                             'package_name': 'package',
                                             'package_version': '0.1'}]
        inputs = {'name': True}
        max_attempts = 10
        retry_interval = 10

        with context.workflow.current.push(ctx):
            api_task = api.task.OperationTask.for_relationship(
                relationship=relationship,
                name=operation_name,
                edge='source',
                inputs=inputs,
                max_attempts=max_attempts,
                retry_interval=retry_interval)

        assert api_task.name == '{0}.{1}'.format(operation_name, relationship.id)
        assert api_task.implementation == 'op_path'
        assert api_task.actor == relationship
        assert api_task.inputs == inputs
        assert api_task.retry_interval == retry_interval
        assert api_task.max_attempts == max_attempts
        assert api_task.plugin == {'name': 'plugin',
                                   'package_name': 'package',
                                   'package_version': '0.1'}
        assert api_task.runs_on == models.Task.RUNS_ON_SOURCE

    def test_target_relationship_operation_task_creation(self, ctx):
        operation_name = 'aria.interfaces.relationship_lifecycle.preconfigure'
        interface = mock.models.get_interface(
            operation_name,
            operation_kwargs=dict(implementation='op_path', plugin='plugin'),
            edge='target'
        )

        relationship = ctx.model.relationship.list()[0]
        relationship.interfaces = [interface]
        relationship.target_node.plugins = [{'name': 'plugin',
                                             'package_name': 'package',
                                             'package_version': '0.1'}]
        inputs = {'name': True}
        max_attempts = 10
        retry_interval = 10

        with context.workflow.current.push(ctx):
            api_task = api.task.OperationTask.for_relationship(
                relationship=relationship,
                name=operation_name,
                edge='target',
                inputs=inputs,
                max_attempts=max_attempts,
                retry_interval=retry_interval)

        assert api_task.name == '{0}.{1}'.format(operation_name, relationship.id)
        assert api_task.implementation == 'op_path'
        assert api_task.actor == relationship
        assert api_task.inputs == inputs
        assert api_task.retry_interval == retry_interval
        assert api_task.max_attempts == max_attempts
        assert api_task.plugin == {'name': 'plugin',
                                   'package_name': 'package',
                                   'package_version': '0.1'}
        assert api_task.runs_on == models.Task.RUNS_ON_TARGET

    def test_operation_task_default_values(self, ctx):
        dependency_node_instance = ctx.model.node.get_by_name(
            mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
        with context.workflow.current.push(ctx):
            task = api.task.OperationTask(
                name='stub',
                implementation='',
                actor=dependency_node_instance)

        assert task.inputs == {}
        assert task.retry_interval == ctx._task_retry_interval
        assert task.max_attempts == ctx._task_max_attempts
        assert task.ignore_failure == ctx._task_ignore_failure
        assert task.plugin == {}
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
