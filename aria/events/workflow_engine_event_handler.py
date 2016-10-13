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

from . import (
    start_task_signal,
    on_success_task_signal,
    on_failure_task_signal,
    start_workflow_signal,
    on_success_workflow_signal,
    on_failure_workflow_signal
)


@start_task_signal.connect
def start_task_handler(task, **kwargs):
    task.logger.debug(
        'Event: Starting task: {task.name}'.format(task=task))


@on_success_task_signal.connect
def success_task_handler(task, **kwargs):
    task.logger.debug(
        'Event: Task success: {task.name}'.format(task=task))


@on_failure_task_signal.connect
def failure_operation_handler(task, **kwargs):
    task.logger.error(
        'Event: Task failure: {task.name}'.format(task=task),
        exc_info=kwargs.get('exception', True))


@start_workflow_signal.connect
def start_workflow_handler(context, **kwargs):
    context.logger.debug(
        'Event: Starting workflow: {context.name}'.format(context=context))


@on_failure_workflow_signal.connect
def failure_workflow_handler(context, **kwargs):
    context.logger.debug(
        'Event: Workflow failure: {context.name}'.format(context=context))


@on_success_workflow_signal.connect
def success_workflow_handler(context, **kwargs):
    context.logger.debug(
        'Event: Workflow success: {context.name}'.format(context=context))
