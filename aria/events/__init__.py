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
Path: aria.events

Events package provides events mechanism for different executions in aria.


1. storage_event_handler: implementation of storage handlers for workflow and operation events.
2. logger_event_handler: implementation of logger handlers for workflow and operation events.

API:
    * start_task_signal
    * on_success_task_signal
    * on_failure_task_signal
    * start_workflow_signal
    * on_success_workflow_signal
    * on_failure_workflow_signal
"""

import os

from blinker import signal

from ..tools.plugin import plugin_installer

# workflow engine task signals:
start_task_signal = signal('start_task_signal')
on_success_task_signal = signal('success_task_signal')
on_failure_task_signal = signal('failure_task_signal')

# workflow engine workflow signals:
start_workflow_signal = signal('start_workflow_signal')
on_success_workflow_signal = signal('on_success_workflow_signal')
on_failure_workflow_signal = signal('on_failure_workflow_signal')

plugin_installer(
    path=os.path.dirname(os.path.realpath(__file__)),
    plugin_suffix='_event_handler',
    package=__package__)
