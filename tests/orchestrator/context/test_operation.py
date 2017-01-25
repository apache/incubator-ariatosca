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

import pytest

from aria import (
    workflow,
    operation,
)
from aria.orchestrator import context
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.executor import thread

from tests import mock, storage
from . import (
    op_path,
    op_name,
    execute,
)

global_test_holder = {}


@pytest.fixture
def ctx(tmpdir):
    context = mock.context.simple(storage.get_sqlite_api_kwargs(str(tmpdir)),
                                  workdir=str(tmpdir.join('workdir')))
    yield context
    storage.release_sqlite_storage(context.model)


@pytest.fixture
def executor():
    result = thread.ThreadExecutor()
    try:
        yield result
    finally:
        result.close()


def test_node_operation_task_execution(ctx, executor):
    operation_name = 'aria.interfaces.lifecycle.create'

    node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    node.operations[operation_name] = {
        'operation': op_path(my_operation, module_path=__name__)

    }
    ctx.model.node.update(node)
    node_instance = ctx.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)

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
    relationship = ctx.model.relationship.list()[0]
    relationship.source_operations[operation_name] = {
        'operation': op_path(my_operation, module_path=__name__)
    }
    ctx.model.relationship.update(relationship)
    relationship_instance = ctx.model.relationship_instance.list()[0]

    dependency_node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    dependency_node_instance = \
        ctx.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
    dependent_node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)
    dependent_node_instance = \
        ctx.model.node_instance.get_by_name(mock.models.DEPENDENT_NODE_INSTANCE_NAME)

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


def test_invalid_task_operation_id(ctx, executor):
    """
    Checks that the right id is used. The task created with id == 1, thus running the task on
    node_instance with id == 2. will check that indeed the node_instance uses the correct id.
    :param ctx:
    :param executor:
    :return:
    """
    operation_name = 'aria.interfaces.lifecycle.create'
    other_node_instance, node_instance = ctx.model.node_instance.list()
    assert other_node_instance.id == 1
    assert node_instance.id == 2

    node = node_instance.node
    node.operations[operation_name] = {
        'operation': op_path(get_node_instance_id, module_path=__name__)

    }
    ctx.model.node.update(node)

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask.node_instance(name=operation_name, instance=node_instance)
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)

    op_node_instance_id = global_test_holder[op_name(node_instance, operation_name)]
    assert op_node_instance_id == node_instance.id
    assert op_node_instance_id != other_node_instance.id


def test_plugin_workdir(ctx, executor, tmpdir):
    op = 'test.op'
    plugin_name = 'mock_plugin'
    node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    node.operations[op] = {'operation': '{0}.{1}'.format(__name__, _test_plugin_workdir.__name__),
                           'plugin': plugin_name}
    node.plugins = [{'name': plugin_name}]
    ctx.model.node.update(node)
    node_instance = ctx.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)

    filename = 'test_file'
    content = 'file content'
    inputs = {'filename': filename, 'content': content}

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(api.task.OperationTask.node_instance(
            name=op, instance=node_instance, inputs=inputs))

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)
    expected_file = tmpdir.join('workdir', 'plugins', str(ctx.deployment.id), plugin_name, filename)
    assert expected_file.read() == content


@operation
def my_operation(ctx, **_):
    global_test_holder[ctx.name] = ctx


@operation
def get_node_instance_id(ctx, **_):
    global_test_holder[ctx.name] = ctx.node_instance.id


@operation
def _test_plugin_workdir(ctx, filename, content):
    with open(os.path.join(ctx.plugin_workdir, filename), 'w') as f:
        f.write(content)


@pytest.fixture(autouse=True)
def cleanup():
    global_test_holder.clear()
