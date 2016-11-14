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

from aria import context
from aria.workflows import api

from ... import mock


@pytest.fixture()
def ctx():
    """
    Create the following graph in storage:
    dependency_node <------ dependent_node
    :return:
    """
    simple_context = mock.context.simple()
    dependency_node = mock.models.get_dependency_node()
    dependency_node_instance = mock.models.get_dependency_node_instance(
        dependency_node=dependency_node)

    relationship = mock.models.get_relationship(dependency_node)
    relationship_instance = mock.models.get_relationship_instance(
        relationship=relationship,
        target_instance=dependency_node_instance
    )

    dependent_node = mock.models.get_dependent_node(relationship)
    dependent_node_instance = mock.models.get_dependent_node_instance(
        dependent_node=dependent_node,
        relationship_instance=relationship_instance
    )

    simple_context.model.node.store(dependent_node)
    simple_context.model.node.store(dependency_node)
    simple_context.model.node_instance.store(dependent_node_instance)
    simple_context.model.node_instance.store(dependency_node_instance)
    simple_context.model.relationship.store(relationship)
    simple_context.model.relationship_instance.store(relationship_instance)
    simple_context.model.execution.store(mock.models.get_execution())
    simple_context.model.deployment.store(mock.models.get_deployment())

    return simple_context


class TestOperationTask(object):

    def test_operation_task_creation(self):
        workflow_context = mock.context.simple()

        name = 'task_name'
        op_details = {'operation_details': True}
        node_instance = mock.models.get_dependency_node_instance()
        inputs = {'inputs': True}
        max_attempts = 10
        retry_interval = 10
        ignore_failure = True

        with context.workflow.current.push(workflow_context):
            model_task = api.task.OperationTask(name=name,
                                                operation_details=op_details,
                                                node_instance=node_instance,
                                                inputs=inputs,
                                                max_attempts=max_attempts,
                                                retry_interval=retry_interval,
                                                ignore_failure=ignore_failure)

        assert model_task.name == name
        assert model_task.operation_details == op_details
        assert model_task.node_instance == node_instance
        assert model_task.inputs == inputs
        assert model_task.retry_interval == retry_interval
        assert model_task.max_attempts == max_attempts
        assert model_task.ignore_failure == ignore_failure

    def test_operation_task_default_values(self):
        workflow_context = mock.context.simple(task_ignore_failure=True)
        with context.workflow.current.push(workflow_context):
            model_task = api.task.OperationTask(
                name='stub',
                operation_details={},
                node_instance=mock.models.get_dependency_node_instance())

        assert model_task.inputs == {}
        assert model_task.retry_interval == workflow_context.task_retry_interval
        assert model_task.max_attempts == workflow_context.task_max_attempts
        assert model_task.ignore_failure == workflow_context.task_ignore_failure


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
