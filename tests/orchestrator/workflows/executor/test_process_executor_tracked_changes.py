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

import copy

import pytest

from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.core import engine
from aria.orchestrator.workflows.executor import process
from aria.orchestrator import workflow, operation
from aria.orchestrator.workflows import exceptions

import tests
from tests import mock
from tests import storage


_TEST_RUNTIME_PROPERTIES = {
    'some': 'values', 'that': 'are', 'most': 'likely', 'only': 'set', 'here': 'yo'
}


def test_track_changes_of_successful_operation(context, executor):
    _run_workflow(context=context, executor=executor, op_func=_mock_success_operation)
    _assert_tracked_changes_are_applied(context)


def test_track_changes_of_failed_operation(context, executor):
    with pytest.raises(exceptions.ExecutorException):
        _run_workflow(context=context, executor=executor, op_func=_mock_fail_operation)
    _assert_tracked_changes_are_applied(context)


def _assert_tracked_changes_are_applied(context):
    instance = context.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    assert instance.runtime_properties == _TEST_RUNTIME_PROPERTIES


def _update_runtime_properties(context):
    context.node.runtime_properties.clear()
    context.node.runtime_properties.update(_TEST_RUNTIME_PROPERTIES)


def test_refresh_state_of_tracked_attributes(context, executor):
    out = _run_workflow(context=context, executor=executor, op_func=_mock_refreshing_operation)
    assert out['initial'] == out['after_refresh']
    assert out['initial'] != out['after_change']


def test_apply_tracked_changes_during_an_operation(context, executor):
    inputs = {
        'committed': {'some': 'new', 'properties': 'right here'},
        'changed_but_refreshed': {'some': 'newer', 'properties': 'right there'}
    }

    expected_initial = context.model.node.get_by_name(
        mock.models.DEPENDENCY_NODE_NAME).runtime_properties

    out = _run_workflow(context=context, executor=executor, op_func=_mock_updating_operation,
                        inputs=inputs)

    expected_after_update = expected_initial.copy()
    expected_after_update.update(inputs['committed'])
    expected_after_change = expected_after_update.copy()
    expected_after_change.update(inputs['changed_but_refreshed'])
    expected_after_refresh = expected_after_update

    assert out['initial'] == expected_initial
    assert out['after_update'] == expected_after_update
    assert out['after_change'] == expected_after_change
    assert out['after_refresh'] == expected_after_refresh


def _run_workflow(context, executor, op_func, inputs=None):
    @workflow
    def mock_workflow(ctx, graph):
        node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
        interface_name = 'test_interface'
        operation_name = 'operation'
        interface = mock.models.create_interface(
            ctx.service,
            interface_name,
            operation_name,
            operation_kwargs=dict(implementation=_operation_mapping(op_func))
        )
        node.interfaces[interface.name] = interface
        task = api.task.OperationTask.for_node(node=node,
                                               interface_name=interface_name,
                                               operation_name=operation_name,
                                               inputs=inputs or {})
        graph.add_tasks(task)
        return graph
    graph = mock_workflow(ctx=context)  # pylint: disable=no-value-for-parameter
    eng = engine.Engine(executor=executor, workflow_context=context, tasks_graph=graph)
    eng.execute()
    return context.model.node.get_by_name(
        mock.models.DEPENDENCY_NODE_NAME).runtime_properties.get('out')


@operation
def _mock_success_operation(ctx):
    _update_runtime_properties(ctx)


@operation
def _mock_fail_operation(ctx):
    _update_runtime_properties(ctx)
    raise RuntimeError


@operation
def _mock_refreshing_operation(ctx):
    out = {'initial': copy.deepcopy(ctx.node.runtime_properties)}
    ctx.node.runtime_properties.update({'some': 'new', 'properties': 'right here'})
    out['after_change'] = copy.deepcopy(ctx.node.runtime_properties)
    ctx.model.node.refresh(ctx.node)
    out['after_refresh'] = copy.deepcopy(ctx.node.runtime_properties)
    ctx.node.runtime_properties['out'] = out


@operation
def _mock_updating_operation(ctx, committed, changed_but_refreshed):
    out = {'initial': copy.deepcopy(ctx.node.runtime_properties)}
    ctx.node.runtime_properties.update(committed)
    ctx.model.node.update(ctx.node)
    out['after_update'] = copy.deepcopy(ctx.node.runtime_properties)
    ctx.node.runtime_properties.update(changed_but_refreshed)
    out['after_change'] = copy.deepcopy(ctx.node.runtime_properties)
    ctx.model.node.refresh(ctx.node)
    out['after_refresh'] = copy.deepcopy(ctx.node.runtime_properties)
    ctx.node.runtime_properties['out'] = out


def _operation_mapping(func):
    return '{name}.{func.__name__}'.format(name=__name__, func=func)


@pytest.fixture
def executor():
    result = process.ProcessExecutor(python_path=[tests.ROOT_DIR])
    yield result
    result.close()


@pytest.fixture
def context(tmpdir):
    result = mock.context.simple(str(tmpdir))
    yield result
    storage.release_sqlite_storage(result.model)
