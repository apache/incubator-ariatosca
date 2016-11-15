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

from aria import (
    workflow,
    operation,
)
from aria.orchestrator import context
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.executor import thread

from tests import mock
from . import (
    op_path,
    op_name,
    execute,
)

global_test_holder = {}


@pytest.fixture
def ctx():
    return mock.context.simple()


@pytest.fixture
def executor():
    result = thread.ThreadExecutor()
    try:
        yield result
    finally:
        result.close()


def test_node_operation_task_execution(ctx, executor):
    operation_name = 'aria.interfaces.lifecycle.create'

    node = mock.models.get_dependency_node()
    node.operations[operation_name] = {
        'operation': op_path(my_operation, module_path=__name__)

    }
    node_instance = mock.models.get_dependency_node_instance(node)
    ctx.model.node.store(node)
    ctx.model.node_instance.store(node_instance)

    inputs = {'putput': True}

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask.node_instance(
                name=operation_name,
                instance=node_instance,
                inputs=inputs
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)

    operation_context = global_test_holder[op_name(node_instance, operation_name)]

    assert isinstance(operation_context, context.operation.NodeOperationContext)

    # Task bases assertions
    assert operation_context.task.actor == node_instance
    assert operation_context.task.name == op_name(node_instance, operation_name)
    assert operation_context.task.operation_mapping == node.operations[operation_name]['operation']
    assert operation_context.task.inputs == inputs

    # Context based attributes (sugaring)
    assert operation_context.node == node_instance.node
    assert operation_context.node_instance == node_instance


def test_relationship_operation_task_execution(ctx, executor):
    operation_name = 'aria.interfaces.relationship_lifecycle.postconfigure'

    dependency_node = mock.models.get_dependency_node()
    dependency_node_instance = mock.models.get_dependency_node_instance()
    relationship = mock.models.get_relationship(target=dependency_node)
    relationship.source_operations[operation_name] = {
        'operation': op_path(my_operation, module_path=__name__)
    }
    relationship_instance = mock.models.get_relationship_instance(
        target_instance=dependency_node_instance,
        relationship=relationship)
    dependent_node = mock.models.get_dependent_node()
    dependent_node_instance = mock.models.get_dependent_node_instance(
        relationship_instance=relationship_instance,
        dependent_node=dependency_node)
    ctx.model.node.store(dependency_node)
    ctx.model.node_instance.store(dependency_node_instance)
    ctx.model.relationship.store(relationship)
    ctx.model.relationship_instance.store(relationship_instance)
    ctx.model.node.store(dependent_node)
    ctx.model.node_instance.store(dependent_node_instance)

    inputs = {'putput': True}

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask.relationship_instance(
                instance=relationship_instance,
                name=operation_name,
                operation_end=api.task.OperationTask.SOURCE_OPERATION,
                inputs=inputs
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)

    operation_context = global_test_holder[op_name(relationship_instance, operation_name)]

    assert isinstance(operation_context, context.operation.RelationshipOperationContext)

    # Task bases assertions
    assert operation_context.task.actor == relationship_instance
    assert operation_context.task.name == op_name(relationship_instance, operation_name)
    assert operation_context.task.operation_mapping == \
           relationship.source_operations[operation_name]['operation']
    assert operation_context.task.inputs == inputs

    # Context based attributes (sugaring)
    assert operation_context.target_node == dependency_node
    assert operation_context.target_node_instance == dependency_node_instance
    assert operation_context.relationship == relationship
    assert operation_context.relationship_instance == relationship_instance
    assert operation_context.source_node == dependent_node
    assert operation_context.source_node_instance == dependent_node_instance


@operation
def my_operation(ctx, **_):
    global_test_holder[ctx.name] = ctx


@pytest.fixture(autouse=True)
def cleanup():
    global_test_holder.clear()
