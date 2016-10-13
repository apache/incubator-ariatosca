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
    start_operation_signal,
    end_operation_signal,
    on_success_operation_signal,
    on_failure_operation_signal,
    start_workflow_signal,
    end_workflow_signal,
    start_sub_workflow_signal,
    end_sub_workflow_signal,
)


@start_operation_signal.connect
def start_operation_handler(sender, **kwargs):
    sender.context.logger.debug(
        'Event - starting operation: {sender.task_name}'.format(sender=sender))


@end_operation_signal.connect
def end_operation_handler(sender, **kwargs):
    sender.context.logger.debug(
        'Event - finished operation: {sender.task_name}'.format(sender=sender))


@on_success_operation_signal.connect
def success_operation_handler(sender, **kwargs):
    sender.context.logger.debug(
        'Event - operation success: {sender.task_name}'.format(sender=sender))


@on_failure_operation_signal.connect
def failure_operation_handler(sender, **kwargs):
    sender.context.logger.error(
        'Event - operation failure: {sender.task_name}'.format(sender=sender),
        exc_info=kwargs.get('exception', True))


@start_workflow_signal.connect
def start_workflow_handler(sender, **kwargs):
    sender.context.logger.debug(
        'Event - starting workflow: {sender.task_name}'.format(sender=sender))


@end_workflow_signal.connect
def end_workflow_handler(sender, **kwargs):
    sender.context.logger.debug(
        'Event - finished workflow: {sender.task_name}'.format(sender=sender))


@start_sub_workflow_signal.connect
def start_sub_workflow_handler(sender, **kwargs):
    sender.context.logger.debug(
        'Event - starting sub workflow: {sender.task_name}'.format(sender=sender))


@end_sub_workflow_signal.connect
def end_sub_workflow_handler(sender, **kwargs):
    sender.context.logger.debug(
        'Event - finished sub workflow: {sender.task_name}'.format(sender=sender))
