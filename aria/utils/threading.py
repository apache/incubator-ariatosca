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
Threading utilities.
"""

from __future__ import absolute_import  # so we can import standard 'threading'

import sys
import itertools
import multiprocessing
from threading import (Thread, Lock)
from Queue import (Queue, Full, Empty)

from .exceptions import print_exception

class ExecutorException(Exception):
    pass


class DaemonThread(Thread):
    def __init__(self, *args, **kwargs):
        super(DaemonThread, self).__init__(*args, **kwargs)
        self.daemon = True

    def run(self):
        """
        We're overriding ``Thread.run`` in order to avoid annoying (but harmless) error messages
        during shutdown. The problem is that CPython nullifies the global state _before_ shutting
        down daemon threads, so that exceptions might happen, and then ``Thread.__bootstrap_inner``
        prints them out.

        Our solution is to swallow these exceptions here.

        The side effect is that uncaught exceptions in our own thread code will _not_ be printed out
        as usual, so it's our responsibility to catch them in our code.
        """

        try:
            super(DaemonThread, self).run()
        except SystemExit as e:
            # This exception should be bubbled up
            raise e
        except BaseException:
            # Exceptions might occur in daemon threads during interpreter shutdown
            pass


# https://gist.github.com/tliron/81dd915166b0bfc64be08b4f8e22c835
class FixedThreadPoolExecutor(object):
    """
    Executes tasks in a fixed thread pool.

    Makes sure to gather all returned results and thrown exceptions in one place, in order of task
    submission.

    Example::

        def sum(arg1, arg2):
            return arg1 + arg2

        executor = FixedThreadPoolExecutor(10)
        try:
            for value in range(100):
                executor.submit(sum, value, value)
            executor.drain()
        except:
            executor.close()
        executor.raise_first()
        print executor.returns

    You can also use it with the Python ``with`` keyword, in which case you don't need to call
    ``close`` explicitly::

        with FixedThreadPoolExecutor(10) as executor:
            for value in range(100):
                executor.submit(sum, value, value)
            executor.drain()
            executor.raise_first()
            print executor.returns
    """

    _CYANIDE = object()  # Special task marker used to kill worker threads.

    def __init__(self,
                 size=None,
                 timeout=None,
                 print_exceptions=False):
        """
        :param size: number of threads in the pool; if ``None`` will use an optimal number for the
         platform
        :param timeout: timeout in seconds for all blocking operations (``None`` means no timeout)
        :param print_exceptions: set to ``True`` in order to print exceptions from tasks
        """
        if not size:
            try:
                size = multiprocessing.cpu_count() * 2 + 1
            except NotImplementedError:
                size = 3

        self.size = size
        self.timeout = timeout
        self.print_exceptions = print_exceptions

        self._tasks = Queue()
        self._returns = {}
        self._exceptions = {}
        self._id_creator = itertools.count()
        self._lock = Lock() # for console output

        self._workers = []
        for index in range(size):
            worker = DaemonThread(
                name='%s%d' % (self.__class__.__name__, index),
                target=self._thread_worker)
            worker.start()
            self._workers.append(worker)

    def submit(self, func, *args, **kwargs):
        """
        Submit a task for execution.

        The task will be called ASAP on the next available worker thread in the pool.

        :raises ExecutorException: if cannot be submitted
        """

        try:
            self._tasks.put((self._id_creator.next(), func, args, kwargs), timeout=self.timeout)
        except Full:
            raise ExecutorException('cannot submit task: queue is full')

    def close(self):
        """
        Blocks until all current tasks finish execution and all worker threads are dead.

        You cannot submit tasks anymore after calling this.

        This is called automatically upon exit if you are using the ``with`` keyword.
        """

        self.drain()
        while self.is_alive:
            try:
                self._tasks.put(self._CYANIDE, timeout=self.timeout)
            except Full:
                raise ExecutorException('cannot close executor: a thread seems to be hanging')
        self._workers = None

    def drain(self):
        """
        Blocks until all current tasks finish execution, but leaves the worker threads alive.
        """

        self._tasks.join()  # oddly, the API does not support a timeout parameter

    @property
    def is_alive(self):
        """
        True if any of the worker threads are alive.
        """

        for worker in self._workers:
            if worker.is_alive():
                return True
        return False

    @property
    def returns(self):
        """
        The returned values from all tasks, in order of submission.
        """

        return [self._returns[k] for k in sorted(self._returns)]

    @property
    def exceptions(self):
        """
        The raised exceptions from all tasks, in order of submission.
        """

        return [self._exceptions[k] for k in sorted(self._exceptions)]

    def raise_first(self):
        """
        If exceptions were thrown by any task, then the first one will be raised.

        This is rather arbitrary: proper handling would involve iterating all the exceptions.
        However, if you want to use the "raise" mechanism, you are limited to raising only one of
        them.
        """

        exceptions = self.exceptions
        if exceptions:
            raise exceptions[0]

    def _thread_worker(self):
        while True:
            if not self._execute_next_task():
                break

    def _execute_next_task(self):
        try:
            task = self._tasks.get(timeout=self.timeout)
        except Empty:
            # Happens if timeout is reached
            return True
        if task == self._CYANIDE:
            # Time to die :(
            return False
        self._execute_task(*task)
        return True

    def _execute_task(self, task_id, func, args, kwargs):
        try:
            result = func(*args, **kwargs)
            self._returns[task_id] = result
        except Exception as e:
            self._exceptions[task_id] = e
            if self.print_exceptions:
                with self._lock:
                    print_exception(e)
        self._tasks.task_done()

    def __enter__(self):
        return self

    def __exit__(self, the_type, value, traceback):
        self.close()
        return False


class LockedList(list):
    """
    A list that supports the ``with`` keyword with a built-in lock.

    Though Python lists are thread-safe in that they will not raise exceptions during concurrent
    access, they do not guarantee atomicity. This class will let you gain atomicity when needed.
    """

    def __init__(self, *args, **kwargs):
        super(LockedList, self).__init__(*args, **kwargs)
        self.lock = Lock()

    def __enter__(self):
        return self.lock.__enter__()

    def __exit__(self, the_type, value, traceback):
        return self.lock.__exit__(the_type, value, traceback)


class ExceptionThread(Thread):
    """
    A thread from which top level exceptions can be retrieved or re-raised.
    """
    def __init__(self, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.exception = None
        self.daemon = True

    def run(self):
        try:
            super(ExceptionThread, self).run()
        except BaseException:
            self.exception = sys.exc_info()

    def is_error(self):
        return self.exception is not None

    def raise_error_if_exists(self):
        if self.is_error():
            type_, value, trace = self.exception
            raise type_, value, trace
