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
from datetime import datetime

import networkx

from aria import logger
from aria.storage import model
from aria.orchestrator import events

from .. import exceptions
from . import task as engine_task
from . import translation
# Import required so all signals are registered
from . import events_handler  # pylint: disable=unused-import


class Engine(logger.LoggerMixin):
    """
    The workflow engine. Executes workflows
    """

    def __init__(self, executor, workflow_context, tasks_graph, **kwargs):
        super(Engine, self).__init__(**kwargs)
        self._workflow_context = workflow_context
        self._execution_graph = networkx.DiGraph()
        self._executor = executor
        translation.build_execution_graph(task_graph=tasks_graph,
                                          execution_graph=self._execution_graph)

    def execute(self):
        """
        execute the workflow
        """
        try:
            events.start_workflow_signal.send(self._workflow_context)
            while True:
                cancel = self._is_cancel()
                if cancel:
                    break
                for task in self._ended_tasks():
                    self._handle_ended_tasks(task)
                for task in self._executable_tasks():
                    self._handle_executable_task(task)
                if self._all_tasks_consumed():
                    break
                else:
                    time.sleep(0.1)
            if cancel:
                events.on_cancelled_workflow_signal.send(self._workflow_context)
            else:
                events.on_success_workflow_signal.send(self._workflow_context)
        except BaseException as e:
            events.on_failure_workflow_signal.send(self._workflow_context, exception=e)
            raise

    def cancel_execution(self):
        """
        Send a cancel request to the engine. If execution already started, execution status
        will be modified to 'cancelling' status. If execution is in pending mode, execution status
        will be modified to 'cancelled' directly.
        """
        events.on_cancelling_workflow_signal.send(self._workflow_context)

    def _is_cancel(self):
        return self._workflow_context.execution.status in [model.Execution.CANCELLING,
                                                           model.Execution.CANCELLED]

    def _executable_tasks(self):
        now = datetime.utcnow()
        return (task for task in self._tasks_iter()
                if task.status in model.Task.WAIT_STATES and
                task.due_at <= now and
                not self._task_has_dependencies(task))

    def _ended_tasks(self):
        return (task for task in self._tasks_iter() if task.status in model.Task.END_STATES)

    def _task_has_dependencies(self, task):
        return len(self._execution_graph.pred.get(task.id, {})) > 0

    def _all_tasks_consumed(self):
        return len(self._execution_graph.node) == 0

    def _tasks_iter(self):
        for _, data in self._execution_graph.nodes_iter(data=True):
            task = data['task']
            if isinstance(task, engine_task.OperationTask):
                if task.model_task.status not in model.Task.END_STATES:
                    self._workflow_context.model.task.refresh(task.model_task)
            yield task

    def _handle_executable_task(self, task):
        if isinstance(task, engine_task.StubTask):
            task.status = model.Task.SUCCESS
        else:
            events.sent_task_signal.send(task)
            self._executor.execute(task)

    def _handle_ended_tasks(self, task):
        if task.status == model.Task.FAILED and not task.ignore_failure:
            raise exceptions.ExecutorException('Workflow failed')
        else:
            self._execution_graph.remove_node(task.id)
