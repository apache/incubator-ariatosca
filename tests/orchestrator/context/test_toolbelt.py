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

from aria import workflow, operation
from aria.orchestrator import context
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.executor import thread
from aria.orchestrator.context.toolbelt import RelationshipToolBelt

from tests import mock, storage
from . import (
    op_path,
    op_name,
    execute,
)

global_test_holder = {}


@pytest.fixture
def workflow_context(tmpdir):
    context = mock.context.simple(str(tmpdir), inmemory=True)
    yield context
    storage.release_sqlite_storage(context.model)


@pytest.fixture
def executor():
    result = thread.ThreadExecutor()
    try:
        yield result
    finally:
        result.close()


def _get_elements(workflow_context):
    dependency_node_template = workflow_context.model.node_template.get_by_name(
        mock.models.DEPENDENCY_NODE_NAME)
    dependency_node_template.host = dependency_node_template
    workflow_context.model.node.update(dependency_node_template)

    dependency_node = workflow_context.model.node.get_by_name(
        mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
    dependency_node.host_fk = dependency_node.id
    workflow_context.model.node.update(dependency_node)

    dependent_node_template = workflow_context.model.node_template.get_by_name(
        mock.models.DEPENDENT_NODE_NAME)
    dependent_node_template.host = dependency_node_template
    workflow_context.model.node_template.update(dependent_node_template)

    dependent_node = workflow_context.model.node.get_by_name(
        mock.models.DEPENDENT_NODE_INSTANCE_NAME)
    dependent_node.host = dependent_node
    workflow_context.model.node.update(dependent_node)

    relationship = workflow_context.model.relationship.list()[0]
    return dependency_node_template, dependency_node, dependent_node_template, dependent_node, \
        relationship


def test_host_ip(workflow_context, executor):
    operation_name = 'aria.interfaces.lifecycle.create'
    _, dependency_node, _, _, _ = _get_elements(workflow_context)
    dependency_node.interfaces = [mock.models.get_interface(
        operation_name,
        operation_kwargs=dict(implementation=op_path(host_ip, module_path=__name__))
    )]
    workflow_context.model.node.update(dependency_node)
    inputs = {'putput': True}

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask.node(
                instance=dependency_node,
                name=operation_name,
                inputs=inputs
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=workflow_context, executor=executor)

    assert global_test_holder.get('host_ip') == dependency_node.runtime_properties.get('ip')


def test_relationship_tool_belt(workflow_context, executor):
    operation_name = 'aria.interfaces.relationship_lifecycle.post_configure'
    _, _, _, _, relationship = _get_elements(workflow_context)
    relationship.interfaces = [
        mock.models.get_interface(
            operation_name,
            operation_kwargs=dict(
                implementation=op_path(relationship_operation, module_path=__name__)),
            edge='source')
    ]
    workflow_context.model.relationship.update(relationship)

    inputs = {'putput': True}

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask.relationship(
                instance=relationship,
                name=operation_name,
                edge='source',
                inputs=inputs
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=workflow_context, executor=executor)

    assert isinstance(global_test_holder.get(op_name(relationship, operation_name)),
                      RelationshipToolBelt)


def test_wrong_model_toolbelt():
    with pytest.raises(RuntimeError):
        context.toolbelt(None)


@operation(toolbelt=True)
def host_ip(toolbelt, **_):
    global_test_holder['host_ip'] = toolbelt.host_ip


@operation(toolbelt=True)
def relationship_operation(ctx, toolbelt, **_):
    global_test_holder[ctx.name] = toolbelt


@pytest.fixture(autouse=True)
def cleanup():
    global_test_holder.clear()
