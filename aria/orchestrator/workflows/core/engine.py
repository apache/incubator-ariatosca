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

from aria import logger
from aria.modeling import models
from aria.orchestrator import events
from aria.orchestrator.context import operation

from .. import exceptions
from ..executor.base import StubTaskExecutor
# Import required so all signals are registered
from . import events_handler  # pylint: disable=unused-import


class Engine(logger.LoggerMixin):
    """
    The workflow engine. Executes workflows
    """

    def __init__(self, executors, **kwargs):
        super(Engine, self).__init__(**kwargs)
        self._executors = executors.copy()
        self._executors.setdefault(StubTaskExecutor, StubTaskExecutor())

    def execute(self, ctx, resuming=False):
        """
        execute the workflow
        """
        if resuming:
            events.on_resume_workflow_signal.send(ctx)

        tasks_tracker = _TasksTracker(ctx)
        try:
            events.start_workflow_signal.send(ctx)
            while True:
                cancel = self._is_cancel(ctx)
                if cancel:
                    break
                for task in tasks_tracker.ended_tasks:
                    self._handle_ended_tasks(task)
                    tasks_tracker.finished(task)
                for task in tasks_tracker.executable_tasks:
                    tasks_tracker.executing(task)
                    self._handle_executable_task(ctx, task)
                if tasks_tracker.all_tasks_consumed:
                    break
                else:
                    time.sleep(0.1)
            if cancel:
                events.on_cancelled_workflow_signal.send(ctx)
            else:
                events.on_success_workflow_signal.send(ctx)
        except BaseException as e:
            events.on_failure_workflow_signal.send(ctx, exception=e)
            raise

    @staticmethod
    def cancel_execution(ctx):
        """
        Send a cancel request to the engine. If execution already started, execution status
        will be modified to 'cancelling' status. If execution is in pending mode, execution status
        will be modified to 'cancelled' directly.
        """
        events.on_cancelling_workflow_signal.send(ctx)

    @staticmethod
    def _is_cancel(ctx):
        execution = ctx.model.execution.refresh(ctx.execution)
        return execution.status in (models.Execution.CANCELLING, models.Execution.CANCELLED)

    def _handle_executable_task(self, ctx, task):
        task_executor = self._executors[task._executor]

        # If the task is a stub, a default context is provided, else it should hold the context cls
        context_cls = operation.BaseOperationContext if task._stub_type else task._context_cls
        op_ctx = context_cls(
            model_storage=ctx.model,
            resource_storage=ctx.resource,
            workdir=ctx._workdir,
            task_id=task.id,
            actor_id=task.actor.id if task.actor else None,
            service_id=task.execution.service.id,
            execution_id=task.execution.id,
            name=task.name
        )

        if not task._stub_type:
            events.sent_task_signal.send(op_ctx)
        task_executor.execute(op_ctx)

    @staticmethod
    def _handle_ended_tasks(task):
        if task.status == models.Task.FAILED and not task.ignore_failure:
            raise exceptions.ExecutorException('Workflow failed')


class _TasksTracker(object):
    def __init__(self, ctx):
        self._ctx = ctx
        self._tasks = ctx.execution.tasks
        self._executed_tasks = [task for task in self._tasks if task.has_ended()]
        self._executable_tasks = list(set(self._tasks) - set(self._executed_tasks))
        self._executing_tasks = []

    @property
    def all_tasks_consumed(self):
        return len(self._executed_tasks) == len(self._tasks) and len(self._executing_tasks) == 0

    def executing(self, task):
        # Task executing could be retrying (thus removed and added earlier)
        if task not in self._executing_tasks:
            self._executable_tasks.remove(task)
            self._executing_tasks.append(task)

    def finished(self, task):
        self._executing_tasks.remove(task)
        self._executed_tasks.append(task)

    @property
    def ended_tasks(self):
        for task in self.executing_tasks:
            if task.has_ended():
                yield task

    @property
    def executable_tasks(self):
        now = datetime.utcnow()
        # we need both lists since retrying task are in the executing task list.
        for task in self._update_tasks(self._executing_tasks + self._executable_tasks):
            if all([task.is_waiting(),
                    task.due_at <= now,
                    all(dependency in self._executed_tasks for dependency in task.dependencies)
                   ]):
                yield task

    @property
    def executing_tasks(self):
        for task in self._update_tasks(self._executing_tasks):
            yield task

    @property
    def executed_tasks(self):
        for task in self._update_tasks(self._executed_tasks):
            yield task

    @property
    def tasks(self):
        for task in self._update_tasks(self._tasks):
            yield task

    def _update_tasks(self, tasks):
        for task in tasks:
            yield self._ctx.model.task.refresh(task)
