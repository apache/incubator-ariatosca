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
    instance = context.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
    assert instance.runtime_properties == _TEST_RUNTIME_PROPERTIES


def _update_runtime_properties(context):
    context.node_instance.runtime_properties.clear()
    context.node_instance.runtime_properties.update(_TEST_RUNTIME_PROPERTIES)


def _run_workflow(context, executor, op_func):
    @workflow
    def mock_workflow(ctx, graph):
        node_instance = ctx.model.node_instance.get_by_name(
            mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
        node_instance.node.operations['test.op'] = {'operation': _operation_mapping(op_func)}
        task = api.task.OperationTask.node_instance(instance=node_instance, name='test.op')
        graph.add_tasks(task)
        return graph
    graph = mock_workflow(ctx=context)  # pylint: disable=no-value-for-parameter
    eng = engine.Engine(executor=executor, workflow_context=context, tasks_graph=graph)
    eng.execute()


@operation
def _mock_success_operation(ctx):
    _update_runtime_properties(ctx)


@operation
def _mock_fail_operation(ctx):
    _update_runtime_properties(ctx)
    raise RuntimeError


def _operation_mapping(func):
    return '{name}.{func.__name__}'.format(name=__name__, func=func)


@pytest.fixture
def executor():
    result = process.ProcessExecutor(python_path=[tests.ROOT_DIR])
    yield result
    result.close()


@pytest.fixture
def context(tmpdir):
    result = mock.context.simple(storage.get_sqlite_api_kwargs(str(tmpdir)))
    yield result
    storage.release_sqlite_storage(result.model)
