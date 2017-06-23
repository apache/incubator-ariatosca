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
Thread task executor.
"""

import Queue
import threading

import sys

from aria.utils import imports, exceptions

from .base import BaseExecutor


class ThreadExecutor(BaseExecutor):
    """
    Thread task executor.

    It's easier writing tests using this executor rather than the full-blown sub-process executor.

    Note: This executor is incapable of running plugin operations.
    """

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

    def _execute(self, ctx):
        self._queue.put(ctx)

    def close(self):
        self._stopped = True
        for thread in self._pool:
            thread.join()

    def _processor(self):
        while not self._stopped:
            try:
                ctx = self._queue.get(timeout=1)
                self._task_started(ctx)
                try:
                    task_func = imports.load_attribute(ctx.task.function)
                    arguments = dict(arg.unwrapped for arg in ctx.task.arguments.values())
                    task_func(ctx=ctx, **arguments)
                    self._task_succeeded(ctx)
                except BaseException as e:
                    self._task_failed(ctx,
                                      exception=e,
                                      traceback=exceptions.get_exception_as_string(*sys.exc_info()))
            # Daemon threads
            except BaseException as e:
                pass
