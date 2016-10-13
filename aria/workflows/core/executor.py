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

import threading
import multiprocessing
import Queue

import jsonpickle

from aria import events
from aria.tools import module


class BaseExecutor(object):

    def __init__(self, *args, **kwargs):
        pass

    def execute(self, task):
        raise NotImplementedError

    def close(self):
        pass

    @staticmethod
    def _task_started(task):
        events.start_task_signal.send(task)

    @staticmethod
    def _task_failed(task, exception):
        events.on_failure_task_signal.send(task, exception=exception)

    @staticmethod
    def _task_succeeded(task):
        events.on_success_task_signal.send(task)


class CurrentThreadBlockingExecutor(BaseExecutor):

    def execute(self, task):
        self._task_started(task)
        try:
            operation_context = task.context
            task_func = module.load_attribute(operation_context.operation_details['operation'])
            task_func(**operation_context.inputs)
            self._task_succeeded(task)
        except BaseException as e:
            self._task_failed(task, exception=e)


class ThreadExecutor(BaseExecutor):

    def __init__(self, pool_size=1, *args, **kwargs):
        super(ThreadExecutor, self).__init__(*args, **kwargs)
        self._stopped = False
        self._queue = Queue.Queue()
        self._pool = []
        for i in range(pool_size):
            name = 'ThreadExecutor-{index}'.format(index=i+1)
            thread = threading.Thread(target=self._processor, name=name)
            thread.daemon = True
            thread.start()
            self._pool.append(thread)

    def execute(self, task):
        self._queue.put(task)

    def close(self):
        self._stopped = True
        for thread in self._pool:
            thread.join()

    def _processor(self):
        while not self._stopped:
            try:
                task = self._queue.get(timeout=1)
                self._task_started(task)
                try:
                    operation_context = task.context
                    task_func = module.load_attribute(
                        operation_context.operation_details['operation'])
                    task_func(**operation_context.inputs)
                    self._task_succeeded(task)
                except BaseException as e:
                    self._task_failed(task, exception=e)
            # Daemon threads
            except:
                pass


class MultiprocessExecutor(BaseExecutor):

    def __init__(self, pool_size=1, *args, **kwargs):
        super(MultiprocessExecutor, self).__init__(*args, **kwargs)
        self._stopped = False
        self._manager = multiprocessing.Manager()
        self._queue = self._manager.Queue()
        self._tasks = {}
        self._listener = threading.Thread(target=self._listener)
        self._listener.daemon = True
        self._listener.start()
        self._pool = multiprocessing.Pool(processes=pool_size,
                                          maxtasksperchild=1)

    def execute(self, task):
        self._tasks[task.id] = task
        self._pool.apply_async(_multiprocess_handler, args=(
            self._queue,
            task.id,
            task.context.operation_details,
            task.context.inputs))

    def close(self):
        self._pool.close()
        self._stopped = True
        self._pool.join()
        self._listener.join()

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
            except:
                pass

    def _remove_task(self, task_id):
        return self._tasks.pop(task_id)


class _MultiprocessMessage(object):

    def __init__(self, type, task_id, exception=None):
        self.type = type
        self.task_id = task_id
        self.exception = exception


def _multiprocess_handler(queue, task_id, operation_details, operation_inputs):
    queue.put(_MultiprocessMessage(type='task_started', task_id=task_id))
    try:
        task_func = module.load_attribute(operation_details['operation'])
        task_func(**operation_inputs)
        queue.put(_MultiprocessMessage(type='task_succeeded', task_id=task_id))
    except BaseException as e:
        queue.put(_MultiprocessMessage(type='task_failed', task_id=task_id,
                                       exception=jsonpickle.dumps(e)))
