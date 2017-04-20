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
import time

import pytest

from aria.orchestrator.workflows.executor import process, thread

from aria import (
    workflow,
    operation,
)
from aria.orchestrator import context
from aria.orchestrator.workflows import api

import tests
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
def ctx(tmpdir):
    context = mock.context.simple(
        str(tmpdir),
        context_kwargs=dict(workdir=str(tmpdir.join('workdir')))
    )
    yield context
    storage.release_sqlite_storage(context.model)


@pytest.fixture
def process_executor():
    ex = process.ProcessExecutor(**dict(python_path=tests.ROOT_DIR))
    try:
        yield ex
    finally:
        ex.close()


@pytest.fixture
def thread_executor():
    ex = thread.ThreadExecutor()
    try:
        yield ex
    finally:
        ex.close()


@pytest.fixture
def dataholder(tmpdir):
    dataholder_path = str(tmpdir.join('dataholder'))
    holder = helpers.FilesystemDataHolder(dataholder_path)
    return holder


def test_node_operation_task_execution(ctx, thread_executor, dataholder):
    interface_name = 'Standard'
    operation_name = 'create'

    arguments = {'putput': True, 'holder_path': dataholder.path}
    node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    interface = mock.models.create_interface(
        node.service,
        interface_name,
        operation_name,
        operation_kwargs=dict(function=op_path(basic_node_operation, module_path=__name__),
                              arguments=arguments)
    )
    node.interfaces[interface.name] = interface
    ctx.model.node.update(node)

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask(
                node,
                interface_name=interface_name,
                operation_name=operation_name,
                arguments=arguments
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=thread_executor)

    assert dataholder['ctx_name'] == context.operation.NodeOperationContext.__name__

    # Task bases assertions
    assert dataholder['actor_name'] == node.name
    assert dataholder['task_name'] == api.task.OperationTask.NAME_FORMAT.format(
        type='node',
        name=node.name,
        interface=interface_name,
        operation=operation_name
    )
    operations = interface.operations
    assert len(operations) == 1
    assert dataholder['function'] == operations.values()[0].function             # pylint: disable=no-member
    assert dataholder['arguments']['putput'] is True

    # Context based attributes (sugaring)
    assert dataholder['template_name'] == node.node_template.name
    assert dataholder['node_name'] == node.name


def test_relationship_operation_task_execution(ctx, thread_executor, dataholder):
    interface_name = 'Configure'
    operation_name = 'post_configure'

    arguments = {'putput': True, 'holder_path': dataholder.path}
    relationship = ctx.model.relationship.list()[0]
    interface = mock.models.create_interface(
        relationship.source_node.service,
        interface_name,
        operation_name,
        operation_kwargs=dict(function=op_path(basic_relationship_operation, module_path=__name__),
                              arguments=arguments),
    )

    relationship.interfaces[interface.name] = interface
    ctx.model.relationship.update(relationship)

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

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=thread_executor)

    assert dataholder['ctx_name'] == context.operation.RelationshipOperationContext.__name__

    # Task bases assertions
    assert dataholder['actor_name'] == relationship.name
    assert interface_name in dataholder['task_name']
    operations = interface.operations
    assert dataholder['function'] == operations.values()[0].function           # pylint: disable=no-member
    assert dataholder['arguments']['putput'] is True

    # Context based attributes (sugaring)
    dependency_node_template = ctx.model.node_template.get_by_name(
        mock.models.DEPENDENCY_NODE_TEMPLATE_NAME)
    dependency_node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    dependent_node_template = ctx.model.node_template.get_by_name(
        mock.models.DEPENDENT_NODE_TEMPLATE_NAME)
    dependent_node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)

    assert dataholder['target_node_template_name'] == dependency_node_template.name
    assert dataholder['target_node_name'] == dependency_node.name
    assert dataholder['relationship_name'] == relationship.name
    assert dataholder['source_node_template_name'] == dependent_node_template.name
    assert dataholder['source_node_name'] == dependent_node.name


