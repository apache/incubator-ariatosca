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

import json
import time
from threading import Thread, Event
from datetime import datetime

import pytest

from aria.modeling import exceptions as modeling_exceptions
from aria.modeling import models
from aria.orchestrator import exceptions
from aria.orchestrator import events
from aria.orchestrator import execution_preparer
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.core import engine, graph_compiler
from aria.orchestrator.workflows.executor import thread
from aria.orchestrator import (
    workflow,
    operation,
)

from tests import (
    mock as tests_mock,
    storage
)

from ...fixtures import (  # pylint: disable=unused-import
    plugins_dir,
    plugin_manager,
    fs_model as model,
    resource_storage as resource
)

custom_events = {
    'is_resumed': Event(),
    'is_active': Event(),
    'execution_cancelled': Event(),
    'execution_failed': Event(),
}


class TimeoutError(BaseException):
    pass


class FailingTask(BaseException):
    pass


def test_undeclared_workflow(request):
    # validating a proper error is raised when the workflow is not declared in the service
    with pytest.raises(exceptions.UndeclaredWorkflowError):
        _get_preparer(request, 'undeclared_workflow').prepare()


def test_missing_workflow_implementation(service, request):
    # validating a proper error is raised when the workflow code path does not exist
    workflow = models.Operation(
        name='test_workflow',
        service=service,
        function='nonexistent.workflow.implementation')
    service.workflows['test_workflow'] = workflow

    with pytest.raises(exceptions.WorkflowImplementationNotFoundError):
        _get_preparer(request, 'test_workflow').prepare()


def test_builtin_workflow_instantiation(request):
    # validates the workflow runner instantiates properly when provided with a builtin workflow
    # (expecting no errors to be raised on undeclared workflow or missing workflow implementation)
    workflow_ctx = _get_preparer(request, 'install').prepare()
    assert len(workflow_ctx.execution.tasks) == 18  # expecting 18 tasks for 2 node topology


def test_custom_workflow_instantiation(request):
    # validates the workflow runner instantiates properly when provided with a custom workflow
    # (expecting no errors to be raised on undeclared workflow or missing workflow implementation)
    mock_workflow = _setup_mock_workflow_in_service(request)
    workflow_ctx = _get_preparer(request, mock_workflow).prepare()
    assert len(workflow_ctx.execution.tasks) == 2   # mock workflow creates only start workflow
                                                    # and end workflow task


def test_existing_active_executions(request, service, model):
    existing_active_execution = models.Execution(
        service=service,
        status=models.Execution.STARTED,
        workflow_name='uninstall')
    model.execution.put(existing_active_execution)
    with pytest.raises(exceptions.ActiveExecutionsError):
        _get_preparer(request, 'install').prepare()


def test_existing_executions_but_no_active_ones(request, service, model):
    existing_terminated_execution = models.Execution(
        service=service,
        status=models.Execution.SUCCEEDED,
        workflow_name='uninstall')
    model.execution.put(existing_terminated_execution)
    # no active executions exist, so no error should be raised
    _get_preparer(request, 'install').prepare()


def test_execution_model_creation(request, service):
    mock_workflow = _setup_mock_workflow_in_service(request)

    workflow_ctx = _get_preparer(request, mock_workflow).prepare()

    assert workflow_ctx.execution.service.id == service.id
    assert workflow_ctx.execution.workflow_name == mock_workflow
    assert workflow_ctx.execution.created_at <= datetime.utcnow()
    assert workflow_ctx.execution.inputs == dict()


def test_execution_inputs_override_workflow_inputs(request):
    wf_inputs = {'input1': 'value1', 'input2': 'value2', 'input3': 5}
    mock_workflow = _setup_mock_workflow_in_service(
        request,
        inputs=dict((name, models.Input.wrap(name, val)) for name, val
                    in wf_inputs.iteritems()))

    workflow_ctx = _get_preparer(request, mock_workflow).prepare(
        execution_inputs={'input2': 'overriding-value2', 'input3': 7}
    )

    assert len(workflow_ctx.execution.inputs) == 3
    # did not override input1 - expecting the default value from the workflow inputs
    assert workflow_ctx.execution.inputs['input1'].value == 'value1'
    # overrode input2
    assert workflow_ctx.execution.inputs['input2'].value == 'overriding-value2'
    # overrode input of integer type
    assert workflow_ctx.execution.inputs['input3'].value == 7


