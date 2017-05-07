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

"""
Translation of user graph's API to the execution graph
"""

from .. import api
from ..executor import base
from . import task as core_task


def build_execution_graph(
        task_graph,
        execution_graph,
        default_executor,
        start_cls=core_task.StartWorkflowTask,
        end_cls=core_task.EndWorkflowTask,
        depends_on=()):
    """
    Translates the user graph to the execution graph
    :param task_graph: The user's graph
    :param workflow_context: The workflow
    :param execution_graph: The execution graph that is being built
    :param start_cls: internal use
    :param end_cls: internal use
    :param depends_on: internal use
    """
    # Insert start marker
    start_task = start_cls(id=_start_graph_suffix(task_graph.id), executor=base.StubTaskExecutor())
    _add_task_and_dependencies(execution_graph, start_task, depends_on)

    for api_task in task_graph.topological_order(reverse=True):
        dependencies = task_graph.get_dependencies(api_task)
        operation_dependencies = _get_tasks_from_dependencies(
            execution_graph, dependencies, default=[start_task])

        if isinstance(api_task, api.task.OperationTask):
            operation_task = core_task.OperationTask(api_task, executor=default_executor)
            _add_task_and_dependencies(execution_graph, operation_task, operation_dependencies)
        elif isinstance(api_task, api.task.WorkflowTask):
            # Build the graph recursively while adding start and end markers
            build_execution_graph(
                task_graph=api_task,
                execution_graph=execution_graph,
                default_executor=default_executor,
                start_cls=core_task.StartSubWorkflowTask,
                end_cls=core_task.EndSubWorkflowTask,
                depends_on=operation_dependencies
            )
        elif isinstance(api_task, api.task.StubTask):
            stub_task = core_task.StubTask(id=api_task.id, executor=base.StubTaskExecutor())
            _add_task_and_dependencies(execution_graph, stub_task, operation_dependencies)
        else:
            raise RuntimeError('Undefined state')

    # Insert end marker
    workflow_dependencies = _get_tasks_from_dependencies(
        execution_graph,
        _get_non_dependency_tasks(task_graph),
        default=[start_task])
    end_task = end_cls(id=_end_graph_suffix(task_graph.id), executor=base.StubTaskExecutor())
    _add_task_and_dependencies(execution_graph, end_task, workflow_dependencies)


def _add_task_and_dependencies(execution_graph, operation_task, operation_dependencies=()):
    execution_graph.add_node(operation_task.id, task=operation_task)
    for dependency in operation_dependencies:
        execution_graph.add_edge(dependency.id, operation_task.id)


def _get_tasks_from_dependencies(execution_graph, dependencies, default=()):
    """
    Returns task list from dependencies.
    """
    tasks = []
    for dependency in dependencies:
        if isinstance(dependency, (api.task.OperationTask, api.task.StubTask)):
            dependency_id = dependency.id
        else:
            dependency_id = _end_graph_suffix(dependency.id)
        tasks.append(execution_graph.node[dependency_id]['task'])
    return tasks or default


def _start_graph_suffix(id):
    return '{0}-Start'.format(id)


def _end_graph_suffix(id):
    return '{0}-End'.format(id)


def _get_non_dependency_tasks(graph):
    for task in graph.tasks:
        if len(list(graph.get_dependents(task))) == 0:
            yield task