def test_invalid_task_operation_id(ctx, thread_executor, dataholder):
    """
    Checks that the right id is used. The task created with id == 1, thus running the task on
    node with id == 2. will check that indeed the node uses the correct id.
    :param ctx:
    :param thread_executor:
    :return:
    """
    interface_name = 'Standard'
    operation_name = 'create'

    other_node, node = ctx.model.node.list()
    assert other_node.id == 1
    assert node.id == 2

    interface = mock.models.create_interface(
        node.service,
        interface_name=interface_name,
        operation_name=operation_name,
        operation_kwargs=dict(function=op_path(get_node_id, module_path=__name__),
                              arguments={'holder_path': dataholder.path})
    )
    node.interfaces[interface.name] = interface
    ctx.model.node.update(node)

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask(
                node,
                interface_name=interface_name,
                operation_name=operation_name,
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=thread_executor)

    op_node_id = dataholder[api.task.OperationTask.NAME_FORMAT.format(
        type='node',
        name=node.name,
        interface=interface_name,
        operation=operation_name
    )]
    assert op_node_id == node.id
    assert op_node_id != other_node.id


def test_plugin_workdir(ctx, thread_executor, tmpdir):
    interface_name = 'Standard'
    operation_name = 'create'

    plugin = mock.models.create_plugin()
    ctx.model.plugin.put(plugin)
    node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    filename = 'test_file'
    content = 'file content'
    arguments = {'filename': filename, 'content': content}
    interface = mock.models.create_interface(
        node.service,
        interface_name,
        operation_name,
        operation_kwargs=dict(
            function='{0}.{1}'.format(__name__, _test_plugin_workdir.__name__),
            plugin=plugin,
            arguments=arguments)
    )
    node.interfaces[interface.name] = interface
    ctx.model.node.update(node)

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=operation_name,
            arguments=arguments))

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=thread_executor)
    expected_file = tmpdir.join('workdir', 'plugins', str(ctx.service.id),
                                plugin.name,
                                filename)
    assert expected_file.read() == content


@pytest.fixture(params=[
    (thread.ThreadExecutor, {}),
    (process.ProcessExecutor, {'python_path': [tests.ROOT_DIR]}),
])
def executor(request):
    executor_cls, executor_kwargs = request.param
    result = executor_cls(**executor_kwargs)
    try:
        yield result
    finally:
        result.close()


def test_node_operation_logging(ctx, executor):
    interface_name, operation_name = mock.operations.NODE_OPERATIONS_INSTALL[0]

    node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)

    arguments = {
        'op_start': 'op_start',
        'op_end': 'op_end',
    }
    interface = mock.models.create_interface(
        node.service,
        interface_name,
        operation_name,
        operation_kwargs=dict(
            function=op_path(logged_operation, module_path=__name__),
            arguments=arguments)
    )
    node.interfaces[interface.name] = interface
    ctx.model.node.update(node)

    @workflow
    def basic_workflow(graph, **_):
        graph.add_tasks(
            api.task.OperationTask(
                node,
                interface_name=interface_name,
                operation_name=operation_name,
                arguments=arguments
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)
    _assert_loggins(ctx, arguments)


def test_relationship_operation_logging(ctx, executor):
    interface_name, operation_name = mock.operations.RELATIONSHIP_OPERATIONS_INSTALL[0]

    relationship = ctx.model.relationship.list()[0]
    arguments = {
        'op_start': 'op_start',
        'op_end': 'op_end',
    }
    interface = mock.models.create_interface(
        relationship.source_node.service,
        interface_name,
        operation_name,
        operation_kwargs=dict(function=op_path(logged_operation, module_path=__name__),
                              arguments=arguments)
    )
    relationship.interfaces[interface.name] = interface
    ctx.model.relationship.update(relationship)

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

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)
    _assert_loggins(ctx, arguments)


