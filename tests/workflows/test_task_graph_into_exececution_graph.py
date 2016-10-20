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
from networkx import topological_sort, DiGraph

from aria import contexts
from aria.workflows.api import tasks_graph
from aria.workflows.core import tasks, translation


@pytest.fixture(autouse=True)
def no_storage(monkeypatch):
    monkeypatch.setattr(tasks.OperationTask, '_create_operation_in_storage',
                        value=lambda *args, **kwargs: None)


def test_task_graph_into_execution_graph():
    task_graph = tasks_graph.TaskGraph('test_task_graph')
    simple_before_task = contexts.OperationContext('test_simple_before_task', {}, {}, None)
    simple_after_task = contexts.OperationContext('test_simple_after_task', {}, {}, None)

    inner_task_graph = tasks_graph.TaskGraph('test_inner_task_graph')
    inner_task = contexts.OperationContext('test_inner_task', {}, {}, None)
    inner_task_graph.add_task(inner_task)

    task_graph.add_task(simple_before_task)
    task_graph.add_task(simple_after_task)
    task_graph.add_task(inner_task_graph)
    task_graph.dependency(inner_task_graph, [simple_before_task])
    task_graph.dependency(simple_after_task, [inner_task_graph])

    # Direct check
    execution_graph = DiGraph()
    translation.build_execution_graph(task_graph=task_graph,
                                      workflow_context=None,
                                      execution_graph=execution_graph)
    execution_tasks = topological_sort(execution_graph)

    assert len(execution_tasks) == 7

    expected_tasks_names = [
        '{0}-Start'.format(task_graph.id),
        simple_before_task.id,
        '{0}-Start'.format(inner_task_graph.id),
        inner_task.id,
        '{0}-End'.format(inner_task_graph.id),
        simple_after_task.id,
        '{0}-End'.format(task_graph.id)
    ]

    assert expected_tasks_names == execution_tasks

    assert isinstance(_get_task_by_name(execution_tasks[0], execution_graph),
                      tasks.StartWorkflowTask)
    assert simple_before_task == _get_task_by_name(execution_tasks[1], execution_graph).context
    assert isinstance(_get_task_by_name(execution_tasks[2], execution_graph),
                      tasks.StartSubWorkflowTask)
    assert inner_task == _get_task_by_name(execution_tasks[3], execution_graph).context
    assert isinstance(_get_task_by_name(execution_tasks[4], execution_graph), tasks.
                      EndSubWorkflowTask)
    assert simple_after_task == _get_task_by_name(execution_tasks[5], execution_graph).context
    assert isinstance(_get_task_by_name(execution_tasks[6], execution_graph), tasks.EndWorkflowTask)


def _get_task_by_name(task_name, graph):
    return graph.node[task_name]['task']
