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

    def execute(self, ctx):
        """
        execute the workflow
        """
        executing_tasks = []
        try:
            events.start_workflow_signal.send(ctx)
            while True:
                cancel = self._is_cancel(ctx)
                if cancel:
                    break
                for task in self._ended_tasks(ctx, executing_tasks):
                    self._handle_ended_tasks(ctx, task, executing_tasks)
                for task in self._executable_tasks(ctx):
                    self._handle_executable_task(ctx, task, executing_tasks)
                if self._all_tasks_consumed(ctx):
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

    def _executable_tasks(self, ctx):
        now = datetime.utcnow()
        return (
            task for task in self._tasks_iter(ctx)
            if task.is_waiting() and task.due_at <= now and \
            not self._task_has_dependencies(ctx, task)
        )

    @staticmethod
    def _ended_tasks(ctx, executing_tasks):
        for task in executing_tasks:
            if task.has_ended() and task in ctx._graph:
                yield task

    @staticmethod
    def _task_has_dependencies(ctx, task):
        return len(ctx._graph.pred.get(task, [])) > 0

    @staticmethod
    def _all_tasks_consumed(ctx):
        return len(ctx._graph.node) == 0

    @staticmethod
    def _tasks_iter(ctx):
        for task in ctx.execution.tasks:
            yield ctx.model.task.refresh(task)

    def _handle_executable_task(self, ctx, task, executing_tasks):
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

        executing_tasks.append(task)

        if not task._stub_type:
            events.sent_task_signal.send(op_ctx)
        task_executor.execute(op_ctx)

    @staticmethod
    def _handle_ended_tasks(ctx, task, executing_tasks):
        executing_tasks.remove(task)
        if task.status == models.Task.FAILED and not task.ignore_failure:
            raise exceptions.ExecutorException('Workflow failed')
        else:
            ctx._graph.remove_node(task)
