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
import Queue
from importlib import import_module

from aria.events import (
    start_task_signal,
    on_success_task_signal,
    on_failure_task_signal,
)


class Executor(object):

    def execute(self, task):
        raise NotImplementedError

    def task_started(self, task_id):
        start_task_signal.send(self, task_id=task_id)

    def task_failed(self, task_id, exception):
        on_failure_task_signal.send(self, task_id=task_id, exception=exception)

    def task_succeeded(self, task_id):
        on_success_task_signal.send(self, task_id=task_id)


class LocalThreadExecutor(Executor):

    def __init__(self, pool_size=1):
        self.stopped = False
        self.queue = Queue.Queue()
        self.pool = []
        for i in range(pool_size):
            name = 'LocalThreadExecutor-{index}'.format(index=i+1)
            thread = threading.Thread(target=self._processor, name=name)
            thread.daemon = True
            thread.start()
            self.pool.append(thread)

    def execute(self, task):
        self.queue.put(task)

    def close(self):
        self.stopped = True

    def _processor(self):
        while not self.stopped:
            try:
                task = self.queue.get(timeout=1)
                self.task_started(task.id)
                try:
                    operation_context = task.operation_context
                    task_func = self._load_task(operation_context.operation_details['operation'])
                    task_func(**operation_context.inputs)
                    self.task_succeeded(task.id)
                except BaseException as e:
                    self.task_failed(task.id, exception=e)
            # Daemon threads
            except:
                pass

    def _load_task(self, handler_path):
        module_name, spec_handler_name = handler_path.rsplit('.', 1)
        try:
            module = import_module(module_name)
            return getattr(module, spec_handler_name)
        except ImportError:
            # TODO: handle
            raise
        except AttributeError:
            # TODO: handle
            raise
