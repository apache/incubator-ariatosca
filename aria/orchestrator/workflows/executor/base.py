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
Base executor module
"""

from aria import logger
from aria.orchestrator import events


class BaseExecutor(logger.LoggerMixin):
    """
    Base class for executors for running tasks
    """

    def execute(self, task):
        """
        Execute a task
        :param task: task to execute
        """
        raise NotImplementedError

    def close(self):
        """
        Close the executor
        """
        pass

    @staticmethod
    def _task_started(task):
        events.start_task_signal.send(task)

    @staticmethod
    def _task_failed(task, exception, traceback=None):
        events.on_failure_task_signal.send(task, exception=exception, traceback=traceback)

    @staticmethod
    def _task_succeeded(task):
        events.on_success_task_signal.send(task)
