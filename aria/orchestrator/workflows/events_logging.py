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
from ... import modeling


def _get_task_name(task):
    if isinstance(task.actor, modeling.model_bases.service_instance.RelationshipBase):
        return '{source_node.name}->{target_node.name}'.format(
            source_node=task.actor.source_node, target_node=task.actor.target_node)
    else:
        return task.actor.name


@events.start_task_signal.connect
def _start_task_handler(task, **kwargs):
    # If the task has no function this is an empty task.
    if task.function:
        suffix = 'started...'
        logger = task.context.logger.info
    else:
        suffix = 'has no implementation'
        logger = task.context.logger.debug

    logger('{name} {task.interface_name}.{task.operation_name} {suffix}'.format(
        name=_get_task_name(task), task=task, suffix=suffix))

@events.on_success_task_signal.connect
def _success_task_handler(task, **kwargs):
    if not task.function:
        return
    task.context.logger.info('{name} {task.interface_name}.{task.operation_name} successful'
                             .format(name=_get_task_name(task), task=task))


@events.on_failure_task_signal.connect
def _failure_operation_handler(task, traceback, **kwargs):
    task.context.logger.error(
        '{name} {task.interface_name}.{task.operation_name} failed'
        .format(name=_get_task_name(task), task=task), extra=dict(traceback=traceback)
    )


@events.start_workflow_signal.connect
def _start_workflow_handler(context, **kwargs):
    context.logger.info("Starting '{ctx.workflow_name}' workflow execution".format(ctx=context))


@events.on_failure_workflow_signal.connect
def _failure_workflow_handler(context, **kwargs):
    context.logger.info("'{ctx.workflow_name}' workflow execution failed".format(ctx=context))


@events.on_success_workflow_signal.connect
def _success_workflow_handler(context, **kwargs):
    context.logger.info("'{ctx.workflow_name}' workflow execution succeeded".format(ctx=context))


@events.on_cancelled_workflow_signal.connect
def _cancel_workflow_handler(context, **kwargs):
    context.logger.info("'{ctx.workflow_name}' workflow execution canceled".format(ctx=context))


@events.on_cancelling_workflow_signal.connect
def _cancelling_workflow_handler(context, **kwargs):
    context.logger.info("Cancelling '{ctx.workflow_name}' workflow execution".format(ctx=context))
