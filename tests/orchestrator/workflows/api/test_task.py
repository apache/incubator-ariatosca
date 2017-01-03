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

from aria.storage import model
from aria.orchestrator import context
from aria.orchestrator.workflows import api

from tests import mock, storage


@pytest.fixture
def ctx():
    """
    Create the following graph in storage:
    dependency_node <------ dependent_node
    :return:
    """
    simple_context = mock.context.simple(storage.get_sqlite_api_kwargs())
    simple_context.model.execution.put(mock.models.get_execution(simple_context.deployment))
    yield simple_context
    storage.release_sqlite_storage(simple_context.model)


class TestOperationTask(object):

    def test_node_operation_task_creation(self, ctx):
        operation_name = 'aria.interfaces.lifecycle.create'
        op_details = {'operation': True, 'plugin': 'plugin'}
        node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)
        node.operations[operation_name] = op_details
        node.plugins = [{'name': 'plugin',
                         'package_name': 'package',
                         'package_version': '0.1'}]
        ctx.model.node.update(node)
        node_instance = \
            ctx.model.node_instance.get_by_name(mock.models.DEPENDENT_NODE_INSTANCE_NAME)
        inputs = {'inputs': True}
        max_attempts = 10
        retry_interval = 10
        ignore_failure = True

        with context.workflow.current.push(ctx):
            api_task = api.task.OperationTask.node_instance(
                name=operation_name,
                instance=node_instance,
                inputs=inputs,
                max_attempts=max_attempts,
                retry_interval=retry_interval,
                ignore_failure=ignore_failure)

        assert api_task.name == '{0}.{1}'.format(operation_name, node_instance.id)
        assert api_task.operation_mapping is True
        assert api_task.actor == node_instance
        assert api_task.inputs == inputs
        assert api_task.retry_interval == retry_interval
        assert api_task.max_attempts == max_attempts
        assert api_task.ignore_failure == ignore_failure
        assert api_task.plugin == {'name': 'plugin',
                                   'package_name': 'package',
                                   'package_version': '0.1'}
        assert api_task.runs_on == model.Task.RUNS_ON_NODE_INSTANCE

    def test_source_relationship_operation_task_creation(self, ctx):
        operation_name = 'aria.interfaces.relationship_lifecycle.preconfigure'
        op_details = {'operation': True, 'plugin': 'plugin'}
        relationship = ctx.model.relationship.list()[0]
        relationship.source_operations[operation_name] = op_details
        relationship.source_node.plugins = [{'name': 'plugin',
                                             'package_name': 'package',
                                             'package_version': '0.1'}]
        relationship_instance = ctx.model.relationship_instance.list()[0]
        inputs = {'inputs': True}
        max_attempts = 10
        retry_interval = 10

        with context.workflow.current.push(ctx):
            api_task = api.task.OperationTask.relationship_instance(
                name=operation_name,
                instance=relationship_instance,
                operation_end=api.task.OperationTask.SOURCE_OPERATION,
                inputs=inputs,
                max_attempts=max_attempts,
                retry_interval=retry_interval)

        assert api_task.name == '{0}.{1}'.format(operation_name, relationship_instance.id)
        assert api_task.operation_mapping is True
        assert api_task.actor == relationship_instance
        assert api_task.inputs == inputs
        assert api_task.retry_interval == retry_interval
        assert api_task.max_attempts == max_attempts
        assert api_task.plugin == {'name': 'plugin',
                                   'package_name': 'package',
                                   'package_version': '0.1'}
        assert api_task.runs_on == model.Task.RUNS_ON_SOURCE

    def test_target_relationship_operation_task_creation(self, ctx):
        operation_name = 'aria.interfaces.relationship_lifecycle.preconfigure'
        op_details = {'operation': True, 'plugin': 'plugin'}
        relationship = ctx.model.relationship.list()[0]
        relationship.target_operations[operation_name] = op_details
        relationship.target_node.plugins = [{'name': 'plugin',
                                             'package_name': 'package',
                                             'package_version': '0.1'}]
        relationship_instance = ctx.model.relationship_instance.list()[0]
        inputs = {'inputs': True}
        max_attempts = 10
        retry_interval = 10

        with context.workflow.current.push(ctx):
            api_task = api.task.OperationTask.relationship_instance(
                name=operation_name,
                instance=relationship_instance,
                operation_end=api.task.OperationTask.TARGET_OPERATION,
                inputs=inputs,
                max_attempts=max_attempts,
                retry_interval=retry_interval)

        assert api_task.name == '{0}.{1}'.format(operation_name, relationship_instance.id)
        assert api_task.operation_mapping is True
        assert api_task.actor == relationship_instance
        assert api_task.inputs == inputs
        assert api_task.retry_interval == retry_interval
        assert api_task.max_attempts == max_attempts
        assert api_task.plugin == {'name': 'plugin',
                                   'package_name': 'package',
                                   'package_version': '0.1'}
        assert api_task.runs_on == model.Task.RUNS_ON_TARGET

    def test_operation_task_default_values(self, ctx):
        dependency_node_instance = ctx.model.node_instance.get_by_name(
            mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
        with context.workflow.current.push(ctx):
            task = api.task.OperationTask(
                name='stub',
                operation_mapping='',
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
