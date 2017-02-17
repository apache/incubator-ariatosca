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
ARIA's events Sub-Package
Path: aria.events.storage_event_handler

Implementation of logger handlers for workflow and operation events.
"""

from .. import events


@events.start_task_signal.connect
def _start_task_handler(task, **kwargs):
    task.context.logger.debug('Event: Starting task: {task.name}'.format(task=task))


@events.on_success_task_signal.connect
def _success_task_handler(task, **kwargs):
    task.context.logger.debug('Event: Task success: {task.name}'.format(task=task))


@events.on_failure_task_signal.connect
def _failure_operation_handler(task, exception, **kwargs):
    error = '{0}: {1}'.format(type(exception).__name__, exception)
    task.context.logger.error('Event: Task failure: {task.name} [{error}]'.format(
        task=task, error=error))


@events.start_workflow_signal.connect
def _start_workflow_handler(context, **kwargs):
    context.logger.debug('Event: Starting workflow: {context.name}'.format(context=context))


@events.on_failure_workflow_signal.connect
def _failure_workflow_handler(context, **kwargs):
    context.logger.debug('Event: Workflow failure: {context.name}'.format(context=context))


@events.on_success_workflow_signal.connect
def _success_workflow_handler(context, **kwargs):
    context.logger.debug('Event: Workflow success: {context.name}'.format(context=context))


@events.on_cancelled_workflow_signal.connect
def _cancel_workflow_handler(context, **kwargs):
    context.logger.debug('Event: Workflow cancelled: {context.name}'.format(context=context))


@events.on_cancelling_workflow_signal.connect
def _cancelling_workflow_handler(context, **kwargs):
    context.logger.debug('Event: Workflow cancelling: {context.name}'.format(context=context))
