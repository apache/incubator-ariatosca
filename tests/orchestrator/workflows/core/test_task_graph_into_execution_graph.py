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

from networkx import topological_sort

from aria.modeling import models
from aria.orchestrator import context
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.core import compile
from aria.orchestrator.workflows.executor import base
from tests import mock
from tests import storage


def test_task_graph_into_execution_graph(tmpdir):
    interface_name = 'Standard'
    operation_name = 'create'
    workflow_context = mock.context.simple(str(tmpdir))
    node = workflow_context.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    interface = mock.models.create_interface(
        node.service,
        interface_name,
        operation_name,
        operation_kwargs=dict(function='test')
    )
    node.interfaces[interface.name] = interface
    workflow_context.model.node.update(node)

    def sub_workflow(name, **_):
        return api.task_graph.TaskGraph(name)

    with context.workflow.current.push(workflow_context):
        test_task_graph = api.task.WorkflowTask(sub_workflow, name='test_task_graph')
        simple_before_task = api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=operation_name)
        simple_after_task = api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=operation_name)

        inner_task_graph = api.task.WorkflowTask(sub_workflow, name='test_inner_task_graph')
        inner_task = api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=operation_name)
        inner_task_graph.add_tasks(inner_task)

    test_task_graph.add_tasks(simple_before_task)
    test_task_graph.add_tasks(simple_after_task)
    test_task_graph.add_tasks(inner_task_graph)
    test_task_graph.add_dependency(inner_task_graph, simple_before_task)
    test_task_graph.add_dependency(simple_after_task, inner_task_graph)

    compile.create_execution_tasks(workflow_context, test_task_graph, base.StubTaskExecutor)

    execution_tasks = topological_sort(workflow_context._graph)

    assert len(execution_tasks) == 7

    expected_tasks_names = [
        '{0}-Start'.format(test_task_graph.id),
        simple_before_task.id,
        '{0}-Start'.format(inner_task_graph.id),
        inner_task.id,
        '{0}-End'.format(inner_task_graph.id),
        simple_after_task.id,
        '{0}-End'.format(test_task_graph.id)
    ]

    assert expected_tasks_names == [t._api_id for t in execution_tasks]
    assert all(isinstance(task, models.Task) for task in execution_tasks)
    execution_tasks = iter(execution_tasks)

    assert next(execution_tasks)._stub_type == models.Task.START_WORKFLOW
    _assert_execution_is_api_task(next(execution_tasks), simple_before_task)
    assert next(execution_tasks)._stub_type == models.Task.START_SUBWROFKLOW
    _assert_execution_is_api_task(next(execution_tasks), inner_task)
    assert next(execution_tasks)._stub_type == models.Task.END_SUBWORKFLOW
    _assert_execution_is_api_task(next(execution_tasks), simple_after_task)
    assert next(execution_tasks)._stub_type == models.Task.END_WORKFLOW

    storage.release_sqlite_storage(workflow_context.model)


def _assert_execution_is_api_task(execution_task, api_task):
    assert execution_task._api_id == api_task.id
    assert execution_task.name == api_task.name
    assert execution_task.function == api_task.function
    assert execution_task.actor == api_task.actor
    assert execution_task.arguments == api_task.arguments


def _get_task_by_name(task_name, graph):
    return graph.node[task_name]['task']
