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
    def _execute(self, task):
        raise NotImplementedError

    def execute(self, ctx):
        """
        Execute a task
        :param task: task to execute
        """
        if ctx.task.function:
            self._execute(ctx)
        else:
            # In this case the task is missing a function. This task still gets to an
            # executor, but since there is nothing to run, we by default simply skip the
            # execution itself.
            self._task_started(ctx)
            self._task_succeeded(ctx)

    def close(self):
        """
        Close the executor
        """
        pass

    @staticmethod
    def _task_started(ctx):
        events.start_task_signal.send(ctx)

    @staticmethod
    def _task_failed(ctx, exception, traceback=None):
        events.on_failure_task_signal.send(ctx, exception=exception, traceback=traceback)

    @staticmethod
    def _task_succeeded(ctx):
        events.on_success_task_signal.send(ctx)


class StubTaskExecutor(BaseExecutor):                                                               # pylint: disable=abstract-method
    def execute(self, ctx, *args, **kwargs):
        with ctx.persist_changes:
            ctx.task.status = ctx.task.SUCCESS
