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

from networkx import topological_sort, DiGraph

from aria.modeling import models
from aria.orchestrator import context
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.core import graph_compiler
from aria.orchestrator.workflows.executor import base
from tests import mock
from tests import storage


def test_task_graph_into_execution_graph(tmpdir):
    interface_name = 'Standard'
    op1_name, op2_name, op3_name = 'create', 'configure', 'start'
    workflow_context = mock.context.simple(str(tmpdir))
    node = workflow_context.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    interface = mock.models.create_interface(
        node.service,
        interface_name,
        op1_name,
        operation_kwargs=dict(function='test')
    )
    interface.operations[op2_name] = mock.models.create_operation(op2_name)                         # pylint: disable=unsubscriptable-object
    interface.operations[op3_name] = mock.models.create_operation(op3_name)                         # pylint: disable=unsubscriptable-object
    node.interfaces[interface.name] = interface
    workflow_context.model.node.update(node)

    def sub_workflow(name, **_):
        return api.task_graph.TaskGraph(name)

    with context.workflow.current.push(workflow_context):
        test_task_graph = api.task.WorkflowTask(sub_workflow, name='test_task_graph')
        simple_before_task = api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=op1_name)
        simple_after_task = api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=op1_name)

        inner_task_graph = api.task.WorkflowTask(sub_workflow, name='test_inner_task_graph')
        inner_task_1 = api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=op1_name)
        inner_task_2 = api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=op2_name)
        inner_task_3 = api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=op3_name)
        inner_task_graph.add_tasks(inner_task_1)
        inner_task_graph.add_tasks(inner_task_2)
        inner_task_graph.add_tasks(inner_task_3)
        inner_task_graph.add_dependency(inner_task_2, inner_task_1)
        inner_task_graph.add_dependency(inner_task_3, inner_task_1)
        inner_task_graph.add_dependency(inner_task_3, inner_task_2)

    test_task_graph.add_tasks(simple_before_task)
    test_task_graph.add_tasks(simple_after_task)
    test_task_graph.add_tasks(inner_task_graph)
    test_task_graph.add_dependency(inner_task_graph, simple_before_task)
    test_task_graph.add_dependency(simple_after_task, inner_task_graph)

    compiler = graph_compiler.GraphCompiler(workflow_context, base.StubTaskExecutor)
    compiler.compile(test_task_graph)

    execution_tasks = topological_sort(_graph(workflow_context.execution.tasks))

    assert len(execution_tasks) == 9

    expected_tasks_names = [
        '{0}-Start'.format(test_task_graph.id),
        simple_before_task.id,
        '{0}-Start'.format(inner_task_graph.id),
        inner_task_1.id,
        inner_task_2.id,
        inner_task_3.id,
        '{0}-End'.format(inner_task_graph.id),
        simple_after_task.id,
        '{0}-End'.format(test_task_graph.id)
    ]

    assert expected_tasks_names == [compiler._model_to_api_id[t.id] for t in execution_tasks]
    assert all(isinstance(task, models.Task) for task in execution_tasks)
    execution_tasks = iter(execution_tasks)

    _assert_tasks(
        iter(execution_tasks),
        iter([simple_after_task, inner_task_1, inner_task_2, inner_task_3, simple_after_task])
    )
    storage.release_sqlite_storage(workflow_context.model)


def _assert_tasks(execution_tasks, api_tasks):
    start_workflow_exec_task = next(execution_tasks)
    assert start_workflow_exec_task._stub_type == models.Task.START_WORKFLOW

    before_exec_task = next(execution_tasks)
    simple_before_task = next(api_tasks)
    _assert_execution_is_api_task(before_exec_task, simple_before_task)
    assert before_exec_task.dependencies == [start_workflow_exec_task]

    start_subworkflow_exec_task = next(execution_tasks)
    assert start_subworkflow_exec_task._stub_type == models.Task.START_SUBWROFKLOW
    assert start_subworkflow_exec_task.dependencies == [before_exec_task]

    inner_exec_task_1 = next(execution_tasks)
    inner_task_1 = next(api_tasks)
    _assert_execution_is_api_task(inner_exec_task_1, inner_task_1)
    assert inner_exec_task_1.dependencies == [start_subworkflow_exec_task]

    inner_exec_task_2 = next(execution_tasks)
    inner_task_2 = next(api_tasks)
    _assert_execution_is_api_task(inner_exec_task_2, inner_task_2)
    assert inner_exec_task_2.dependencies == [inner_exec_task_1]

    inner_exec_task_3 = next(execution_tasks)
    inner_task_3 = next(api_tasks)
    _assert_execution_is_api_task(inner_exec_task_3, inner_task_3)
    assert sorted(inner_exec_task_3.dependencies) == sorted([inner_exec_task_1, inner_exec_task_2])

    end_subworkflow_exec_task = next(execution_tasks)
    assert end_subworkflow_exec_task._stub_type == models.Task.END_SUBWORKFLOW
    assert end_subworkflow_exec_task.dependencies == [inner_exec_task_3]

    after_exec_task = next(execution_tasks)
    simple_after_task = next(api_tasks)
    _assert_execution_is_api_task(after_exec_task, simple_after_task)
    assert after_exec_task.dependencies == [end_subworkflow_exec_task]

    end_workflow_exec_task = next(execution_tasks)
    assert end_workflow_exec_task._stub_type == models.Task.END_WORKFLOW
    assert end_workflow_exec_task.dependencies == [after_exec_task]


def _assert_execution_is_api_task(execution_task, api_task):
    assert execution_task.name == api_task.name
    assert execution_task.function == api_task.function
    assert execution_task.actor == api_task.actor
    assert execution_task.arguments == api_task.arguments


def _get_task_by_name(task_name, graph):
    return graph.node[task_name]['task']


def _graph(tasks):
    graph = DiGraph()
    for task in tasks:
        for dependency in task.dependencies:
            graph.add_edge(dependency, task)

    return graph
