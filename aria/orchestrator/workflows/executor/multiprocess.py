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
Multiprocess based executor
"""

import multiprocessing
import threading

import jsonpickle

from aria.tools import module
from .base import BaseExecutor


class MultiprocessExecutor(BaseExecutor):
    """
    Executor which runs tasks in a multiprocess environment
    """

    def __init__(self, pool_size=1, *args, **kwargs):
        super(MultiprocessExecutor, self).__init__(*args, **kwargs)
        self._stopped = False
        self._manager = multiprocessing.Manager()
        self._queue = self._manager.Queue()
        self._tasks = {}
        self._listener_thread = threading.Thread(target=self._listener)
        self._listener_thread.daemon = True
        self._listener_thread.start()
        self._pool = multiprocessing.Pool(processes=pool_size)

    def execute(self, task):
        self._tasks[task.id] = task
        self._pool.apply_async(_multiprocess_handler, args=(
            self._queue,
            task.context,
            task.id,
            task.operation_mapping,
            task.inputs))

    def close(self):
        self._pool.close()
        self._stopped = True
        self._pool.join()
        self._listener_thread.join()

    def _listener(self):
        while not self._stopped:
            try:
                message = self._queue.get(timeout=1)
                if message.type == 'task_started':
                    self._task_started(self._tasks[message.task_id])
                elif message.type == 'task_succeeded':
                    self._task_succeeded(self._remove_task(message.task_id))
                elif message.type == 'task_failed':
                    self._task_failed(self._remove_task(message.task_id),
                                      exception=jsonpickle.loads(message.exception))
                else:
                    # TODO: something
                    raise RuntimeError()
            # Daemon threads
            except BaseException:
                pass

    def _remove_task(self, task_id):
        return self._tasks.pop(task_id)


class _MultiprocessMessage(object):

    def __init__(self, type, task_id, exception=None):
        self.type = type
        self.task_id = task_id
        self.exception = exception


def _multiprocess_handler(queue, ctx, task_id, operation_mapping, operation_inputs):
    queue.put(_MultiprocessMessage(type='task_started', task_id=task_id))
    try:
        task_func = module.load_attribute(operation_mapping)
        task_func(ctx=ctx, **operation_inputs)
        queue.put(_MultiprocessMessage(type='task_succeeded', task_id=task_id))
    except BaseException as e:
        queue.put(_MultiprocessMessage(type='task_failed', task_id=task_id,
                                       exception=jsonpickle.dumps(e)))
