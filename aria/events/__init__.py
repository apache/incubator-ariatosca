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

import os

from blinker import signal

from ..tools.plugin import plugin_installer


# workflow engine default signals:
start_task_signal = signal('start_task_signal')
end_task_signal = signal('end_task_signal')
on_success_task_signal = signal('success_task_signal')
on_failure_task_signal = signal('failure_task_signal')

# workflow engine workflow signals:
start_workflow_signal = signal('start_workflow_signal')
end_workflow_signal = signal('end_workflow_signal')
on_success_workflow_signal = signal('on_success_workflow_signal')
on_failure_workflow_signal = signal('on_failure_workflow_signal')
start_sub_workflow_signal = signal('start_sub_workflow_signal')
end_sub_workflow_signal = signal('end_sub_workflow_signal')

# workflow engine operation signals:
start_operation_signal = signal('start_operation_signal')
end_operation_signal = signal('end_operation_signal')
on_success_operation_signal = signal('on_success_operation_signal')
on_failure_operation_signal = signal('on_failure_operation_signal')

plugin_installer(
    path=os.path.dirname(os.path.realpath(__file__)),
    plugin_suffix='_event_handler',
    package=__package__)
