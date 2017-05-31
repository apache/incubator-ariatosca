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
from aria.modeling import models
from aria.orchestrator import context
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.executor import thread

from tests import (
    mock,
    storage,
    helpers
)
from . import (
    op_path,
    execute,
)


@pytest.fixture
def workflow_context(tmpdir):
    context = mock.context.simple(str(tmpdir))
    yield context
    storage.release_sqlite_storage(context.model)


@pytest.fixture
def executor():
    result = thread.ThreadExecutor()
    try:
        yield result
    finally:
        result.close()


@pytest.fixture
def dataholder(tmpdir):
    dataholder_path = str(tmpdir.join('dataholder'))
    holder = helpers.FilesystemDataHolder(dataholder_path)
    return holder


def _get_elements(workflow_context):
    dependency_node_template = workflow_context.model.node_template.get_by_name(
        mock.models.DEPENDENCY_NODE_TEMPLATE_NAME)
    dependency_node_template.host = dependency_node_template
    workflow_context.model.node.update(dependency_node_template)

    dependency_node = workflow_context.model.node.get_by_name(
        mock.models.DEPENDENCY_NODE_NAME)
    dependency_node.host_fk = dependency_node.id
    workflow_context.model.node.update(dependency_node)

    dependent_node_template = workflow_context.model.node_template.get_by_name(
        mock.models.DEPENDENT_NODE_TEMPLATE_NAME)
    dependent_node_template.host = dependency_node_template
    workflow_context.model.node_template.update(dependent_node_template)

    dependent_node = workflow_context.model.node.get_by_name(
        mock.models.DEPENDENT_NODE_NAME)
    dependent_node.host = dependent_node
    workflow_context.model.node.update(dependent_node)

    relationship = workflow_context.model.relationship.list()[0]
    return dependency_node_template, dependency_node, dependent_node_template, dependent_node, \
        relationship


def test_host_ip(workflow_context, executor, dataholder):

    interface_name = 'Standard'
    operation_name = 'create'
    _, dependency_node, _, _, _ = _get_elements(workflow_context)
    arguments = {'putput': True, 'holder_path': dataholder.path}
    interface = mock.models.create_interface(
        dependency_node.service,
        interface_name=interface_name,
        operation_name=operation_name,
        operation_kwargs=dict(function=op_path(host_ip, module_path=__name__), arguments=arguments)
    )
    dependency_node.interfaces[interface.name] = interface
    dependency_node.attributes['ip'] = models.Parameter.wrap('ip', '1.1.1.1')

    workflow_context.model.node.update(dependency_node)

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask(
                dependency_node,
                interface_name=interface_name,
                operation_name=operation_name,
                arguments=arguments
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=workflow_context, executor=executor)

    assert dataholder.get('host_ip') == dependency_node.attributes.get('ip').value


def test_relationship_tool_belt(workflow_context, executor, dataholder):
    interface_name = 'Configure'
    operation_name = 'post_configure'
    _, _, _, _, relationship = _get_elements(workflow_context)
    arguments = {'putput': True, 'holder_path': dataholder.path}
    interface = mock.models.create_interface(
        relationship.source_node.service,
        interface_name=interface_name,
        operation_name=operation_name,
        operation_kwargs=dict(function=op_path(relationship_operation, module_path=__name__),
                              arguments=arguments)
    )
    relationship.interfaces[interface.name] = interface
    workflow_context.model.relationship.update(relationship)

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask(
                relationship,
                interface_name=interface_name,
                operation_name=operation_name,
                arguments=arguments
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=workflow_context, executor=executor)

    assert dataholder.get(api.task.OperationTask.NAME_FORMAT.format(
        type='relationship',
        name=relationship.name,
        interface=interface_name,
        operation=operation_name)) == relationship.source_node.name


def test_wrong_model_toolbelt():
    with pytest.raises(RuntimeError):
        context.toolbelt(None)


@operation(toolbelt=True)
def host_ip(toolbelt, holder_path, **_):
    helpers.FilesystemDataHolder(holder_path)['host_ip'] = toolbelt.host_ip


@operation(toolbelt=True)
def relationship_operation(ctx, toolbelt, holder_path, **_):
    helpers.FilesystemDataHolder(holder_path)[ctx.name] = toolbelt._op_context.source_node.name
