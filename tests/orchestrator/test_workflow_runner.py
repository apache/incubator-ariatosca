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
from datetime import datetime

import pytest
import mock

from aria.modeling import exceptions as modeling_exceptions
from aria.modeling import models
from aria.orchestrator import exceptions
from aria.orchestrator.workflow_runner import WorkflowRunner
from aria.orchestrator.workflows.executor.process import ProcessExecutor

from ..mock import (
    topology,
    workflow as workflow_mocks
)
from ..fixtures import (  # pylint: disable=unused-import
    plugins_dir,
    plugin_manager,
    fs_model as model,
    resource_storage as resource
)


def test_undeclared_workflow(request):
    # validating a proper error is raised when the workflow is not declared in the service
    with pytest.raises(exceptions.UndeclaredWorkflowError):
        _create_workflow_runner(request, 'undeclared_workflow')


def test_missing_workflow_implementation(service, request):
    # validating a proper error is raised when the workflow code path does not exist
    workflow = models.Operation(
        name='test_workflow',
        service=service,
        implementation='nonexistent.workflow.implementation',
        inputs={})
    service.workflows['test_workflow'] = workflow

    with pytest.raises(exceptions.WorkflowImplementationNotFoundError):
        _create_workflow_runner(request, 'test_workflow')


def test_builtin_workflow_instantiation(request):
    # validates the workflow runner instantiates properly when provided with a builtin workflow
    # (expecting no errors to be raised on undeclared workflow or missing workflow implementation)
    workflow_runner = _create_workflow_runner(request, 'install')
    tasks = list(workflow_runner._tasks_graph.tasks)
    assert len(tasks) == 2  # expecting two WorkflowTasks


def test_custom_workflow_instantiation(request):
    # validates the workflow runner instantiates properly when provided with a custom workflow
    # (expecting no errors to be raised on undeclared workflow or missing workflow implementation)
    mock_workflow = _setup_mock_workflow_in_service(request)
    workflow_runner = _create_workflow_runner(request, mock_workflow)
    tasks = list(workflow_runner._tasks_graph.tasks)
    assert len(tasks) == 0  # mock workflow creates no tasks


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
        status=models.Execution.TERMINATED,
        workflow_name='uninstall')
    model.execution.put(existing_terminated_execution)
    # no active executions exist, so no error should be raised
    _create_workflow_runner(request, 'install')


def test_default_executor(request):
    # validates the ProcessExecutor is used by the workflow runner by default
    mock_workflow = _setup_mock_workflow_in_service(request)

    with mock.patch('aria.orchestrator.workflow_runner.Engine') as mock_engine_cls:
        _create_workflow_runner(request, mock_workflow)
        _, engine_kwargs = mock_engine_cls.call_args
        assert isinstance(engine_kwargs.get('executor'), ProcessExecutor)


def test_custom_executor(request):
    mock_workflow = _setup_mock_workflow_in_service(request)

    custom_executor = mock.MagicMock()
    with mock.patch('aria.orchestrator.workflow_runner.Engine') as mock_engine_cls:
        _create_workflow_runner(request, mock_workflow, executor=custom_executor)
        _, engine_kwargs = mock_engine_cls.call_args
        assert engine_kwargs.get('executor') == custom_executor


def test_task_configuration_parameters(request):
    mock_workflow = _setup_mock_workflow_in_service(request)

    task_max_attempts = 5
    task_retry_interval = 7
    with mock.patch('aria.orchestrator.workflow_runner.Engine') as mock_engine_cls:
        _create_workflow_runner(request, mock_workflow, task_max_attempts=task_max_attempts,
                                task_retry_interval=task_retry_interval)
        _, engine_kwargs = mock_engine_cls.call_args
        assert engine_kwargs['workflow_context']._task_max_attempts == task_max_attempts
        assert engine_kwargs['workflow_context']._task_retry_interval == task_retry_interval


def test_execute(request, service):
    mock_workflow = _setup_mock_workflow_in_service(request)

    mock_engine = mock.MagicMock()
    with mock.patch('aria.orchestrator.workflow_runner.Engine', return_value=mock_engine) \
            as mock_engine_cls:
        workflow_runner = _create_workflow_runner(request, mock_workflow)

        _, engine_kwargs = mock_engine_cls.call_args
        assert engine_kwargs['workflow_context'].service.id == service.id
        assert engine_kwargs['workflow_context'].execution.workflow_name == 'test_workflow'

        workflow_runner.execute()
        mock_engine.execute.assert_called_once_with()


def test_cancel_execution(request):
    mock_workflow = _setup_mock_workflow_in_service(request)

    mock_engine = mock.MagicMock()
    with mock.patch('aria.orchestrator.workflow_runner.Engine', return_value=mock_engine):
        workflow_runner = _create_workflow_runner(request, mock_workflow)
        workflow_runner.cancel()
        mock_engine.cancel_execution.assert_called_once_with()


def test_execution_model_creation(request, service, model):
    mock_workflow = _setup_mock_workflow_in_service(request)

    with mock.patch('aria.orchestrator.workflow_runner.Engine') as mock_engine_cls:
        workflow_runner = _create_workflow_runner(request, mock_workflow)

        _, engine_kwargs = mock_engine_cls.call_args
        assert engine_kwargs['workflow_context'].execution == workflow_runner.execution
        assert model.execution.get(workflow_runner.execution.id) == workflow_runner.execution
        assert workflow_runner.execution.service.id == service.id
        assert workflow_runner.execution.workflow_name == mock_workflow
        assert workflow_runner.execution.created_at <= datetime.utcnow()
        assert workflow_runner.execution.inputs == dict()


def test_execution_inputs_override_workflow_inputs(request):
    wf_inputs = {'input1': 'value1', 'input2': 'value2', 'input3': 5}
    mock_workflow = _setup_mock_workflow_in_service(
        request,
        inputs=dict((name, models.Parameter.wrap(name, val)) for name, val
                    in wf_inputs.iteritems()))

    with mock.patch('aria.orchestrator.workflow_runner.Engine'):
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
        request, inputs={'required_input': models.Parameter.wrap('required_input', value=None)})

    with pytest.raises(modeling_exceptions.MissingRequiredInputsException):
        _create_workflow_runner(request, mock_workflow, inputs={})


def test_execution_inputs_wrong_type_inputs(request):
    mock_workflow = _setup_mock_workflow_in_service(
        request, inputs={'input': models.Parameter.wrap('input', 'value')})

    with pytest.raises(modeling_exceptions.InputsOfWrongTypeException):
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
        request, inputs=dict((name, models.Parameter.wrap(name, val)) for name, val
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
    service_id = topology.create_simple_topology_two_nodes(model)
    service = model.service.get(service_id)
    return service


def _setup_mock_workflow_in_service(request, inputs=None):
    # sets up a mock workflow as part of the service, including uploading
    # the workflow code to the service's dir on the resource storage
    service = request.getfuncargvalue('service')
    resource = request.getfuncargvalue('resource')

    source = workflow_mocks.__file__
    resource.service_template.upload(str(service.service_template.id), source)
    mock_workflow_name = 'test_workflow'
    workflow = models.Operation(
        name=mock_workflow_name,
        service=service,
        implementation='workflow.mock_workflow',
        inputs=inputs or {})
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