def test_execution_inputs_undeclared_inputs(request):
    mock_workflow = _setup_mock_workflow_in_service(request)

    with pytest.raises(modeling_exceptions.UndeclaredInputsException):
        _get_preparer(request, mock_workflow).prepare(
            execution_inputs={'undeclared_input': 'value'})


def test_execution_inputs_missing_required_inputs(request):
    mock_workflow = _setup_mock_workflow_in_service(
        request, inputs={'required_input': models.Input.wrap('required_input', value=None)})

    with pytest.raises(modeling_exceptions.MissingRequiredInputsException):
        _get_preparer(request, mock_workflow).prepare(execution_inputs={})


def test_execution_inputs_wrong_type_inputs(request):
    mock_workflow = _setup_mock_workflow_in_service(
        request, inputs={'input': models.Input.wrap('input', 'value')})

    with pytest.raises(modeling_exceptions.ParametersOfWrongTypeException):
        _get_preparer(request, mock_workflow).prepare(execution_inputs={'input': 5})


def test_execution_inputs_builtin_workflow_with_inputs(request):
    # built-in workflows don't have inputs
    with pytest.raises(modeling_exceptions.UndeclaredInputsException):
        _get_preparer(request, 'install').prepare(execution_inputs={'undeclared_input': 'value'})


def test_workflow_function_parameters(request, tmpdir):
    # validating the workflow function is passed with the
    # merged execution inputs, in dict form

    # the workflow function parameters will be written to this file
    output_path = str(tmpdir.join('output'))
    wf_inputs = {'output_path': output_path, 'input1': 'value1', 'input2': 'value2', 'input3': 5}

    mock_workflow = _setup_mock_workflow_in_service(
        request, inputs=dict((name, models.Input.wrap(name, val)) for name, val
                             in wf_inputs.iteritems()))

    _get_preparer(request, mock_workflow).prepare(
        execution_inputs={'input2': 'overriding-value2', 'input3': 7})

    with open(output_path) as f:
        wf_call_kwargs = json.load(f)
    assert len(wf_call_kwargs) == 3
    assert wf_call_kwargs.get('input1') == 'value1'
    assert wf_call_kwargs.get('input2') == 'overriding-value2'
    assert wf_call_kwargs.get('input3') == 7


@pytest.fixture
def service(model):
    # sets up a service in the storage
    service_id = tests_mock.topology.create_simple_topology_two_nodes(model)
    service = model.service.get(service_id)
    return service


def _setup_mock_workflow_in_service(request, inputs=None):
    # sets up a mock workflow as part of the service, including uploading
    # the workflow code to the service's dir on the resource storage
    service = request.getfixturevalue('service')
    resource = request.getfixturevalue('resource')

    source = tests_mock.workflow.__file__
    resource.service_template.upload(str(service.service_template.id), source)
    mock_workflow_name = 'test_workflow'
    arguments = {}
    if inputs:
        for input in inputs.itervalues():
            arguments[input.name] = input.as_argument()
    workflow = models.Operation(
        name=mock_workflow_name,
        service=service,
        function='workflow.mock_workflow',
        inputs=inputs or {},
        arguments=arguments)
    service.workflows[mock_workflow_name] = workflow
    return mock_workflow_name


def _get_preparer(request, workflow_name):
    # helper method for instantiating a workflow runner
    service = request.getfixturevalue('service')
    model = request.getfixturevalue('model')
    resource = request.getfixturevalue('resource')
    plugin_manager = request.getfixturevalue('plugin_manager')

    return execution_preparer.ExecutionPreparer(
        model,
        resource,
        plugin_manager,
        service,
        workflow_name
    )


