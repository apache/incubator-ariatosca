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
Dry executor
"""

from datetime import datetime

from .base import BaseExecutor


class DryExecutor(BaseExecutor):
    """
    Executor which dry runs tasks - prints task information without causing any side effects
    """

    def execute(self, task):
        # updating the task manually instead of calling self._task_started(task),
        # to avoid any side effects raising that event might cause
        with task._update():
            task.started_at = datetime.utcnow()
            task.status = task.STARTED

        actor_type = type(task.actor).__name__.lower()
        implementation = '{0} > '.format(task.plugin) if task.plugin else ''
        implementation += task.implementation
        inputs = dict(inp.unwrap() for inp in task.inputs.values())

        task.context.logger.info(
            'Executing {actor_type} {task.actor.name} operation {task.interface_name} '
            '{task.operation_name}: {implementation} (Inputs: {inputs})'
            .format(actor_type=actor_type, task=task, implementation=implementation, inputs=inputs))

        # updating the task manually instead of calling self._task_succeeded(task),
        # to avoid any side effects raising that event might cause
        with task._update():
            task.ended_at = datetime.utcnow()
            task.status = task.SUCCESS