def test_attribute_consumption(ctx, executor, dataholder):
    # region Updating node operation
    node_int_name, node_op_name = mock.operations.NODE_OPERATIONS_INSTALL[0]

    source_node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)

    arguments = {'dict_': {'key': 'value'},
                 'set_test_dict': {'key2': 'value2'}}
    interface = mock.models.create_interface(
        source_node.service,
        node_int_name,
        node_op_name,
        operation_kwargs=dict(
            function=op_path(attribute_altering_operation, module_path=__name__),
            arguments=arguments)
    )
    source_node.interfaces[interface.name] = interface
    ctx.model.node.update(source_node)
    # endregion

    # region updating relationship operation
    rel_int_name, rel_op_name = mock.operations.RELATIONSHIP_OPERATIONS_INSTALL[2]

    relationship = ctx.model.relationship.list()[0]
    interface = mock.models.create_interface(
        relationship.source_node.service,
        rel_int_name,
        rel_op_name,
        operation_kwargs=dict(
            function=op_path(attribute_consuming_operation, module_path=__name__),
            arguments={'holder_path': dataholder.path}
        )
    )
    relationship.interfaces[interface.name] = interface
    ctx.model.relationship.update(relationship)
    # endregion

    @workflow
    def basic_workflow(graph, **_):
        graph.sequence(
            api.task.OperationTask(
                source_node,
                interface_name=node_int_name,
                operation_name=node_op_name,
                arguments=arguments
            ),
            api.task.OperationTask(
                relationship,
                interface_name=rel_int_name,
                operation_name=rel_op_name,
            )
        )

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)
    target_node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)

    assert len(source_node.attributes) == len(target_node.attributes) == 2
    assert source_node.attributes['key'] != target_node.attributes['key']
    assert source_node.attributes['key'].value == \
           target_node.attributes['key'].value == \
           dataholder['key'] == 'value'

    assert source_node.attributes['key2'] != target_node.attributes['key2']
    assert source_node.attributes['key2'].value == \
           target_node.attributes['key2'].value == \
           dataholder['key2'] == 'value2'


def _assert_loggins(ctx, arguments):
    # The logs should contain the following: Workflow Start, Operation Start, custom operation
    # log string (op_start), custom operation log string (op_end), Operation End, Workflow End.

    executions = ctx.model.execution.list()
    assert len(executions) == 1
    execution = executions[0]

    tasks = ctx.model.task.list()
    assert len(tasks) == 1
    task = tasks[0]
    assert len(task.logs) == 4

    logs = ctx.model.log.list()
    assert len(logs) == len(execution.logs) == 6
    assert set(logs) == set(execution.logs)

    assert all(l.execution == execution for l in logs)
    assert all(l in logs and l.task == task for l in task.logs)

    op_start_log = [l for l in logs if arguments['op_start'] in l.msg and l.level.lower() == 'info']
    assert len(op_start_log) == 1
    op_start_log = op_start_log[0]

    op_end_log = [l for l in logs if arguments['op_end'] in l.msg and l.level.lower() == 'debug']
    assert len(op_end_log) == 1
    op_end_log = op_end_log[0]

    assert op_start_log.created_at < op_end_log.created_at


@operation
def logged_operation(ctx, **_):
    ctx.logger.info(ctx.task.arguments['op_start'].value)
    # enables to check the relation between the created_at field properly
    time.sleep(1)
    ctx.logger.debug(ctx.task.arguments['op_end'].value)


@operation
def basic_node_operation(ctx, holder_path, **_):
    holder = helpers.FilesystemDataHolder(holder_path)

    operation_common(ctx, holder)
    holder['template_name'] = ctx.node_template.name
    holder['node_name'] = ctx.node.name


@operation
def basic_relationship_operation(ctx, holder_path, **_):
    holder = helpers.FilesystemDataHolder(holder_path)

    operation_common(ctx, holder)
    holder['target_node_template_name'] = ctx.target_node_template.name
    holder['target_node_name'] = ctx.target_node.name
    holder['relationship_name'] = ctx.relationship.name
    holder['source_node_template_name'] = ctx.source_node_template.name
    holder['source_node_name'] = ctx.source_node.name


def operation_common(ctx, holder):
    holder['ctx_name'] = ctx.__class__.__name__

    holder['actor_name'] = ctx.task.actor.name
    holder['task_name'] = ctx.task.name
    holder['function'] = ctx.task.function
    holder['arguments'] = dict(i.unwrapped for i in ctx.task.arguments.values())


@operation
def get_node_id(ctx, holder_path, **_):
    helpers.FilesystemDataHolder(holder_path)[ctx.name] = ctx.node.id


@operation
def _test_plugin_workdir(ctx, filename, content):
    with open(os.path.join(ctx.plugin_workdir, filename), 'w') as f:
        f.write(content)


@operation
def attribute_altering_operation(ctx, dict_, set_test_dict, **_):
    ctx.node.attributes.update(dict_)

    for key, value in set_test_dict.items():
        ctx.node.attributes[key] = value


@operation
def attribute_consuming_operation(ctx, holder_path, **_):
    holder = helpers.FilesystemDataHolder(holder_path)
    ctx.target_node.attributes.update(ctx.source_node.attributes)
    holder.update(**ctx.target_node.attributes)

    ctx.target_node.attributes['key2'] = ctx.source_node.attributes['key2']
    holder['key2'] = ctx.target_node.attributes['key2']