class TestResumableWorkflows(object):

    def _prepare_execution_and_get_workflow_ctx(
            self,
            model,
            resource,
            service,
            workflow,
            executor,
            inputs=None):

        service.workflows['custom_workflow'] = tests_mock.models.create_operation(
            'custom_workflow',
            operation_kwargs={
                'function': '{0}.{1}'.format(__name__, workflow.__name__),
                'inputs': dict((k, models.Input.wrap(k, v)) for k, v in (inputs or {}).items())
            }
        )
        model.service.update(service)
        compiler = execution_preparer.ExecutionPreparer(
            model, resource, None, service, 'custom_workflow'
        )
        ctx = compiler.prepare(inputs, executor)
        model.execution.update(ctx.execution)

        return ctx

    @staticmethod
    def _cancel_active_execution(eng, ctx):
        if custom_events['is_active'].wait(60) is False:
            raise TimeoutError("is_active wasn't set to True")
        eng.cancel_execution(ctx)
        if custom_events['execution_cancelled'].wait(60) is False:
            raise TimeoutError("Execution did not end")

    def test_resume_workflow(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_pass_first_task_only)
        ctx = self._prepare_execution_and_get_workflow_ctx(
            workflow_context.model,
            workflow_context.resource,
            workflow_context.model.service.list()[0],
            mock_parallel_tasks_workflow,
            thread_executor,
            inputs={'number_of_tasks': 2}
        )

        eng = engine.Engine(thread_executor)

        wf_thread = Thread(target=eng.execute, kwargs=dict(ctx=ctx))
        wf_thread.daemon = True
        wf_thread.start()

        # Wait for the execution to start
        self._cancel_active_execution(eng, ctx)
        node = ctx.model.node.refresh(node)

        tasks = ctx.model.task.list(filters={'_stub_type': None})
        assert any(task.status == task.SUCCESS for task in tasks)
        assert any(task.status == task.RETRYING for task in tasks)
        custom_events['is_resumed'].set()
        assert any(task.status == task.RETRYING for task in tasks)

        # Create a new workflow engine, with an existing execution id. This would cause
        # the old execution to restart.
        new_engine = engine.Engine(thread_executor)
        new_engine.execute(ctx, resuming=True)

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert all(task.status == task.SUCCESS for task in tasks)
        assert node.attributes['invocations'].value == 3
        assert ctx.execution.status == ctx.execution.SUCCEEDED

    def test_resume_started_task(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_stuck_task)

        ctx = self._prepare_execution_and_get_workflow_ctx(
            workflow_context.model,
            workflow_context.resource,
            workflow_context.model.service.list()[0],
            mock_parallel_tasks_workflow,
            thread_executor,
            inputs={'number_of_tasks': 1}
        )

        eng = engine.Engine(thread_executor)
        wf_thread = Thread(target=eng.execute, kwargs=dict(ctx=ctx))
        wf_thread.daemon = True
        wf_thread.start()

        self._cancel_active_execution(eng, ctx)
        node = workflow_context.model.node.refresh(node)
        task = workflow_context.model.task.list(filters={'_stub_type': None})[0]
        assert node.attributes['invocations'].value == 1
        assert task.status == task.STARTED
        assert ctx.execution.status in (ctx.execution.CANCELLED, ctx.execution.CANCELLING)
        custom_events['is_resumed'].set()

        new_thread_executor = thread.ThreadExecutor()
        try:
            new_engine = engine.Engine(new_thread_executor)
            new_engine.execute(ctx, resuming=True)
        finally:
            new_thread_executor.close()

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert node.attributes['invocations'].value == 2
        assert task.status == task.SUCCESS
        assert ctx.execution.status == ctx.execution.SUCCEEDED

    def test_resume_failed_task(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_failed_before_resuming)

        ctx = self._prepare_execution_and_get_workflow_ctx(
            workflow_context.model,
            workflow_context.resource,
            workflow_context.model.service.list()[0],
            mock_parallel_tasks_workflow,
            thread_executor)

        eng = engine.Engine(thread_executor)
        wf_thread = Thread(target=eng.execute, kwargs=dict(ctx=ctx))
        wf_thread.setDaemon(True)
        wf_thread.start()

        self._cancel_active_execution(eng, ctx)
        node = workflow_context.model.node.refresh(node)

        task = workflow_context.model.task.list(filters={'_stub_type': None})[0]
        assert node.attributes['invocations'].value == 2
        assert task.status == task.STARTED
        assert ctx.execution.status in (ctx.execution.CANCELLED, ctx.execution.CANCELLING)

        custom_events['is_resumed'].set()
        assert node.attributes['invocations'].value == 2

        # Create a new workflow runner, with an existing execution id. This would cause
        # the old execution to restart.
        new_thread_executor = thread.ThreadExecutor()
        try:
            new_engine = engine.Engine(new_thread_executor)
            new_engine.execute(ctx, resuming=True)
        finally:
            new_thread_executor.close()

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert node.attributes['invocations'].value == task.max_attempts - 1
        assert task.status == task.SUCCESS
        assert ctx.execution.status == ctx.execution.SUCCEEDED

    def test_resume_failed_task_and_successful_task(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_pass_first_task_only)

        ctx = self._prepare_execution_and_get_workflow_ctx(
            workflow_context.model,
            workflow_context.resource,
            workflow_context.model.service.list()[0],
            mock_parallel_tasks_workflow,
            thread_executor,
            inputs={'retry_interval': 1, 'max_attempts': 2, 'number_of_tasks': 2}
        )
        eng = engine.Engine(thread_executor)
        wf_thread = Thread(target=eng.execute, kwargs=dict(ctx=ctx))
        wf_thread.setDaemon(True)
        wf_thread.start()

        if custom_events['execution_failed'].wait(60) is False:
            raise TimeoutError("Execution did not end")

        tasks = workflow_context.model.task.list(filters={'_stub_type': None})
        node = workflow_context.model.node.refresh(node)
        assert node.attributes['invocations'].value == 3
        failed_task = [t for t in tasks if t.status == t.FAILED][0]

        # First task passes
        assert any(task.status == task.FAILED for task in tasks)
        assert failed_task.attempts_count == 2
        # Second task fails
        assert any(task.status == task.SUCCESS for task in tasks)
        assert ctx.execution.status in ctx.execution.FAILED

        custom_events['is_resumed'].set()
        new_thread_executor = thread.ThreadExecutor()
        try:
            new_engine = engine.Engine(new_thread_executor)
            new_engine.execute(ctx, resuming=True, retry_failed=True)
        finally:
            new_thread_executor.close()

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert failed_task.attempts_count == 1
        assert node.attributes['invocations'].value == 4
        assert all(task.status == task.SUCCESS for task in tasks)
        assert ctx.execution.status == ctx.execution.SUCCEEDED

    def test_two_sequential_task_first_task_failed(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_fail_first_task_only)

        ctx = self._prepare_execution_and_get_workflow_ctx(
            workflow_context.model,
            workflow_context.resource,
            workflow_context.model.service.list()[0],
            mock_sequential_tasks_workflow,
            thread_executor,
            inputs={'retry_interval': 1, 'max_attempts': 1, 'number_of_tasks': 2}
        )
        eng = engine.Engine(thread_executor)
        wf_thread = Thread(target=eng.execute, kwargs=dict(ctx=ctx))
        wf_thread.setDaemon(True)
        wf_thread.start()

        if custom_events['execution_failed'].wait(60) is False:
            raise TimeoutError("Execution did not end")

        tasks = workflow_context.model.task.list(filters={'_stub_type': None})
        node = workflow_context.model.node.refresh(node)
        assert node.attributes['invocations'].value == 1
        assert any(t.status == t.FAILED for t in tasks)
        assert any(t.status == t.PENDING for t in tasks)

        custom_events['is_resumed'].set()
        new_thread_executor = thread.ThreadExecutor()
        try:
            new_engine = engine.Engine(new_thread_executor)
            new_engine.execute(ctx, resuming=True)
        finally:
            new_thread_executor.close()

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert node.attributes['invocations'].value == 2
        assert any(t.status == t.SUCCESS for t in tasks)
        assert any(t.status == t.FAILED for t in tasks)
        assert ctx.execution.status == ctx.execution.SUCCEEDED

    @staticmethod
    @pytest.fixture
    def thread_executor():
        result = thread.ThreadExecutor()
        try:
            yield result
        finally:
            result.close()

    @staticmethod
    @pytest.fixture
    def workflow_context(tmpdir):
        workflow_context = tests_mock.context.simple(str(tmpdir))
        yield workflow_context
        storage.release_sqlite_storage(workflow_context.model)

    @staticmethod
    def _create_interface(ctx, node, func, arguments=None):
        interface_name = 'aria.interfaces.lifecycle'
        operation_kwargs = dict(function='{name}.{func.__name__}'.format(
            name=__name__, func=func))
        if arguments:
            # the operation has to declare the arguments before those may be passed
            operation_kwargs['arguments'] = arguments
        operation_name = 'create'
        interface = tests_mock.models.create_interface(node.service, interface_name, operation_name,
                                                       operation_kwargs=operation_kwargs)
        node.interfaces[interface.name] = interface
        ctx.model.node.update(node)

        return node, interface_name, operation_name

    @staticmethod
    def _engine(workflow_func, workflow_context, executor):
        graph = workflow_func(ctx=workflow_context)
        execution = workflow_context.execution
        graph_compiler.GraphCompiler(workflow_context, executor.__class__).compile(graph)
        workflow_context.execution = execution

        return engine.Engine(executor)

    @pytest.fixture(autouse=True)
    def register_to_events(self):
        def execution_cancelled(*args, **kwargs):
            custom_events['execution_cancelled'].set()

        def execution_failed(*args, **kwargs):
            custom_events['execution_failed'].set()

        events.on_cancelled_workflow_signal.connect(execution_cancelled)
        events.on_failure_workflow_signal.connect(execution_failed)
        yield
        events.on_cancelled_workflow_signal.disconnect(execution_cancelled)
        events.on_failure_workflow_signal.disconnect(execution_failed)
        for event in custom_events.values():
            event.clear()


