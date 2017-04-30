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
import time
import threading
from datetime import datetime

import pytest

from aria.orchestrator import (
    events,
    workflow,
    operation,
)
from aria.modeling import models
from aria.orchestrator.workflows import (
    api,
    exceptions,
)
from aria.orchestrator.workflows.core import engine
from aria.orchestrator.workflows.executor import thread

from tests import mock, storage


global_test_holder = {}


class BaseTest(object):

    @classmethod
    def _execute(cls, workflow_func, workflow_context, executor):
        eng = cls._engine(workflow_func=workflow_func,
                          workflow_context=workflow_context,
                          executor=executor)
        eng.execute()
        return eng

    @staticmethod
    def _engine(workflow_func, workflow_context, executor):
        graph = workflow_func(ctx=workflow_context)
        return engine.Engine(executor=executor,
                             workflow_context=workflow_context,
                             tasks_graph=graph)

    @staticmethod
    def _op(ctx,
            func,
            inputs=None,
            max_attempts=None,
            retry_interval=None,
            ignore_failure=None):
        node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
        interface_name = 'aria.interfaces.lifecycle'
        operation_kwargs = dict(implementation='{name}.{func.__name__}'.format(
            name=__name__, func=func))
        if inputs:
            # the operation has to declare the inputs before those may be passed
            operation_kwargs['inputs'] = inputs
        operation_name = 'create'
        interface = mock.models.create_interface(node.service, interface_name, operation_name,
                                                 operation_kwargs=operation_kwargs)
        node.interfaces[interface.name] = interface

        return api.task.OperationTask(
            node,
            interface_name='aria.interfaces.lifecycle',
            operation_name=operation_name,
            inputs=inputs or {},
            max_attempts=max_attempts,
            retry_interval=retry_interval,
            ignore_failure=ignore_failure,
        )

    @pytest.fixture(autouse=True)
    def globals_cleanup(self):
        try:
            yield
        finally:
            global_test_holder.clear()

    @pytest.fixture(autouse=True)
    def signals_registration(self, ):
        def sent_task_handler(*args, **kwargs):
            calls = global_test_holder.setdefault('sent_task_signal_calls', 0)
            global_test_holder['sent_task_signal_calls'] = calls + 1

        def start_workflow_handler(workflow_context, *args, **kwargs):
            workflow_context.states.append('start')

        def success_workflow_handler(workflow_context, *args, **kwargs):
            workflow_context.states.append('success')

        def failure_workflow_handler(workflow_context, exception, *args, **kwargs):
            workflow_context.states.append('failure')
            workflow_context.exception = exception

        def cancel_workflow_handler(workflow_context, *args, **kwargs):
            workflow_context.states.append('cancel')

        events.start_workflow_signal.connect(start_workflow_handler)
        events.on_success_workflow_signal.connect(success_workflow_handler)
        events.on_failure_workflow_signal.connect(failure_workflow_handler)
        events.on_cancelled_workflow_signal.connect(cancel_workflow_handler)
        events.sent_task_signal.connect(sent_task_handler)
        try:
            yield
        finally:
            events.start_workflow_signal.disconnect(start_workflow_handler)
            events.on_success_workflow_signal.disconnect(success_workflow_handler)
            events.on_failure_workflow_signal.disconnect(failure_workflow_handler)
            events.on_cancelled_workflow_signal.disconnect(cancel_workflow_handler)
            events.sent_task_signal.disconnect(sent_task_handler)

    @pytest.fixture
    def executor(self):
        result = thread.ThreadExecutor()
        try:
            yield result
        finally:
            result.close()

    @pytest.fixture
    def workflow_context(self, tmpdir):
        workflow_context = mock.context.simple(str(tmpdir))
        workflow_context.states = []
        workflow_context.exception = None
        yield workflow_context
        storage.release_sqlite_storage(workflow_context.model)


