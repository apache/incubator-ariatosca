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

from aria.orchestrator.decorators import operation, workflow
from aria.orchestrator.workflows.core import engine, graph_compiler
from aria.orchestrator.workflows.executor.thread import ThreadExecutor
from aria.orchestrator.workflows import api
from aria.modeling.service_instance import NodeBase

from tests import mock, storage

global_test_dict = {}  # used to capture transitional node state changes


@pytest.fixture
def ctx(tmpdir):
    context = mock.context.simple(str(tmpdir))
    yield context
    storage.release_sqlite_storage(context.model)

# TODO another possible approach of writing these tests:
# Don't create a ctx for every test.
# Problem is, that if for every test we create a workflow that contains just one standard
# lifecycle operation, then by the time we try to run the second test, the workflow failes since
# the execution tries to go from 'terminated' to 'pending'.
# And if we write a workflow that contains all the lifecycle operations, then first we need to
# change the api of `mock.models.create_interface`, which a lot of other tests use, and second how
# do we check all the state transition during the workflow execution in a convenient way.

TYPE_URI_NAME = 'tosca.interfaces.node.lifecycle.Standard'
SHORTHAND_NAME = 'Standard'
TYPE_QUALIFIED_NAME = 'tosca:Standard'


def test_node_state_changes_as_a_result_of_standard_lifecycle_create(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_URI_NAME, op_name='create')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'create')


def test_node_state_changes_as_a_result_of_standard_lifecycle_configure(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_URI_NAME, op_name='configure')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'configure')


def test_node_state_changes_as_a_result_of_standard_lifecycle_start(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_URI_NAME, op_name='start')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'start')


def test_node_state_changes_as_a_result_of_standard_lifecycle_stop(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_URI_NAME, op_name='stop')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'stop')


def test_node_state_changes_as_a_result_of_standard_lifecycle_delete(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_URI_NAME, op_name='delete')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'delete')


def test_node_state_changes_as_a_result_of_standard_lifecycle_create_shorthand_name(ctx):
    node = run_operation_on_node(ctx, interface_name=SHORTHAND_NAME, op_name='create')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'create')


def test_node_state_changes_as_a_result_of_standard_lifecycle_configure_shorthand_name(ctx):
    node = run_operation_on_node(ctx, interface_name=SHORTHAND_NAME, op_name='configure')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'configure')


def test_node_state_changes_as_a_result_of_standard_lifecycle_start_shorthand_name(ctx):
    node = run_operation_on_node(ctx, interface_name=SHORTHAND_NAME, op_name='start')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'start')


def test_node_state_changes_as_a_result_of_standard_lifecycle_stop_shorthand_name(ctx):
    node = run_operation_on_node(ctx, interface_name=SHORTHAND_NAME, op_name='stop')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'stop')


def test_node_state_changes_as_a_result_of_standard_lifecycle_delete_shorthand_name(ctx):
    node = run_operation_on_node(ctx, interface_name=SHORTHAND_NAME, op_name='delete')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'delete')

def test_node_state_changes_as_a_result_of_standard_lifecycle_create_typequalified_name(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_QUALIFIED_NAME, op_name='create')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'create')


def test_node_state_changes_as_a_result_of_standard_lifecycle_configure_typequalified_name(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_QUALIFIED_NAME, op_name='configure')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'configure')


def test_node_state_changes_as_a_result_of_standard_lifecycle_start_typequalified_name(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_QUALIFIED_NAME, op_name='start')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'start')


def test_node_state_changes_as_a_result_of_standard_lifecycle_stop_typequalified_name(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_QUALIFIED_NAME, op_name='stop')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'stop')


def test_node_state_changes_as_a_result_of_standard_lifecycle_delete_typequalified_name(ctx):
    node = run_operation_on_node(ctx, interface_name=TYPE_QUALIFIED_NAME, op_name='delete')
    _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, 'delete')

def test_node_state_doesnt_change_as_a_result_of_an_operation_that_is_not_standard_lifecycle1(ctx):
    node = run_operation_on_node(ctx, interface_name='interface_name', op_name='op_name')
    assert node.state == node.INITIAL


def test_node_state_doesnt_change_as_a_result_of_an_operation_that_is_not_standard_lifecycle2(ctx):
    node = run_operation_on_node(ctx, interface_name='interface_name', op_name='create')
    assert node.state == node.INITIAL


def run_operation_on_node(ctx, op_name, interface_name):
    node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    interface = mock.models.create_interface(
        service=node.service,
        interface_name=interface_name,
        operation_name=op_name,
        operation_kwargs=dict(function='{name}.{func.__name__}'.format(name=__name__, func=func)))
    node.interfaces[interface.name] = interface
    graph_compiler.GraphCompiler(ctx, ThreadExecutor).compile(
        single_operation_workflow(ctx, node=node, interface_name=interface_name, op_name=op_name)
    )

    eng = engine.Engine(executors={ThreadExecutor: ThreadExecutor()})
    eng.execute(ctx)
    return node


def run_standard_lifecycle_operation_on_node(ctx, op_name):
    return run_operation_on_node(ctx, interface_name='aria.interfaces.lifecycle.Standard',
                                 op_name=op_name)


def _assert_node_state_changed_as_a_result_of_standard_lifecycle_operation(node, op_name):
    assert global_test_dict['transitional_state'] == NodeBase._OP_TO_STATE[op_name]['transitional']
    assert node.state == NodeBase._OP_TO_STATE[op_name]['finished']


@workflow
def single_operation_workflow(graph, node, interface_name, op_name, **_):
    graph.add_tasks(api.task.OperationTask(
        node,
        interface_name=interface_name,
        operation_name=op_name))


@operation
def func(ctx):
    global_test_dict['transitional_state'] = ctx.node.state
