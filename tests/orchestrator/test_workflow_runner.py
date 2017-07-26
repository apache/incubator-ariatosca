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

import mock
import pytest

from aria.modeling import exceptions as modeling_exceptions
from aria.modeling import models
from aria.orchestrator import exceptions
from aria.orchestrator import events
from aria.orchestrator.workflow_runner import WorkflowRunner
from aria.orchestrator.workflows.executor.process import ProcessExecutor
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

from ..fixtures import (  # pylint: disable=unused-import
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
        _create_workflow_runner(request, 'undeclared_workflow')


def test_missing_workflow_implementation(service, request):
    # validating a proper error is raised when the workflow code path does not exist
    workflow = models.Operation(
        name='test_workflow',
        service=service,
        function='nonexistent.workflow.implementation')
    service.workflows['test_workflow'] = workflow

    with pytest.raises(exceptions.WorkflowImplementationNotFoundError):
        _create_workflow_runner(request, 'test_workflow')


def test_builtin_workflow_instantiation(request):
    # validates the workflow runner instantiates properly when provided with a builtin workflow
    # (expecting no errors to be raised on undeclared workflow or missing workflow implementation)
    workflow_runner = _create_workflow_runner(request, 'install')
    tasks = list(workflow_runner.execution.tasks)
    assert len(tasks) == 18  # expecting 18 tasks for 2 node topology


def test_custom_workflow_instantiation(request):
    # validates the workflow runner instantiates properly when provided with a custom workflow
    # (expecting no errors to be raised on undeclared workflow or missing workflow implementation)
    mock_workflow = _setup_mock_workflow_in_service(request)
    workflow_runner = _create_workflow_runner(request, mock_workflow)
    tasks = list(workflow_runner.execution.tasks)
    assert len(tasks) == 2  # mock workflow creates only start workflow and end workflow task


def test_existing_active_executions(request, service, model):
    existing_active_execution = models.Execution(
        service=service,
        status=models.Execution.STARTED,
        workflow_name='uninstall')
    model.execution.put(existing_active_execution)
    with pytest.raises(exceptions.ActiveExecutionsError):
        _create_workflow_runner(request, 'install')


def test_existing_executions_but_no_active_ones(request, service, model):
    existing_terminated_execution = models.Execution(
        service=service,
        status=models.Execution.SUCCEEDED,
        workflow_name='uninstall')
    model.execution.put(existing_terminated_execution)
    # no active executions exist, so no error should be raised
    _create_workflow_runner(request, 'install')


def test_default_executor(request):
    # validates the ProcessExecutor is used by the workflow runner by default
    mock_workflow = _setup_mock_workflow_in_service(request)

    with mock.patch('aria.orchestrator.workflow_runner.engine.Engine') as mock_engine_cls:
        _create_workflow_runner(request, mock_workflow)
        _, engine_kwargs = mock_engine_cls.call_args
        assert isinstance(engine_kwargs.get('executors').values()[0], ProcessExecutor)


def test_custom_executor(request):
    mock_workflow = _setup_mock_workflow_in_service(request)

    custom_executor = mock.MagicMock()
    with mock.patch('aria.orchestrator.workflow_runner.engine.Engine') as mock_engine_cls:
        _create_workflow_runner(request, mock_workflow, executor=custom_executor)
        _, engine_kwargs = mock_engine_cls.call_args
        assert engine_kwargs.get('executors').values()[0] == custom_executor


def test_task_configuration_parameters(request):
    mock_workflow = _setup_mock_workflow_in_service(request)

    task_max_attempts = 5
    task_retry_interval = 7
    with mock.patch('aria.orchestrator.workflow_runner.engine.Engine.execute') as \
            mock_engine_execute:
        _create_workflow_runner(request, mock_workflow, task_max_attempts=task_max_attempts,
                                task_retry_interval=task_retry_interval).execute()
        _, engine_kwargs = mock_engine_execute.call_args
        assert engine_kwargs['ctx']._task_max_attempts == task_max_attempts
        assert engine_kwargs['ctx']._task_retry_interval == task_retry_interval


def test_execute(request, service):
    mock_workflow = _setup_mock_workflow_in_service(request)

    mock_engine = mock.MagicMock()
    with mock.patch('aria.orchestrator.workflow_runner.engine.Engine.execute',
                    return_value=mock_engine) as mock_engine_execute:
        workflow_runner = _create_workflow_runner(request, mock_workflow)
        workflow_runner.execute()

        _, engine_kwargs = mock_engine_execute.call_args
        assert engine_kwargs['ctx'].service.id == service.id
        assert engine_kwargs['ctx'].execution.workflow_name == 'test_workflow'

        mock_engine_execute.assert_called_once_with(ctx=workflow_runner._workflow_context,
                                                    resuming=False,
                                                    retry_failed=False)


def test_cancel_execution(request):
    mock_workflow = _setup_mock_workflow_in_service(request)

    mock_engine = mock.MagicMock()
    with mock.patch('aria.orchestrator.workflow_runner.engine.Engine', return_value=mock_engine):
        workflow_runner = _create_workflow_runner(request, mock_workflow)
        workflow_runner.cancel()
        mock_engine.cancel_execution.assert_called_once_with(ctx=workflow_runner._workflow_context)


def test_execution_model_creation(request, service, model):
    mock_workflow = _setup_mock_workflow_in_service(request)

    with mock.patch('aria.orchestrator.workflow_runner.engine.Engine'):
        workflow_runner = _create_workflow_runner(request, mock_workflow)

        assert model.execution.get(workflow_runner.execution.id) == workflow_runner.execution
        assert workflow_runner.execution.service.id == service.id
        assert workflow_runner.execution.workflow_name == mock_workflow
        assert workflow_runner.execution.created_at <= datetime.utcnow()
        assert workflow_runner.execution.inputs == dict()


def test_execution_inputs_override_workflow_inputs(request):
    wf_inputs = {'input1': 'value1', 'input2': 'value2', 'input3': 5}
    mock_workflow = _setup_mock_workflow_in_service(
        request,
        inputs=dict((name, models.Input.wrap(name, val)) for name, val
                    in wf_inputs.iteritems()))

    with mock.patch('aria.orchestrator.workflow_runner.engine.Engine'):
        workflow_runner = _create_workflow_runner(
            request, mock_workflow, inputs={'input2': 'overriding-value2', 'input3': 7})

        assert len(workflow_runner.execution.inputs) == 3
        # did not override input1 - expecting the default value from the workflow inputs
        assert workflow_runner.execution.inputs['input1'].value == 'value1'
        # overrode input2
        assert workflow_runner.execution.inputs['input2'].value == 'overriding-value2'
        # overrode input of integer type
        assert workflow_runner.execution.inputs['input3'].value == 7


def test_execution_inputs_undeclared_inputs(request):
    mock_workflow = _setup_mock_workflow_in_service(request)

    with pytest.raises(modeling_exceptions.UndeclaredInputsException):
        _create_workflow_runner(request, mock_workflow, inputs={'undeclared_input': 'value'})


def test_execution_inputs_missing_required_inputs(request):
    mock_workflow = _setup_mock_workflow_in_service(
        request, inputs={'required_input': models.Input.wrap('required_input', value=None)})

    with pytest.raises(modeling_exceptions.MissingRequiredInputsException):
        _create_workflow_runner(request, mock_workflow, inputs={})


def test_execution_inputs_wrong_type_inputs(request):
    mock_workflow = _setup_mock_workflow_in_service(
        request, inputs={'input': models.Input.wrap('input', 'value')})

    with pytest.raises(modeling_exceptions.ParametersOfWrongTypeException):
        _create_workflow_runner(request, mock_workflow, inputs={'input': 5})


def test_execution_inputs_builtin_workflow_with_inputs(request):
    # built-in workflows don't have inputs
    with pytest.raises(modeling_exceptions.UndeclaredInputsException):
        _create_workflow_runner(request, 'install', inputs={'undeclared_input': 'value'})


def test_workflow_function_parameters(request, tmpdir):
    # validating the workflow function is passed with the
    # merged execution inputs, in dict form

    # the workflow function parameters will be written to this file
    output_path = str(tmpdir.join('output'))
    wf_inputs = {'output_path': output_path, 'input1': 'value1', 'input2': 'value2', 'input3': 5}

    mock_workflow = _setup_mock_workflow_in_service(
        request, inputs=dict((name, models.Input.wrap(name, val)) for name, val
                             in wf_inputs.iteritems()))

    _create_workflow_runner(request, mock_workflow,
                            inputs={'input2': 'overriding-value2', 'input3': 7})

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


def _create_workflow_runner(request, workflow_name, inputs=None, executor=None,
                            task_max_attempts=None, task_retry_interval=None):
    # helper method for instantiating a workflow runner
    service_id = request.getfixturevalue('service').id
    model = request.getfixturevalue('model')
    resource = request.getfixturevalue('resource')
    plugin_manager = request.getfixturevalue('plugin_manager')

    # task configuration parameters can't be set to None, therefore only
    # passing those if they've been set by the test
    task_configuration_kwargs = dict()
    if task_max_attempts is not None:
        task_configuration_kwargs['task_max_attempts'] = task_max_attempts
    if task_retry_interval is not None:
        task_configuration_kwargs['task_retry_interval'] = task_retry_interval

    return WorkflowRunner(
        workflow_name=workflow_name,
        service_id=service_id,
        inputs=inputs or {},
        executor=executor,
        model_storage=model,
        resource_storage=resource,
        plugin_manager=plugin_manager,
        **task_configuration_kwargs)


class TestResumableWorkflows(object):

    def _create_initial_workflow_runner(
            self, workflow_context, workflow, executor, inputs=None):

        service = workflow_context.service
        service.workflows['custom_workflow'] = tests_mock.models.create_operation(
            'custom_workflow',
            operation_kwargs={
                'function': '{0}.{1}'.format(__name__, workflow.__name__),
                'inputs': dict((k, models.Input.wrap(k, v)) for k, v in (inputs or {}).items())
            }
        )
        workflow_context.model.service.update(service)

        wf_runner = WorkflowRunner(
            service_id=workflow_context.service.id,
            inputs=inputs or {},
            model_storage=workflow_context.model,
            resource_storage=workflow_context.resource,
            plugin_manager=None,
            workflow_name='custom_workflow',
            executor=executor)
        return wf_runner

    @staticmethod
    def _wait_for_active_and_cancel(workflow_runner):
        if custom_events['is_active'].wait(60) is False:
            raise TimeoutError("is_active wasn't set to True")
        workflow_runner.cancel()
        if custom_events['execution_cancelled'].wait(60) is False:
            raise TimeoutError("Execution did not end")

    def test_resume_workflow(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_pass_first_task_only)

        wf_runner = self._create_initial_workflow_runner(
            workflow_context, mock_parallel_tasks_workflow, thread_executor,
            inputs={'number_of_tasks': 2})

        wf_thread = Thread(target=wf_runner.execute)
        wf_thread.daemon = True
        wf_thread.start()

        # Wait for the execution to start
        self._wait_for_active_and_cancel(wf_runner)
        node = workflow_context.model.node.refresh(node)

        tasks = workflow_context.model.task.list(filters={'_stub_type': None})
        assert any(task.status == task.SUCCESS for task in tasks)
        assert any(task.status == task.RETRYING for task in tasks)
        custom_events['is_resumed'].set()
        assert any(task.status == task.RETRYING for task in tasks)

        # Create a new workflow runner, with an existing execution id. This would cause
        # the old execution to restart.
        new_wf_runner = WorkflowRunner(
            service_id=wf_runner.service.id,
            inputs={},
            model_storage=workflow_context.model,
            resource_storage=workflow_context.resource,
            plugin_manager=None,
            execution_id=wf_runner.execution.id,
            executor=thread_executor)

        new_wf_runner.execute()

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert all(task.status == task.SUCCESS for task in tasks)
        assert node.attributes['invocations'].value == 3
        assert wf_runner.execution.status == wf_runner.execution.SUCCEEDED

    def test_resume_started_task(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_stuck_task)

        wf_runner = self._create_initial_workflow_runner(
            workflow_context, mock_parallel_tasks_workflow, thread_executor,
            inputs={'number_of_tasks': 1})

        wf_thread = Thread(target=wf_runner.execute)
        wf_thread.daemon = True
        wf_thread.start()

        self._wait_for_active_and_cancel(wf_runner)
        node = workflow_context.model.node.refresh(node)
        task = workflow_context.model.task.list(filters={'_stub_type': None})[0]
        assert node.attributes['invocations'].value == 1
        assert task.status == task.STARTED
        assert wf_runner.execution.status in (wf_runner.execution.CANCELLED,
                                              wf_runner.execution.CANCELLING)
        custom_events['is_resumed'].set()

        new_thread_executor = thread.ThreadExecutor()
        try:
            new_wf_runner = WorkflowRunner(
                service_id=wf_runner.service.id,
                inputs={},
                model_storage=workflow_context.model,
                resource_storage=workflow_context.resource,
                plugin_manager=None,
                execution_id=wf_runner.execution.id,
                executor=new_thread_executor)

            new_wf_runner.execute()
        finally:
            new_thread_executor.close()

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert node.attributes['invocations'].value == 2
        assert task.status == task.SUCCESS
        assert wf_runner.execution.status == wf_runner.execution.SUCCEEDED

    def test_resume_failed_task(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_failed_before_resuming)

        wf_runner = self._create_initial_workflow_runner(workflow_context,
                                                         mock_parallel_tasks_workflow,
                                                         thread_executor)
        wf_thread = Thread(target=wf_runner.execute)
        wf_thread.setDaemon(True)
        wf_thread.start()

        self._wait_for_active_and_cancel(wf_runner)
        node = workflow_context.model.node.refresh(node)

        task = workflow_context.model.task.list(filters={'_stub_type': None})[0]
        assert node.attributes['invocations'].value == 2
        assert task.status == task.STARTED
        assert wf_runner.execution.status in (wf_runner.execution.CANCELLED,
                                              wf_runner.execution.CANCELLING)

        custom_events['is_resumed'].set()
        assert node.attributes['invocations'].value == 2

        # Create a new workflow runner, with an existing execution id. This would cause
        # the old execution to restart.
        new_thread_executor = thread.ThreadExecutor()
        try:
            new_wf_runner = WorkflowRunner(
                service_id=wf_runner.service.id,
                inputs={},
                model_storage=workflow_context.model,
                resource_storage=workflow_context.resource,
                plugin_manager=None,
                execution_id=wf_runner.execution.id,
                executor=new_thread_executor)

            new_wf_runner.execute()
        finally:
            new_thread_executor.close()

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert node.attributes['invocations'].value == task.max_attempts - 1
        assert task.status == task.SUCCESS
        assert wf_runner.execution.status == wf_runner.execution.SUCCEEDED

    def test_resume_failed_task_and_successful_task(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_pass_first_task_only)

        wf_runner = self._create_initial_workflow_runner(
            workflow_context,
            mock_parallel_tasks_workflow,
            thread_executor,
            inputs={'retry_interval': 1, 'max_attempts': 2, 'number_of_tasks': 2}
        )
        wf_thread = Thread(target=wf_runner.execute)
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
        assert wf_runner.execution.status in wf_runner.execution.FAILED

        custom_events['is_resumed'].set()
        new_thread_executor = thread.ThreadExecutor()
        try:
            new_wf_runner = WorkflowRunner(
                service_id=wf_runner.service.id,
                retry_failed_tasks=True,
                inputs={},
                model_storage=workflow_context.model,
                resource_storage=workflow_context.resource,
                plugin_manager=None,
                execution_id=wf_runner.execution.id,
                executor=new_thread_executor)

            new_wf_runner.execute()
        finally:
            new_thread_executor.close()

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert failed_task.attempts_count == 1
        assert node.attributes['invocations'].value == 4
        assert all(task.status == task.SUCCESS for task in tasks)
        assert wf_runner.execution.status == wf_runner.execution.SUCCEEDED

    def test_two_sequential_task_first_task_failed(self, workflow_context, thread_executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_fail_first_task_only)

        wf_runner = self._create_initial_workflow_runner(
            workflow_context,
            mock_sequential_tasks_workflow,
            thread_executor,
            inputs={'retry_interval': 1, 'max_attempts': 1, 'number_of_tasks': 2}
        )
        wf_thread = Thread(target=wf_runner.execute)
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
            new_wf_runner = WorkflowRunner(
                service_id=wf_runner.service.id,
                inputs={},
                model_storage=workflow_context.model,
                resource_storage=workflow_context.resource,
                plugin_manager=None,
                execution_id=wf_runner.execution.id,
                executor=new_thread_executor)

            new_wf_runner.execute()
        finally:
            new_thread_executor.close()

        # Wait for it to finish and assert changes.
        node = workflow_context.model.node.refresh(node)
        assert node.attributes['invocations'].value == 2
        assert any(t.status == t.SUCCESS for t in tasks)
        assert any(t.status == t.FAILED for t in tasks)
        assert wf_runner.execution.status == wf_runner.execution.SUCCEEDED



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

        return engine.Engine(executors={executor.__class__: executor})

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