class TestEngine(BaseTest):

    def test_empty_graph_execution(self, workflow_context, executor):
        @workflow
        def mock_workflow(**_):
            pass
        self._execute(workflow_func=mock_workflow,
                      workflow_context=workflow_context,
                      executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        assert 'sent_task_signal_calls' not in global_test_holder
        execution = workflow_context.execution
        assert execution.started_at <= execution.ended_at <= datetime.utcnow()
        assert execution.error is None
        assert execution.status == models.Execution.SUCCEEDED

    def test_single_task_successful_execution(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            graph.add_tasks(self._op(ctx, func=mock_success_task))
        self._execute(
            workflow_func=mock_workflow,
            workflow_context=workflow_context,
            executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        assert global_test_holder.get('sent_task_signal_calls') == 1

    def test_single_task_failed_execution(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            graph.add_tasks(self._op(ctx, func=mock_failed_task))
        with pytest.raises(exceptions.ExecutorException):
            self._execute(
                workflow_func=mock_workflow,
                workflow_context=workflow_context,
                executor=executor)
        assert workflow_context.states == ['start', 'failure']
        assert isinstance(workflow_context.exception, exceptions.ExecutorException)
        assert global_test_holder.get('sent_task_signal_calls') == 1
        execution = workflow_context.execution
        assert execution.started_at <= execution.ended_at <= datetime.utcnow()
        assert execution.error is not None
        assert execution.status == models.Execution.FAILED

    def test_two_tasks_execution_order(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op1 = self._op(ctx, func=mock_ordered_task, inputs={'counter': 1})
            op2 = self._op(ctx, func=mock_ordered_task, inputs={'counter': 2})
            graph.sequence(op1, op2)
        self._execute(
            workflow_func=mock_workflow,
            workflow_context=workflow_context,
            executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        assert global_test_holder.get('invocations') == [1, 2]
        assert global_test_holder.get('sent_task_signal_calls') == 2

    def test_stub_and_subworkflow_execution(self, workflow_context, executor):
        @workflow
        def sub_workflow(ctx, graph):
            op1 = self._op(ctx, func=mock_ordered_task, inputs={'counter': 1})
            op2 = api.task.StubTask()
            op3 = self._op(ctx, func=mock_ordered_task, inputs={'counter': 2})
            graph.sequence(op1, op2, op3)

        @workflow
        def mock_workflow(ctx, graph):
            graph.add_tasks(api.task.WorkflowTask(sub_workflow, ctx=ctx))
        self._execute(workflow_func=mock_workflow,
                      workflow_context=workflow_context,
                      executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        assert global_test_holder.get('invocations') == [1, 2]
        assert global_test_holder.get('sent_task_signal_calls') == 2


class TestCancel(BaseTest):

    def test_cancel_started_execution(self, workflow_context, executor):
        number_of_tasks = 100

        @workflow
        def mock_workflow(ctx, graph):
            operations = (
                self._op(ctx, func=mock_sleep_task, inputs=dict(seconds=0.1))
                for _ in range(number_of_tasks)
            )
            return graph.sequence(*operations)

        eng = self._engine(workflow_func=mock_workflow,
                           workflow_context=workflow_context,
                           executor=executor)
        t = threading.Thread(target=eng.execute)
        t.start()
        time.sleep(10)
        eng.cancel_execution()
        t.join(timeout=60) # we need to give this a *lot* of time because Travis can be *very* slow
        assert not t.is_alive() # if join is timed out it will not raise an exception
        assert workflow_context.states == ['start', 'cancel']
        assert workflow_context.exception is None
        invocations = global_test_holder.get('invocations', [])
        assert 0 < len(invocations) < number_of_tasks
        execution = workflow_context.execution
        assert execution.started_at <= execution.ended_at <= datetime.utcnow()
        assert execution.error is None
        assert execution.status == models.Execution.CANCELLED

    def test_cancel_pending_execution(self, workflow_context, executor):
        @workflow
        def mock_workflow(graph, **_):
            return graph
        eng = self._engine(workflow_func=mock_workflow,
                           workflow_context=workflow_context,
                           executor=executor)
        eng.cancel_execution()
        execution = workflow_context.execution
        assert execution.status == models.Execution.CANCELLED


class TestRetries(BaseTest):

    def test_two_max_attempts_and_success_on_retry(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_conditional_failure_task,
                          inputs={'failure_count': 1},
                          max_attempts=2)
            graph.add_tasks(op)
        self._execute(
            workflow_func=mock_workflow,
            workflow_context=workflow_context,
            executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        assert len(global_test_holder.get('invocations', [])) == 2
        assert global_test_holder.get('sent_task_signal_calls') == 2

    def test_two_max_attempts_and_failure_on_retry(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_conditional_failure_task,
                          inputs={'failure_count': 2},
                          max_attempts=2)
            graph.add_tasks(op)
        with pytest.raises(exceptions.ExecutorException):
            self._execute(
                workflow_func=mock_workflow,
                workflow_context=workflow_context,
                executor=executor)
        assert workflow_context.states == ['start', 'failure']
        assert isinstance(workflow_context.exception, exceptions.ExecutorException)
        assert len(global_test_holder.get('invocations', [])) == 2
        assert global_test_holder.get('sent_task_signal_calls') == 2

    def test_three_max_attempts_and_success_on_first_retry(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_conditional_failure_task,
                          inputs={'failure_count': 1},
                          max_attempts=3)
            graph.add_tasks(op)
        self._execute(
            workflow_func=mock_workflow,
            workflow_context=workflow_context,
            executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        assert len(global_test_holder.get('invocations', [])) == 2
        assert global_test_holder.get('sent_task_signal_calls') == 2

    def test_three_max_attempts_and_success_on_second_retry(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_conditional_failure_task,
                          inputs={'failure_count': 2},
                          max_attempts=3)
            graph.add_tasks(op)
        self._execute(
            workflow_func=mock_workflow,
            workflow_context=workflow_context,
            executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        assert len(global_test_holder.get('invocations', [])) == 3
        assert global_test_holder.get('sent_task_signal_calls') == 3

    def test_infinite_retries(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_conditional_failure_task,
                          inputs={'failure_count': 1},
                          max_attempts=-1)
            graph.add_tasks(op)
        self._execute(
            workflow_func=mock_workflow,
            workflow_context=workflow_context,
            executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        assert len(global_test_holder.get('invocations', [])) == 2
        assert global_test_holder.get('sent_task_signal_calls') == 2

    def test_retry_interval_float(self, workflow_context, executor):
        self._test_retry_interval(retry_interval=0.3,
                                  workflow_context=workflow_context,
                                  executor=executor)

    def test_retry_interval_int(self, workflow_context, executor):
        self._test_retry_interval(retry_interval=1,
                                  workflow_context=workflow_context,
                                  executor=executor)

    def _test_retry_interval(self, retry_interval, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_conditional_failure_task,
                          inputs={'failure_count': 1},
                          max_attempts=2,
                          retry_interval=retry_interval)
            graph.add_tasks(op)
        self._execute(
            workflow_func=mock_workflow,
            workflow_context=workflow_context,
            executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        invocations = global_test_holder.get('invocations', [])
        assert len(invocations) == 2
        invocation1, invocation2 = invocations
        assert invocation2 - invocation1 >= retry_interval
        assert global_test_holder.get('sent_task_signal_calls') == 2

    def test_ignore_failure(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_conditional_failure_task,
                          ignore_failure=True,
                          inputs={'failure_count': 100},
                          max_attempts=100)
            graph.add_tasks(op)
        self._execute(
            workflow_func=mock_workflow,
            workflow_context=workflow_context,
            executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        invocations = global_test_holder.get('invocations', [])
        assert len(invocations) == 1
        assert global_test_holder.get('sent_task_signal_calls') == 1


class TestTaskRetryAndAbort(BaseTest):
    message = 'EXPECTED_ERROR'

    def test_task_retry_default_interval(self, workflow_context, executor):
        default_retry_interval = 0.1

        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_task_retry,
                          inputs={'message': self.message},
                          retry_interval=default_retry_interval,
                          max_attempts=2)
            graph.add_tasks(op)
        with pytest.raises(exceptions.ExecutorException):
            self._execute(
                workflow_func=mock_workflow,
                workflow_context=workflow_context,
                executor=executor)
        assert workflow_context.states == ['start', 'failure']
        assert isinstance(workflow_context.exception, exceptions.ExecutorException)
        invocations = global_test_holder.get('invocations', [])
        assert len(invocations) == 2
        invocation1, invocation2 = invocations
        assert invocation2 - invocation1 >= default_retry_interval
        assert global_test_holder.get('sent_task_signal_calls') == 2

    def test_task_retry_custom_interval(self, workflow_context, executor):
        default_retry_interval = 100
        custom_retry_interval = 0.1

        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_task_retry,
                          inputs={'message': self.message,
                                  'retry_interval': custom_retry_interval},
                          retry_interval=default_retry_interval,
                          max_attempts=2)
            graph.add_tasks(op)
        execution_start = time.time()
        with pytest.raises(exceptions.ExecutorException):
            self._execute(
                workflow_func=mock_workflow,
                workflow_context=workflow_context,
                executor=executor)
        execution_end = time.time()
        assert workflow_context.states == ['start', 'failure']
        assert isinstance(workflow_context.exception, exceptions.ExecutorException)
        invocations = global_test_holder.get('invocations', [])
        assert len(invocations) == 2
        assert (execution_end - execution_start) < default_retry_interval
        assert global_test_holder.get('sent_task_signal_calls') == 2

    def test_task_abort(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op = self._op(ctx, func=mock_task_abort,
                          inputs={'message': self.message},
                          retry_interval=100,
                          max_attempts=100)
            graph.add_tasks(op)
        with pytest.raises(exceptions.ExecutorException):
            self._execute(
                workflow_func=mock_workflow,
                workflow_context=workflow_context,
                executor=executor)
        assert workflow_context.states == ['start', 'failure']
        assert isinstance(workflow_context.exception, exceptions.ExecutorException)
        invocations = global_test_holder.get('invocations', [])
        assert len(invocations) == 1
        assert global_test_holder.get('sent_task_signal_calls') == 1


@operation
def mock_success_task(**_):
    pass


@operation
def mock_failed_task(**_):
    raise RuntimeError


@operation
def mock_ordered_task(counter, **_):
    invocations = global_test_holder.setdefault('invocations', [])
    invocations.append(counter)


@operation
def mock_conditional_failure_task(failure_count, **_):
    invocations = global_test_holder.setdefault('invocations', [])
    try:
        if len(invocations) < failure_count:
            raise RuntimeError
    finally:
        invocations.append(time.time())


@operation
def mock_sleep_task(seconds, **_):
    _add_invocation_timestamp()
    time.sleep(seconds)


@operation
def mock_task_retry(ctx, message, retry_interval=None, **_):
    _add_invocation_timestamp()
    retry_kwargs = {}
    if retry_interval is not None:
        retry_kwargs['retry_interval'] = retry_interval
    ctx.task.retry(message, **retry_kwargs)


@operation
def mock_task_abort(ctx, message, **_):
    _add_invocation_timestamp()
    ctx.task.abort(message)


def _add_invocation_timestamp():
    invocations = global_test_holder.setdefault('invocations', [])
    invocations.append(time.time())
