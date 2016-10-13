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

import logging
import uuid

import pytest
import retrying

from aria import events
from aria.storage import models
from aria.workflows.core import executor


class TestExecutor(object):

    @pytest.mark.parametrize('pool_size,executor_cls', [
        (1, executor.ThreadExecutor),
        (2, executor.ThreadExecutor),
        (1, executor.MultiprocessExecutor),
        (2, executor.MultiprocessExecutor),
        (0, executor.CurrentThreadBlockingExecutor)
    ])
    def test_execute(self, pool_size, executor_cls):
        self.executor = executor_cls(pool_size)
        expected_value = 'value'
        successful_task = MockTask(mock_successful_task)
        failing_task = MockTask(mock_failing_task)
        task_with_inputs = MockTask(mock_task_with_input, inputs={'input': expected_value})

        for task in [successful_task, failing_task, task_with_inputs]:
            self.executor.execute(task)

        @retrying.retry(stop_max_delay=10000, wait_fixed=100)
        def assertion():
            assert successful_task.states == ['start', 'success']
            assert failing_task.states == ['start', 'failure']
            assert task_with_inputs.states == ['start', 'failure']
            assert isinstance(failing_task.exception, TestException)
            assert isinstance(task_with_inputs.exception, TestException)
            assert task_with_inputs.exception.message == expected_value
        assertion()

    def setup_method(self):
        events.start_task_signal.connect(start_handler)
        events.on_success_task_signal.connect(success_handler)
        events.on_failure_task_signal.connect(failure_handler)

    def teardown_method(self):
        events.start_task_signal.disconnect(start_handler)
        events.on_success_task_signal.disconnect(success_handler)
        events.on_failure_task_signal.disconnect(failure_handler)
        if self.executor:
            self.executor.close()


def mock_successful_task():
    pass


def mock_failing_task():
    raise TestException


def mock_task_with_input(input):
    raise TestException(input)


class TestException(Exception):
    pass


class MockContext(object):

    def __init__(self, operation_details, inputs):
        self.operation_details = operation_details
        self.inputs = inputs
        self.operation = models.Operation(execution_id='')


class MockTask(object):

    def __init__(self, func, inputs=None):
        self.states = []
        self.exception = None
        self.id = str(uuid.uuid4())
        name = func.__name__
        operation = 'tests.workflows.test_executor.{name}'.format(name=name)
        self.context = MockContext(operation_details={'operation': operation},
                                   inputs=inputs or {})
        self.logger = logging.getLogger()
        self.name = name


def start_handler(task, *args, **kwargs):
    task.states.append('start')


def success_handler(task, *args, **kwargs):
    task.states.append('success')


def failure_handler(task, exception, *args, **kwargs):
    task.states.append('failure')
    task.exception = exception
