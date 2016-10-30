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
from aria.workflows.executor import (
    thread,
    multiprocess,
    blocking,
    # celery
)

try:
    import celery as _celery
    app = _celery.Celery()
    app.conf.update(CELERY_RESULT_BACKEND='amqp://')
except ImportError:
    _celery = None
    app = None


class TestExecutor(object):

    @pytest.mark.parametrize('executor_cls,executor_kwargs', [
        (thread.ThreadExecutor, {'pool_size': 1}),
        (thread.ThreadExecutor, {'pool_size': 2}),
        (multiprocess.MultiprocessExecutor, {'pool_size': 1}),
        (multiprocess.MultiprocessExecutor, {'pool_size': 2}),
        (blocking.CurrentThreadBlockingExecutor, {}),
        # (celery.CeleryExecutor, {'app': app})
    ])
    def test_execute(self, executor_cls, executor_kwargs):
        self.executor = executor_cls(**executor_kwargs)
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
            assert isinstance(failing_task.exception, MockException)
            assert isinstance(task_with_inputs.exception, MockException)
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
    raise MockException


def mock_task_with_input(input):
    raise MockException(input)

if app:
    mock_successful_task = app.task(mock_successful_task)
    mock_failing_task = app.task(mock_failing_task)
    mock_task_with_input = app.task(mock_task_with_input)


class MockException(Exception):
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
