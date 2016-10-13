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

from aria import contexts

from . import tasks


def build_execution_graph(
        task_graph,
        workflow_context,
        execution_graph,
        start_cls=tasks.StartWorkflowTask,
        end_cls=tasks.EndWorkflowTask,
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
    start_task = start_cls(id=_start_graph_suffix(task_graph.id),
                           name=_start_graph_suffix(task_graph.name),
                           context=workflow_context)
    _add_task_and_dependencies(execution_graph, start_task, depends_on)

    for operation_or_workflow, dependencies in task_graph.task_tree(reverse=True):
        operation_dependencies = _get_tasks_from_dependencies(
            execution_graph,
            dependencies,
            default=[start_task])

        if _is_operation(operation_or_workflow):
            # Add the task an the dependencies
            operation_task = tasks.OperationTask(id=operation_or_workflow.id,
                                                 name=operation_or_workflow.name,
                                                 context=operation_or_workflow)
            _add_task_and_dependencies(execution_graph, operation_task, operation_dependencies)
        else:
            # Built the graph recursively while adding start and end markers
            build_execution_graph(
                task_graph=operation_or_workflow,
                workflow_context=workflow_context,
                execution_graph=execution_graph,
                start_cls=tasks.StartSubWorkflowTask,
                end_cls=tasks.EndSubWorkflowTask,
                depends_on=operation_dependencies
            )

    # Insert end marker
    workflow_dependencies = _get_tasks_from_dependencies(
        execution_graph,
        task_graph.leaf_tasks,
        default=[start_task])
    end_task = end_cls(
        id=_end_graph_suffix(task_graph.id),
        name=_end_graph_suffix(task_graph.name),
        context=workflow_context)
    _add_task_and_dependencies(execution_graph, end_task, workflow_dependencies)


def _add_task_and_dependencies(execution_graph, operation_task, operation_dependencies=()):
    execution_graph.add_node(operation_task.id, task=operation_task)
    for dependency in operation_dependencies:
        execution_graph.add_edge(dependency.id, operation_task.id)


def _get_tasks_from_dependencies(execution_graph, dependencies, default=()):
    """
    Returns task list from dependencies.
    """
    return [execution_graph.node[dependency.id if _is_operation(dependency)
                                 else _end_graph_suffix(dependency.id)]['task']
            for dependency in dependencies] or default


def _is_operation(task):
    return isinstance(task, contexts.OperationContext)


def _start_graph_suffix(id):
    return '{0}-Start'.format(id)


def _end_graph_suffix(id):
    return '{0}-End'.format(id)
