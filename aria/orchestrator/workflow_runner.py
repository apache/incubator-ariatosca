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
Running workflows.
"""

import os
import sys
from datetime import datetime

from . import exceptions
from .context.workflow import WorkflowContext
from .workflows import builtin
from .workflows.core import engine, graph_compiler
from .workflows.executor.process import ProcessExecutor
from ..modeling import models
from ..modeling import utils as modeling_utils
from ..utils.imports import import_fullname


DEFAULT_TASK_MAX_ATTEMPTS = 30
DEFAULT_TASK_RETRY_INTERVAL = 30


class WorkflowRunner(object):

    def __init__(self, model_storage, resource_storage, plugin_manager,
                 execution_id=None, retry_failed_tasks=False,
                 service_id=None, workflow_name=None, inputs=None, executor=None,
                 task_max_attempts=DEFAULT_TASK_MAX_ATTEMPTS,
                 task_retry_interval=DEFAULT_TASK_RETRY_INTERVAL):
        """
        Manages a single workflow execution on a given service.

        :param workflow_name: workflow name
        :param service_id: service ID
        :param inputs: key-value dict of inputs for the execution
        :param model_storage: model storage API ("MAPI")
        :param resource_storage: resource storage API ("RAPI")
        :param plugin_manager: plugin manager
        :param executor: executor for tasks; defaults to a
         :class:`~aria.orchestrator.workflows.executor.process.ProcessExecutor` instance
        :param task_max_attempts: maximum attempts of repeating each failing task
        :param task_retry_interval: retry interval between retry attempts of a failing task
        """

        if not (execution_id or (workflow_name and service_id)):
            exceptions.InvalidWorkflowRunnerParams(
                "Either provide execution id in order to resume a workflow or workflow name "
                "and service id with inputs")

        self._is_resume = execution_id is not None
        self._retry_failed_tasks = retry_failed_tasks

        self._model_storage = model_storage
        self._resource_storage = resource_storage

        # the IDs are stored rather than the models themselves, so this module could be used
        # by several threads without raising errors on model objects shared between threads

        if self._is_resume:
            self._execution_id = execution_id
            self._service_id = self.execution.service.id
            self._workflow_name = model_storage.execution.get(self._execution_id).workflow_name
        else:
            self._service_id = service_id
            self._workflow_name = workflow_name
            self._validate_workflow_exists_for_service()
            self._execution_id = self._create_execution_model(inputs).id

        self._workflow_context = WorkflowContext(
            name=self.__class__.__name__,
            model_storage=self._model_storage,
            resource_storage=resource_storage,
            service_id=service_id,
            execution_id=self._execution_id,
            workflow_name=self._workflow_name,
            task_max_attempts=task_max_attempts,
            task_retry_interval=task_retry_interval)

        # Set default executor and kwargs
        executor = executor or ProcessExecutor(plugin_manager=plugin_manager)

        # transforming the execution inputs to dict, to pass them to the workflow function
        execution_inputs_dict = dict(inp.unwrapped for inp in self.execution.inputs.itervalues())

        if not self._is_resume:
            workflow_fn = self._get_workflow_fn()
            self._tasks_graph = workflow_fn(ctx=self._workflow_context, **execution_inputs_dict)
            compiler = graph_compiler.GraphCompiler(self._workflow_context, executor.__class__)
            compiler.compile(self._tasks_graph)

        self._engine = engine.Engine(executors={executor.__class__: executor})

    @property
    def execution_id(self):
        return self._execution_id

    @property
    def execution(self):
        return self._model_storage.execution.get(self.execution_id)

    @property
    def service(self):
        return self._model_storage.service.get(self._service_id)

    def execute(self):
        self._engine.execute(ctx=self._workflow_context,
                             resuming=self._is_resume,
                             retry_failed=self._retry_failed_tasks)

    def cancel(self):
        self._engine.cancel_execution(ctx=self._workflow_context)

    def _create_execution_model(self, inputs):
        execution = models.Execution(
            created_at=datetime.utcnow(),
            service=self.service,
            workflow_name=self._workflow_name,
            inputs={})

        if self._workflow_name in builtin.BUILTIN_WORKFLOWS:
            workflow_inputs = dict()  # built-in workflows don't have any inputs
        else:
            workflow_inputs = self.service.workflows[self._workflow_name].inputs

        modeling_utils.validate_no_undeclared_inputs(declared_inputs=workflow_inputs,
                                                     supplied_inputs=inputs or {})
        modeling_utils.validate_required_inputs_are_supplied(declared_inputs=workflow_inputs,
                                                             supplied_inputs=inputs or {})
        execution.inputs = modeling_utils.merge_parameter_values(inputs,
                                                                 workflow_inputs,
                                                                 model_cls=models.Input)
        # TODO: these two following calls should execute atomically
        self._validate_no_active_executions(execution)
        self._model_storage.execution.put(execution)
        return execution

    def _validate_workflow_exists_for_service(self):
        if self._workflow_name not in self.service.workflows and \
                        self._workflow_name not in builtin.BUILTIN_WORKFLOWS:
            raise exceptions.UndeclaredWorkflowError(
                'No workflow policy {0} declared in service {1}'
                .format(self._workflow_name, self.service.name))

    def _validate_no_active_executions(self, execution):
        active_executions = [e for e in self.service.executions if e.is_active()]
        if active_executions:
            raise exceptions.ActiveExecutionsError(
                "Can't start execution; Service {0} has an active execution with ID {1}"
                .format(self.service.name, active_executions[0].id))

    def _get_workflow_fn(self):
        if self._workflow_name in builtin.BUILTIN_WORKFLOWS:
            return import_fullname('{0}.{1}'.format(builtin.BUILTIN_WORKFLOWS_PATH_PREFIX,
                                                    self._workflow_name))

        workflow = self.service.workflows[self._workflow_name]

        # TODO: Custom workflow support needs improvement, currently this code uses internal
        # knowledge of the resource storage; Instead, workflows should probably be loaded
        # in a similar manner to operation plugins. Also consider passing to import_fullname
        # as paths instead of appending to sys path.
        service_template_resources_path = os.path.join(
            self._resource_storage.service_template.base_path,
            str(self.service.service_template.id))
        sys.path.append(service_template_resources_path)

        try:
            workflow_fn = import_fullname(workflow.function)
        except ImportError:
            raise exceptions.WorkflowImplementationNotFoundError(
                'Could not find workflow {0} function at {1}'.format(
                    self._workflow_name, workflow.function))

        return workflow_fn
