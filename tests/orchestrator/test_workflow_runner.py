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
from threading import Thread, Event
from datetime import datetime

import mock
import pytest

from aria.modeling import exceptions as modeling_exceptions
from aria.modeling import models
from aria.orchestrator import exceptions
from aria.orchestrator.events import on_cancelled_workflow_signal
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

events = {
    'is_resumed': Event(),
    'is_active': Event(),
    'execution_ended': Event()
}


class TimeoutError(BaseException):
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
                                                    resuming=False)


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

    with pytest.raises(modeling_exceptions.UndeclaredParametersException):
        _create_workflow_runner(request, mock_workflow, inputs={'undeclared_input': 'value'})


def test_execution_inputs_missing_required_inputs(request):
    mock_workflow = _setup_mock_workflow_in_service(
        request, inputs={'required_input': models.Input.wrap('required_input', value=None)})

    with pytest.raises(modeling_exceptions.MissingRequiredParametersException):
        _create_workflow_runner(request, mock_workflow, inputs={})


def test_execution_inputs_wrong_type_inputs(request):
    mock_workflow = _setup_mock_workflow_in_service(
        request, inputs={'input': models.Input.wrap('input', 'value')})

    with pytest.raises(modeling_exceptions.ParametersOfWrongTypeException):
        _create_workflow_runner(request, mock_workflow, inputs={'input': 5})


def test_execution_inputs_builtin_workflow_with_inputs(request):
    # built-in workflows don't have inputs
    with pytest.raises(modeling_exceptions.UndeclaredParametersException):
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
    service = request.getfuncargvalue('service')
    resource = request.getfuncargvalue('resource')

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
    service_id = request.getfuncargvalue('service').id
    model = request.getfuncargvalue('model')
    resource = request.getfuncargvalue('resource')
    plugin_manager = request.getfuncargvalue('plugin_manager')

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

    def test_resume_workflow(self, workflow_context, executor):
        node = workflow_context.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
        node.attributes['invocations'] = models.Attribute.wrap('invocations', 0)
        self._create_interface(workflow_context, node, mock_resuming_task)

        service = workflow_context.service
        service.workflows['custom_workflow'] = tests_mock.models.create_operation(
            'custom_workflow',
            operation_kwargs={'function': '{0}.{1}'.format(__name__, mock_workflow.__name__)}
        )
        workflow_context.model.service.update(service)

        wf_runner = WorkflowRunner(
            service_id=workflow_context.service.id,
            inputs={},
            model_storage=workflow_context.model,
            resource_storage=workflow_context.resource,
            plugin_manager=None,
            workflow_name='custom_workflow',
            executor=executor)
        wf_thread = Thread(target=wf_runner.execute)
        wf_thread.daemon = True
        wf_thread.start()

        # Wait for the execution to start
        if events['is_active'].wait(5) is False:
            raise TimeoutError("is_active wasn't set to True")
        wf_runner.cancel()

        if events['execution_ended'].wait(60) is False:
            raise TimeoutError("Execution did not end")

        tasks = workflow_context.model.task.list(filters={'_stub_type': None})
        assert any(task.status == task.SUCCESS for task in tasks)
        assert any(task.status in (task.FAILED, task.RETRYING) for task in tasks)
        events['is_resumed'].set()
        assert any(task.status in (task.FAILED, task.RETRYING) for task in tasks)

        # Create a new workflow runner, with an existing execution id. This would cause
        # the old execution to restart.
        new_wf_runner = WorkflowRunner(
            service_id=wf_runner.service.id,
            inputs={},
            model_storage=workflow_context.model,
            resource_storage=workflow_context.resource,
            plugin_manager=None,
            execution_id=wf_runner.execution.id,
            executor=executor)

        new_wf_runner.execute()

        # Wait for it to finish and assert changes.
        assert all(task.status == task.SUCCESS for task in tasks)
        assert node.attributes['invocations'].value == 3
        assert wf_runner.execution.status == wf_runner.execution.SUCCEEDED

    @staticmethod
    @pytest.fixture
    def executor():
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
        def execution_ended(*args, **kwargs):
            events['execution_ended'].set()

        on_cancelled_workflow_signal.connect(execution_ended)
        yield
        on_cancelled_workflow_signal.disconnect(execution_ended)


@workflow
def mock_workflow(ctx, graph):
    node = ctx.model.node.get_by_name(tests_mock.models.DEPENDENCY_NODE_NAME)
    graph.add_tasks(
        api.task.OperationTask(
            node, interface_name='aria.interfaces.lifecycle', operation_name='create'),
        api.task.OperationTask(
            node, interface_name='aria.interfaces.lifecycle', operation_name='create')
    )


@operation
def mock_resuming_task(ctx):
    ctx.node.attributes['invocations'] += 1

    if ctx.node.attributes['invocations'] != 1:
        events['is_active'].set()
        if not events['is_resumed'].isSet():
            # if resume was called, increase by one. o/w fail the execution - second task should
            # fail as long it was not a part of resuming the workflow
            raise BaseException("wasn't resumed yet")
