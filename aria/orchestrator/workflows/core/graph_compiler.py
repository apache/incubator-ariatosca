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


class GraphCompiler(object):
    def __init__(self, ctx, default_executor):
        self._ctx = ctx
        self._default_executor = default_executor
        self._stub_executor = executor.base.StubTaskExecutor
        self._model_to_api_id = {}

    def compile(self,
                task_graph,
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
        task_graph = task_graph or self._task_graph
        depends_on = list(depends_on)

        # Insert start marker
        start_task = self._create_stub_task(
            start_stub_type, depends_on, self._start_graph_suffix(task_graph.id), task_graph.name,
        )

        for task in task_graph.topological_order(reverse=True):
            dependencies = \
                (self._get_tasks_from_dependencies(task_graph.get_dependencies(task))
                 or [start_task])

            if isinstance(task, api.task.OperationTask):
                self._create_operation_task(task, dependencies)

            elif isinstance(task, api.task.WorkflowTask):
                # Build the graph recursively while adding start and end markers
                self.compile(
                    task, models.Task.START_SUBWROFKLOW, models.Task.END_SUBWORKFLOW, dependencies
                )
            elif isinstance(task, api.task.StubTask):
                self._create_stub_task(models.Task.STUB, dependencies, task.id)
            else:
                raise RuntimeError('Undefined state')

        # Insert end marker
        self._create_stub_task(
            end_stub_type,
            self._get_non_dependent_tasks(self._ctx.execution) or [start_task],
            self._end_graph_suffix(task_graph.id),
            task_graph.name
        )

    def _create_stub_task(self, stub_type, dependencies, api_id, name=None):
        model_task = models.Task(
            name=name,
            dependencies=dependencies,
            execution=self._ctx.execution,
            _executor=self._stub_executor,
            _stub_type=stub_type)
        self._ctx.model.task.put(model_task)
        self._model_to_api_id[model_task.id] = api_id
        return model_task

    def _create_operation_task(self, api_task, dependencies):
        model_task = models.Task.from_api_task(
            api_task, self._default_executor, dependencies=dependencies)
        self._ctx.model.task.put(model_task)
        self._model_to_api_id[model_task.id] = api_task.id
        return model_task

    @staticmethod
    def _start_graph_suffix(api_id):
        return '{0}-Start'.format(api_id)

    @staticmethod
    def _end_graph_suffix(api_id):
        return '{0}-End'.format(api_id)

    @staticmethod
    def _get_non_dependent_tasks(execution):
        tasks_with_dependencies = set()
        for task in execution.tasks:
            tasks_with_dependencies.update(task.dependencies)
        return list(set(execution.tasks) - set(tasks_with_dependencies))

    def _get_tasks_from_dependencies(self, dependencies):
        """
        Returns task list from dependencies.
        """
        tasks = []
        for dependency in dependencies:
            if getattr(dependency, 'actor', False):
                # This is
                dependency_name = dependency.id
            else:
                dependency_name = self._end_graph_suffix(dependency.id)
            tasks.extend(task for task in self._ctx.execution.tasks
                         if self._model_to_api_id.get(task.id, None) == dependency_name)
        return tasks