@workflow
def mock_sequential_tasks_workflow(ctx, graph,
                                   retry_interval=1, max_attempts=10, number_of_tasks=1):
    node = ctx.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
    graph.sequence(*_create_tasks(node, retry_interval, max_attempts, number_of_tasks))


@workflow
def mock_parallel_tasks_workflow(ctx, graph,
                                 retry_interval=1, max_attempts=10, number_of_tasks=1):
    node = ctx.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
    graph.add_tasks(*_create_tasks(node, retry_interval, max_attempts, number_of_tasks))


def _create_tasks(node, retry_interval, max_attempts, number_of_tasks):
    return [
        api.task.OperationTask(node,
                               'aria.interfaces.lifecycle',
                               'create',
                               retry_interval=retry_interval,
                               max_attempts=max_attempts)
        for _ in xrange(number_of_tasks)
    ]


@operation
def mock_failed_before_resuming(ctx):
    """
    The task should run atmost ctx.task.max_attempts - 1 times, and only then pass.
    overall, the number of invocations should be ctx.task.max_attempts - 1
    """
    ctx.node.attributes['invocations'] += 1

    if ctx.node.attributes['invocations'] == 2:
        custom_events['is_active'].set()
        # unfreeze the thread only when all of the invocations are done
        while ctx.node.attributes['invocations'] < ctx.task.max_attempts - 1:
            time.sleep(5)

    elif ctx.node.attributes['invocations'] == ctx.task.max_attempts - 1:
        # pass only just before the end.
        return
    else:
        # fail o.w.
        raise FailingTask("stop this task")


@operation
def mock_stuck_task(ctx):
    ctx.node.attributes['invocations'] += 1
    while not custom_events['is_resumed'].isSet():
        if not custom_events['is_active'].isSet():
            custom_events['is_active'].set()
        time.sleep(5)


@operation
def mock_pass_first_task_only(ctx):
    ctx.node.attributes['invocations'] += 1

    if ctx.node.attributes['invocations'] != 1:
        custom_events['is_active'].set()
        if not custom_events['is_resumed'].isSet():
            # if resume was called, increase by one. o/w fail the execution - second task should
            # fail as long it was not a part of resuming the workflow
            raise FailingTask("wasn't resumed yet")


@operation
def mock_fail_first_task_only(ctx):
    ctx.node.attributes['invocations'] += 1

    if not custom_events['is_resumed'].isSet() and ctx.node.attributes['invocations'] == 1:
        raise FailingTask("First task should fail")
