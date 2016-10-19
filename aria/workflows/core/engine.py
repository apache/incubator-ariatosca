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
The workflow engine. Executes workflows
"""

import time

import networkx

from aria import events, logger

from . import translation


class Engine(logger.LoggerMixin):
    """
    The workflow engine. Executes workflows
    """

    def __init__(self, executor, workflow_context, tasks_graph, **kwargs):
        super(Engine, self).__init__(**kwargs)
        self._workflow_context = workflow_context
        self._tasks_graph = tasks_graph
        self._execution_graph = networkx.DiGraph()
        self._executor = executor
        translation.build_execution_graph(task_graph=self._tasks_graph,
                                          workflow_context=workflow_context,
                                          execution_graph=self._execution_graph)

    def execute(self):
        """
        execute the workflow
        """
        try:
            events.start_workflow_signal.send(self._workflow_context)
            while True:
                for task in self._ended_tasks():
                    self._handle_ended_tasks(task)
                for task in self._executable_tasks():
                    self._handle_executable_task(task)
                if self._all_tasks_consumed():
                    break
                else:
                    time.sleep(0.1)
            events.on_success_workflow_signal.send(self._workflow_context)
        except BaseException as e:
            events.on_failure_workflow_signal.send(self._workflow_context, exception=e)
            raise

    def _executable_tasks(self):
        now = time.time()
        return (task for task in self._tasks_iter()
                if task.status == task.PENDING and
                task.eta <= now and
                not self._task_has_dependencies(task))

    def _ended_tasks(self):
        return (task for task in self._tasks_iter() if task.status in task.END_STATES)

    def _task_has_dependencies(self, task):
        return len(self._execution_graph.succ.get(task.id, {})) > 0

    def _all_tasks_consumed(self):
        return len(self._execution_graph.node) == 0

    def _tasks_iter(self):
        return (data['task'] for _, data in self._execution_graph.nodes_iter(data=True))

    def _handle_executable_task(self, task):
        self._executor.execute(task)

    def _handle_ended_tasks(self, task):
        if task.status == task.FAILED:
            raise RuntimeError('Workflow failed')
        else:
            self._execution_graph.remove_node(task.id)
