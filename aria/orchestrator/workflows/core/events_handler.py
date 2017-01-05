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
Aria's events Sub-Package
Path: aria.events.storage_event_handler

Implementation of storage handlers for workflow and operation events.
"""


from datetime import (
    datetime,
    timedelta,
)

from ... import events
from ... import exceptions

@events.sent_task_signal.connect
def _task_sent(task, *args, **kwargs):
    with task._update():
        task.status = task.SENT


@events.start_task_signal.connect
def _task_started(task, *args, **kwargs):
    with task._update():
        task.started_at = datetime.utcnow()
        task.status = task.STARTED


@events.on_failure_task_signal.connect
def _task_failed(task, exception, *args, **kwargs):
    with task._update():
        should_retry = all([
            not isinstance(exception, exceptions.TaskAbortException),
            task.retry_count < task.max_attempts - 1 or task.max_attempts == task.INFINITE_RETRIES,
            # ignore_failure check here means the task will not be retries and it will be marked
            # as failed. The engine will also look at ignore_failure so it won't fail the
            # workflow.
            not task.ignore_failure
        ])
        if should_retry:
            retry_interval = None
            if isinstance(exception, exceptions.TaskRetryException):
                retry_interval = exception.retry_interval
            if retry_interval is None:
                retry_interval = task.retry_interval
            task.status = task.RETRYING
            task.retry_count += 1
            task.due_at = datetime.utcnow() + timedelta(seconds=retry_interval)
        else:
            task.ended_at = datetime.utcnow()
            task.status = task.FAILED


@events.on_success_task_signal.connect
def _task_succeeded(task, *args, **kwargs):
    with task._update():
        task.ended_at = datetime.utcnow()
        task.status = task.SUCCESS


@events.start_workflow_signal.connect
def _workflow_started(workflow_context, *args, **kwargs):
    execution = workflow_context.execution
    execution.status = execution.STARTED
    execution.started_at = datetime.utcnow()
    workflow_context.execution = execution


@events.on_failure_workflow_signal.connect
def _workflow_failed(workflow_context, exception, *args, **kwargs):
    execution = workflow_context.execution
    execution.error = str(exception)
    execution.status = execution.FAILED
    execution.ended_at = datetime.utcnow()
    workflow_context.execution = execution


@events.on_success_workflow_signal.connect
def _workflow_succeeded(workflow_context, *args, **kwargs):
    execution = workflow_context.execution
    execution.status = execution.TERMINATED
    execution.ended_at = datetime.utcnow()
    workflow_context.execution = execution


@events.on_cancelled_workflow_signal.connect
def _workflow_cancelled(workflow_context, *args, **kwargs):
    execution = workflow_context.execution
    # _workflow_cancelling function may have called this function
    # already
    if execution.status == execution.CANCELLED:
        return
    execution.status = execution.CANCELLED
    execution.ended_at = datetime.utcnow()
    workflow_context.execution = execution


@events.on_cancelling_workflow_signal.connect
def _workflow_cancelling(workflow_context, *args, **kwargs):
    execution = workflow_context.execution
    if execution.status == execution.PENDING:
        return _workflow_cancelled(workflow_context=workflow_context)
    execution.status = execution.CANCELLING
    workflow_context.execution = execution
