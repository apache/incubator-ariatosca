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

from aria.orchestrator import context
from aria.orchestrator.workflows import api, core

from tests import mock
from tests import storage


def test_task_graph_into_execution_graph(tmpdir):
    operation_name = 'tosca.interfaces.node.lifecycle.Standard.create'
    task_context = mock.context.simple(str(tmpdir))
    node = task_context.model.node.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
    node.interfaces = [mock.models.get_interface(operation_name)]
    task_context.model.node.update(node)

    def sub_workflow(name, **_):
        return api.task_graph.TaskGraph(name)

    with context.workflow.current.push(task_context):
        test_task_graph = api.task.WorkflowTask(sub_workflow, name='test_task_graph')
        simple_before_task = api.task.OperationTask.node(instance=node,
                                                         name=operation_name)
        simple_after_task = api.task.OperationTask.node(instance=node,
                                                        name=operation_name)

        inner_task_graph = api.task.WorkflowTask(sub_workflow, name='test_inner_task_graph')
        inner_task = api.task.OperationTask.node(instance=node,
                                                 name=operation_name)
        inner_task_graph.add_tasks(inner_task)

    test_task_graph.add_tasks(simple_before_task)
    test_task_graph.add_tasks(simple_after_task)
    test_task_graph.add_tasks(inner_task_graph)
    test_task_graph.add_dependency(inner_task_graph, simple_before_task)
    test_task_graph.add_dependency(simple_after_task, inner_task_graph)

    # Direct check
    execution_graph = DiGraph()
    core.translation.build_execution_graph(task_graph=test_task_graph,
                                           execution_graph=execution_graph)
    execution_tasks = topological_sort(execution_graph)

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

    assert expected_tasks_names == execution_tasks

    assert isinstance(_get_task_by_name(execution_tasks[0], execution_graph),
                      core.task.StartWorkflowTask)

    _assert_execution_is_api_task(_get_task_by_name(execution_tasks[1], execution_graph),
                                  simple_before_task)
    assert isinstance(_get_task_by_name(execution_tasks[2], execution_graph),
                      core.task.StartSubWorkflowTask)

    _assert_execution_is_api_task(_get_task_by_name(execution_tasks[3], execution_graph),
                                  inner_task)
    assert isinstance(_get_task_by_name(execution_tasks[4], execution_graph),
                      core.task.EndSubWorkflowTask)

    _assert_execution_is_api_task(_get_task_by_name(execution_tasks[5], execution_graph),
                                  simple_after_task)
    assert isinstance(_get_task_by_name(execution_tasks[6], execution_graph),
                      core.task.EndWorkflowTask)
    storage.release_sqlite_storage(task_context.model)


def _assert_execution_is_api_task(execution_task, api_task):
    assert execution_task.id == api_task.id
    assert execution_task.name == api_task.name
    assert execution_task.implementation == api_task.implementation
    assert execution_task.actor == api_task.actor
    assert execution_task.inputs == api_task.inputs


def _get_task_by_name(task_name, graph):
    return graph.node[task_name]['task']
