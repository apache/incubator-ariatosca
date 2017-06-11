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


from ....modeling import models
from .. import executor, api


def create_execution_tasks(ctx, task_graph, default_executor):
    execution = ctx.execution
    _construct_execution_tasks(execution, task_graph, default_executor)
    ctx.model.execution.update(execution)
    return execution.tasks


def _construct_execution_tasks(execution,
                               task_graph,
                               default_executor,
                               stub_executor=executor.base.StubTaskExecutor,
                               start_stub_type=models.Task.START_WORKFLOW,
                               end_stub_type=models.Task.END_WORKFLOW,
                               depends_on=()):
    """
    Translates the user graph to the execution graph
    :param task_graph: The user's graph
    :param start_stub_type: internal use
    :param end_stub_type: internal use
    :param depends_on: internal use
    """
    depends_on = list(depends_on)

    # Insert start marker
    start_task = models.Task(execution=execution,
                             dependencies=depends_on,
                             _api_id=_start_graph_suffix(task_graph.id),
                             _stub_type=start_stub_type,
                             _executor=stub_executor)

    for task in task_graph.topological_order(reverse=True):
        operation_dependencies = _get_tasks_from_dependencies(
            execution, task_graph.get_dependencies(task), [start_task])

        if isinstance(task, api.task.OperationTask):
            models.Task.from_api_task(api_task=task,
                                      executor=default_executor,
                                      dependencies=operation_dependencies)

        elif isinstance(task, api.task.WorkflowTask):
            # Build the graph recursively while adding start and end markers
            _construct_execution_tasks(
                execution=execution,
                task_graph=task,
                default_executor=default_executor,
                stub_executor=stub_executor,
                start_stub_type=models.Task.START_SUBWROFKLOW,
                end_stub_type=models.Task.END_SUBWORKFLOW,
                depends_on=operation_dependencies
            )
        elif isinstance(task, api.task.StubTask):
            models.Task(execution=execution,
                        dependencies=operation_dependencies,
                        _api_id=task.id,
                        _executor=stub_executor,
                        _stub_type=models.Task.STUB,
                       )
        else:
            raise RuntimeError('Undefined state')

    # Insert end marker
    models.Task(dependencies=_get_non_dependent_tasks(execution) or [start_task],
                execution=execution,
                _api_id=_end_graph_suffix(task_graph.id),
                _executor=stub_executor,
                _stub_type=end_stub_type)


def _start_graph_suffix(api_id):
    return '{0}-Start'.format(api_id)


def _end_graph_suffix(api_id):
    return '{0}-End'.format(api_id)


def _get_non_dependent_tasks(execution):
    tasks_with_dependencies = set()
    for task in execution.tasks:
        tasks_with_dependencies.update(task.dependencies)
    return list(set(execution.tasks) - set(tasks_with_dependencies))


def _get_tasks_from_dependencies(execution, dependencies, default=()):
    """
    Returns task list from dependencies.
    """
    tasks = []
    for dependency in dependencies:
        if getattr(dependency, 'actor', False):
            # This is
            dependency_name = dependency.id
        else:
            dependency_name = _end_graph_suffix(dependency.id)
        tasks.extend(task for task in execution.tasks if task._api_id == dependency_name)
    return tasks or default
