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

from datetime import datetime

import pytest

import aria
from aria import events
from aria import workflow
from aria import context
from aria.storage import models
from aria.workflows import exceptions
from aria.workflows.executor import thread
from aria.workflows.core import engine
from aria.workflows import api

from .. import mock

import tests.storage


global_test_holder = {}


class TestEngine(object):

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

    def test_single_task_successful_execution(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            graph.add_tasks(self._op(mock_success_task, ctx))
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
            graph.add_tasks(self._op(mock_failed_task, ctx))
        with pytest.raises(exceptions.ExecutorException):
            self._execute(
                workflow_func=mock_workflow,
                workflow_context=workflow_context,
                executor=executor)
        assert workflow_context.states == ['start', 'failure']
        assert isinstance(workflow_context.exception, exceptions.ExecutorException)
        assert global_test_holder.get('sent_task_signal_calls') == 1

    def test_two_tasks_execution_order(self, workflow_context, executor):
        @workflow
        def mock_workflow(ctx, graph):
            op1 = self._op(mock_ordered_task, ctx, inputs={'counter': 1})
            op2 = self._op(mock_ordered_task, ctx, inputs={'counter': 2})
            graph.sequence(op1, op2)
        self._execute(
            workflow_func=mock_workflow,
            workflow_context=workflow_context,
            executor=executor)
        assert workflow_context.states == ['start', 'success']
        assert workflow_context.exception is None
        assert global_test_holder.get('invocations') == [1, 2]
        assert global_test_holder.get('sent_task_signal_calls') == 2

    @staticmethod
    def _execute(workflow_func, workflow_context, executor):
        graph = workflow_func(ctx=workflow_context)
        eng = engine.Engine(executor=executor, workflow_context=workflow_context, tasks_graph=graph)
        eng.execute()

    @staticmethod
    def _op(func, ctx, inputs=None):
        return api.task.OperationTask(
            name='task',
            operation_details={'operation': 'tests.workflows.test_engine.{name}'.format(
                name=func.__name__)},
            node_instance=ctx.model.node_instance.get('dependency_node_instance'),
            inputs=inputs
        )

    @pytest.fixture(scope='function', autouse=True)
    def globals_cleanup(self):
        try:
            yield
        finally:
            global_test_holder.clear()

    @pytest.fixture(scope='function', autouse=True)
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

        events.start_workflow_signal.connect(start_workflow_handler)
        events.on_success_workflow_signal.connect(success_workflow_handler)
        events.on_failure_workflow_signal.connect(failure_workflow_handler)
        events.sent_task_signal.connect(sent_task_handler)
        try:
            yield
        finally:
            events.start_workflow_signal.disconnect(start_workflow_handler)
            events.on_success_workflow_signal.disconnect(success_workflow_handler)
            events.on_failure_workflow_signal.disconnect(failure_workflow_handler)
            events.sent_task_signal.disconnect(sent_task_handler)

    @pytest.fixture(scope='function')
    def executor(self):
        result = thread.ThreadExecutor()
        try:
            yield result
        finally:
            result.close()

    @pytest.fixture(scope='function')
    def workflow_context(self):
        model_storage = aria.application_model_storage(tests.storage.InMemoryModelDriver())
        model_storage.setup()
        deployment = models.Deployment(
            id='d1',
            blueprint_id='b1',
            description=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            workflows={})
        model_storage.deployment.store(deployment)
        node = mock.models.get_dependency_node()
        node_instance = mock.models.get_dependency_node_instance(node)
        model_storage.node.store(node)
        model_storage.node_instance.store(node_instance)
        result = context.workflow.WorkflowContext(
            name='test',
            model_storage=model_storage,
            resource_storage=None,
            deployment_id=deployment.id,
            workflow_id='name')
        result.states = []
        result.exception = None
        return result


def mock_success_task():
    pass


def mock_failed_task():
    raise RuntimeError


def mock_ordered_task(counter):
    invocations = global_test_holder.setdefault('invocations', [])
    invocations.append(counter)
