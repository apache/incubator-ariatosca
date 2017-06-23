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
Celery task executor.
"""

import threading
import Queue

from aria.orchestrator.workflows.executor import BaseExecutor


class CeleryExecutor(BaseExecutor):
    """
    Celery task executor.
    """

    def __init__(self, app, *args, **kwargs):
        super(CeleryExecutor, self).__init__(*args, **kwargs)
        self._app = app
        self._started_signaled = False
        self._started_queue = Queue.Queue(maxsize=1)
        self._tasks = {}
        self._results = {}
        self._receiver = None
        self._stopped = False
        self._receiver_thread = threading.Thread(target=self._events_receiver)
        self._receiver_thread.daemon = True
        self._receiver_thread.start()
        self._started_queue.get(timeout=30)

    def _execute(self, ctx):
        self._tasks[ctx.id] = ctx
        arguments = dict(arg.unwrapped for arg in ctx.arguments.values())
        arguments['ctx'] = ctx.context
        self._results[ctx.id] = self._app.send_task(
            ctx.operation_mapping,
            kwargs=arguments,
            task_id=ctx.id,
            queue=self._get_queue(ctx))

    def close(self):
        self._stopped = True
        if self._receiver:
            self._receiver.should_stop = True
        self._receiver_thread.join()

    @staticmethod
    def _get_queue(task):
        return None if task else None  # TODO

    def _events_receiver(self):
        with self._app.connection() as connection:
            self._receiver = self._app.events.Receiver(connection, handlers={
                'task-started': self._celery_task_started,
                'task-succeeded': self._celery_task_succeeded,
                'task-failed': self._celery_task_failed,
            })
            for _ in self._receiver.itercapture(limit=None, timeout=None, wakeup=True):
                if not self._started_signaled:
                    self._started_queue.put(True)
                    self._started_signaled = True
                if self._stopped:
                    return

    def _celery_task_started(self, event):
        self._task_started(self._tasks[event['uuid']])

    def _celery_task_succeeded(self, event):
        task, _ = self._remove_task(event['uuid'])
        self._task_succeeded(task)

    def _celery_task_failed(self, event):
        task, async_result = self._remove_task(event['uuid'])
        try:
            exception = async_result.result
        except BaseException as e:
            exception = RuntimeError(
                'Could not de-serialize exception of task {0} --> {1}: {2}'
                .format(task.name, type(e).__name__, str(e)))
        self._task_failed(task, exception=exception)

    def _remove_task(self, task_id):
        return self._tasks.pop(task_id), self._results.pop(task_id)
