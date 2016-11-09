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

from . import (
    start_workflow_signal,
    on_success_workflow_signal,
    on_failure_workflow_signal,
    on_cancelled_workflow_signal,
    on_cancelling_workflow_signal,
    sent_task_signal,
    start_task_signal,
    on_success_task_signal,
    on_failure_task_signal,
)


@sent_task_signal.connect
def _task_sent(task, *args, **kwargs):
    with task.update():
        task.status = task.SENT


@start_task_signal.connect
def _task_started(task, *args, **kwargs):
    with task.update():
        task.started_at = datetime.utcnow()
        task.status = task.STARTED


@on_failure_task_signal.connect
def _task_failed(task, *args, **kwargs):
    with task.update():
        if task.retry_count < task.max_retries or task.max_retries == task.INFINITE_RETRIES:
            task.status = task.RETRYING
            task.retry_count += 1
            task.due_at = datetime.utcnow() + timedelta(seconds=task.retry_interval)
        else:
            task.ended_at = datetime.utcnow()
            task.status = task.FAILED


@on_success_task_signal.connect
def _task_succeeded(task, *args, **kwargs):
    with task.update():
        task.ended_at = datetime.utcnow()
        task.status = task.SUCCESS


@start_workflow_signal.connect
def _workflow_started(workflow_context, *args, **kwargs):
    execution = workflow_context.execution
    execution.status = execution.STARTED
    execution.started_at = datetime.utcnow()
    workflow_context.execution = execution


@on_failure_workflow_signal.connect
def _workflow_failed(workflow_context, exception, *args, **kwargs):
    execution = workflow_context.execution
    execution.error = str(exception)
    execution.status = execution.FAILED
    execution.ended_at = datetime.utcnow()
    workflow_context.execution = execution


@on_success_workflow_signal.connect
def _workflow_succeeded(workflow_context, *args, **kwargs):
    execution = workflow_context.execution
    execution.status = execution.TERMINATED
    execution.ended_at = datetime.utcnow()
    workflow_context.execution = execution


@on_cancelled_workflow_signal.connect
def _workflow_cancelled(workflow_context, *args, **kwargs):
    execution = workflow_context.execution
    # _workflow_cancelling function may have called this function
    # already
    if execution.status == execution.CANCELLED:
        return
    execution.status = execution.CANCELLED
    execution.ended_at = datetime.utcnow()
    workflow_context.execution = execution


@on_cancelling_workflow_signal.connect
def _workflow_cancelling(workflow_context, *args, **kwargs):
    execution = workflow_context.execution
    if execution.status == execution.PENDING:
        return _workflow_cancelled(workflow_context=workflow_context)
    execution.status = execution.CANCELLING
    workflow_context.execution = execution
