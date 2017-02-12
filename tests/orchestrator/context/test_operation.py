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
    context = mock.context.simple(
        str(tmpdir.join('workdir')),
        inmemory=True,
        context_kwargs=dict(workdir=str(tmpdir.join('workdir')))
    )
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

    node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
    interface = mock.models.get_interface(
        operation_name,
        operation_kwargs=dict(implementation=op_path(my_operation, module_path=__name__))
    )
    node.interfaces = [interface]
    ctx.model.node.update(node)
    inputs = {'putput': True}

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask.node(
                name=operation_name,
                instance=node,
                inputs=inputs
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)

    operation_context = global_test_holder[op_name(node, operation_name)]

    assert isinstance(operation_context, context.operation.NodeOperationContext)

    # Task bases assertions
    assert operation_context.task.actor == node
    assert operation_context.task.name == op_name(node, operation_name)
    operations = interface.operations.filter_by(name=operation_name)                                # pylint: disable=no-member
    assert operations.count() == 1
    assert operation_context.task.implementation == operations[0].implementation
    assert operation_context.task.inputs == inputs

    # Context based attributes (sugaring)
    assert operation_context.node_template == node.node_template
    assert operation_context.node == node


def test_relationship_operation_task_execution(ctx, executor):
    operation_name = 'aria.interfaces.relationship_lifecycle.post_configure'
    relationship = ctx.model.relationship.list()[0]

    interface = mock.models.get_interface(
        operation_name=operation_name,
        operation_kwargs=dict(implementation=op_path(my_operation, module_path=__name__)),
        edge='source'
    )

    relationship.interfaces = [interface]
    ctx.model.relationship.update(relationship)
    inputs = {'putput': True}

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask.relationship(
                instance=relationship,
                name=operation_name,
                inputs=inputs,
                edge='source'
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)

    operation_context = global_test_holder[op_name(relationship,
                                                   operation_name)]

    assert isinstance(operation_context, context.operation.RelationshipOperationContext)

    # Task bases assertions
    assert operation_context.task.actor == relationship
    assert operation_context.task.name.startswith(operation_name)
    operation = interface.operations.filter_by(name=operation_name)                                 # pylint: disable=no-member
    assert operation_context.task.implementation == operation.all()[0].implementation
    assert operation_context.task.inputs == inputs

    # Context based attributes (sugaring)
    dependency_node_template = ctx.model.node_template.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    dependency_node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
    dependent_node_template = ctx.model.node_template.get_by_name(mock.models.DEPENDENT_NODE_NAME)
    dependent_node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_INSTANCE_NAME)

    assert operation_context.target_node_template == dependency_node_template
    assert operation_context.target_node == dependency_node
    assert operation_context.relationship == relationship
    assert operation_context.source_node_template == dependent_node_template
    assert operation_context.source_node == dependent_node


def test_invalid_task_operation_id(ctx, executor):
    """
    Checks that the right id is used. The task created with id == 1, thus running the task on
    node_instance with id == 2. will check that indeed the node_instance uses the correct id.
    :param ctx:
    :param executor:
    :return:
    """
    operation_name = 'aria.interfaces.lifecycle.create'
    other_node, node = ctx.model.node.list()
    assert other_node.id == 1
    assert node.id == 2

    interface = mock.models.get_interface(
        operation_name=operation_name,
        operation_kwargs=dict(implementation=op_path(get_node_instance_id, module_path=__name__))
    )
    node.interfaces = [interface]
    ctx.model.node.update(node)

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask.node(name=operation_name, instance=node)
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)

    op_node_instance_id = global_test_holder[op_name(node, operation_name)]
    assert op_node_instance_id == node.id
    assert op_node_instance_id != other_node.id


def test_plugin_workdir(ctx, executor, tmpdir):
    op = 'test.op'
    plugin_name = 'mock_plugin'
    node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
    node.interfaces = [mock.models.get_interface(
        op,
        operation_kwargs=dict(
            implementation='{0}.{1}'.format(__name__, _test_plugin_workdir.__name__),
            plugin=plugin_name)
    )]
    node.plugins = [{'name': plugin_name}]
    ctx.model.node.update(node)

    filename = 'test_file'
    content = 'file content'
    inputs = {'filename': filename, 'content': content}

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(api.task.OperationTask.node(
            name=op, instance=node, inputs=inputs))

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)
    expected_file = tmpdir.join('workdir', 'plugins', str(ctx.service_instance.id),
                                plugin_name,
                                filename)
    assert expected_file.read() == content


@operation
def my_operation(ctx, **_):
    global_test_holder[ctx.name] = ctx


@operation
def get_node_instance_id(ctx, **_):
    global_test_holder[ctx.name] = ctx.node.id


@operation
def _test_plugin_workdir(ctx, filename, content):
    with open(os.path.join(ctx.plugin_workdir, filename), 'w') as f:
        f.write(content)


@pytest.fixture(autouse=True)
def cleanup():
    global_test_holder.clear()
