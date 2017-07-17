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
Workflow event handling.
"""

from datetime import (
    datetime,
    timedelta,
)

from ... import events
from ... import exceptions


@events.sent_task_signal.connect
def _task_sent(ctx, *args, **kwargs):
    with ctx.persist_changes:
        ctx.task.status = ctx.task.SENT


@events.start_task_signal.connect
def _task_started(ctx, *args, **kwargs):
    with ctx.persist_changes:
        ctx.task.started_at = datetime.utcnow()
        ctx.task.status = ctx.task.STARTED
        _update_node_state_if_necessary(ctx, is_transitional=True)


@events.on_failure_task_signal.connect
def _task_failed(ctx, exception, *args, **kwargs):
    with ctx.persist_changes:
        should_retry = all([
            not isinstance(exception, exceptions.TaskAbortException),
            ctx.task.attempts_count < ctx.task.max_attempts or
            ctx.task.max_attempts == ctx.task.INFINITE_RETRIES,
            # ignore_failure check here means the task will not be retried and it will be marked
            # as failed. The engine will also look at ignore_failure so it won't fail the
            # workflow.
            not ctx.task.ignore_failure
        ])
        if should_retry:
            retry_interval = None
            if isinstance(exception, exceptions.TaskRetryException):
                retry_interval = exception.retry_interval
            if retry_interval is None:
                retry_interval = ctx.task.retry_interval
            ctx.task.status = ctx.task.RETRYING
            ctx.task.attempts_count += 1
            ctx.task.due_at = datetime.utcnow() + timedelta(seconds=retry_interval)
        else:
            ctx.task.ended_at = datetime.utcnow()
            ctx.task.status = ctx.task.FAILED


@events.on_success_task_signal.connect
def _task_succeeded(ctx, *args, **kwargs):
    with ctx.persist_changes:
        ctx.task.ended_at = datetime.utcnow()
        ctx.task.status = ctx.task.SUCCESS

        _update_node_state_if_necessary(ctx)


@events.start_workflow_signal.connect
def _workflow_started(workflow_context, *args, **kwargs):
    with workflow_context.persist_changes:
        execution = workflow_context.execution
        # the execution may already be in the process of cancelling
        if execution.status in (execution.CANCELLING, execution.CANCELLED):
            return
        execution.status = execution.STARTED
        execution.started_at = datetime.utcnow()


@events.on_failure_workflow_signal.connect
def _workflow_failed(workflow_context, exception, *args, **kwargs):
    with workflow_context.persist_changes:
        execution = workflow_context.execution
        execution.error = str(exception)
        execution.status = execution.FAILED
        execution.ended_at = datetime.utcnow()


@events.on_success_workflow_signal.connect
def _workflow_succeeded(workflow_context, *args, **kwargs):
    with workflow_context.persist_changes:
        execution = workflow_context.execution
        execution.status = execution.SUCCEEDED
        execution.ended_at = datetime.utcnow()


@events.on_cancelled_workflow_signal.connect
def _workflow_cancelled(workflow_context, *args, **kwargs):
    with workflow_context.persist_changes:
        execution = workflow_context.execution
        # _workflow_cancelling function may have called this function already
        if execution.status == execution.CANCELLED:
            return
        # the execution may have already been finished
        elif execution.status in (execution.SUCCEEDED, execution.FAILED):
            _log_tried_to_cancel_execution_but_it_already_ended(workflow_context, execution.status)
        else:
            execution.status = execution.CANCELLED
            execution.ended_at = datetime.utcnow()


@events.on_resume_workflow_signal.connect
def _workflow_resume(workflow_context, *args, **kwargs):
    with workflow_context.persist_changes:
        execution = workflow_context.execution
        execution.status = execution.PENDING
        # Any non ended task would be put back to pending state
        for task in execution.tasks:
            if not task.has_ended():
                task.status = task.PENDING


@events.on_cancelling_workflow_signal.connect
def _workflow_cancelling(workflow_context, *args, **kwargs):
    with workflow_context.persist_changes:
        execution = workflow_context.execution
        if execution.status == execution.PENDING:
            return _workflow_cancelled(workflow_context=workflow_context)
        # the execution may have already been finished
        elif execution.status in (execution.SUCCEEDED, execution.FAILED):
            _log_tried_to_cancel_execution_but_it_already_ended(workflow_context, execution.status)
        else:
            execution.status = execution.CANCELLING


def _update_node_state_if_necessary(ctx, is_transitional=False):
    # TODO: this is not the right way to check! the interface name is arbitrary
    # and also will *never* be the type name
    node = ctx.task.node if ctx.task is not None else None
    if (node is not None) and \
        (ctx.task.interface_name in ('Standard', 'tosca.interfaces.node.lifecycle.Standard',
                                     'tosca:Standard')):
        state = node.determine_state(op_name=ctx.task.operation_name,
                                     is_transitional=is_transitional)
        if state:
            node.state = state
            ctx.model.node.update(node)


def _log_tried_to_cancel_execution_but_it_already_ended(workflow_context, status):
    workflow_context.logger.info(
        "'{workflow_name}' workflow execution {status} before the cancel request"
        "was fully processed".format(workflow_name=workflow_context.workflow_name, status=status))
