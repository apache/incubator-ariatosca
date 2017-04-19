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


import pytest
import retrying

try:
    import celery as _celery
    app = _celery.Celery()
    app.conf.update(CELERY_RESULT_BACKEND='amqp://')
except ImportError:
    _celery = None
    app = None

from aria.modeling import models
from aria.orchestrator import events
from aria.orchestrator.workflows.executor import (
    thread,
    process,
    # celery
)

import tests
from . import MockTask


def _get_implementation(func):
    return '{module}.{func.__name__}'.format(module=__name__, func=func)


def test_execute(executor):
    expected_value = 'value'
    successful_task = MockTask(_get_implementation(mock_successful_task))
    failing_task = MockTask(_get_implementation(mock_failing_task))
    task_with_inputs = MockTask(_get_implementation(mock_task_with_input),
                                inputs={'input': models.Parameter.wrap('input', 'value')})

    for task in [successful_task, failing_task, task_with_inputs]:
        executor.execute(task)

    @retrying.retry(stop_max_delay=10000, wait_fixed=100)
    def assertion():
        assert successful_task.states == ['start', 'success']
        assert failing_task.states == ['start', 'failure']
        assert task_with_inputs.states == ['start', 'failure']
        assert isinstance(failing_task.exception, MockException)
        assert isinstance(task_with_inputs.exception, MockException)
        assert task_with_inputs.exception.message == expected_value
    assertion()


def mock_successful_task(**_):
    pass


def mock_failing_task(**_):
    raise MockException


def mock_task_with_input(input, **_):
    raise MockException(input)

if app:
    mock_successful_task = app.task(mock_successful_task)
    mock_failing_task = app.task(mock_failing_task)
    mock_task_with_input = app.task(mock_task_with_input)


class MockException(Exception):
    pass


@pytest.fixture(params=[
    (thread.ThreadExecutor, {'pool_size': 1}),
    (thread.ThreadExecutor, {'pool_size': 2}),
    # subprocess needs to load a tests module so we explicitly add the root directory as if
    # the project has been installed in editable mode
    (process.ProcessExecutor, {'python_path': [tests.ROOT_DIR]}),
    # (celery.CeleryExecutor, {'app': app})
])
def executor(request):
    executor_cls, executor_kwargs = request.param
    result = executor_cls(**executor_kwargs)
    yield result
    result.close()


@pytest.fixture(autouse=True)
def register_signals():
    def start_handler(task, *args, **kwargs):
        task.states.append('start')

    def success_handler(task, *args, **kwargs):
        task.states.append('success')

    def failure_handler(task, exception, *args, **kwargs):
        task.states.append('failure')
        task.exception = exception

    events.start_task_signal.connect(start_handler)
    events.on_success_task_signal.connect(success_handler)
    events.on_failure_task_signal.connect(failure_handler)
    yield
    events.start_task_signal.disconnect(start_handler)
    events.on_success_task_signal.disconnect(success_handler)
    events.on_failure_task_signal.disconnect(failure_handler)
