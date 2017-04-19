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
Workflow runner
"""

import os
import sys
from datetime import datetime

from . import exceptions
from .context.workflow import WorkflowContext
from .workflows import builtin
from .workflows.core.engine import Engine
from .workflows.executor.process import ProcessExecutor
from ..modeling import models
from ..modeling import utils as modeling_utils
from ..utils.imports import import_fullname


DEFAULT_TASK_MAX_ATTEMPTS = 30
DEFAULT_TASK_RETRY_INTERVAL = 30


class WorkflowRunner(object):

    def __init__(self, workflow_name, service_id, inputs,
                 model_storage, resource_storage, plugin_manager,
                 executor=None, task_max_attempts=DEFAULT_TASK_MAX_ATTEMPTS,
                 task_retry_interval=DEFAULT_TASK_RETRY_INTERVAL):
        """
        Manages a single workflow execution on a given service
        :param workflow_name: Workflow name
        :param service_id: Service id
        :param inputs: A key-value dict of inputs for the execution
        :param model_storage: Model storage
        :param resource_storage: Resource storage
        :param plugin_manager: Plugin manager
        :param executor: Executor for tasks. Defaults to a ProcessExecutor instance.
        :param task_max_attempts: Maximum attempts of repeating each failing task
        :param task_retry_interval: Retry interval in between retry attempts of a failing task
        """

        self._model_storage = model_storage
        self._resource_storage = resource_storage
        self._workflow_name = workflow_name

        # the IDs are stored rather than the models themselves, so this module could be used
        # by several threads without raising errors on model objects shared between threads
        self._service_id = service_id

        self._validate_workflow_exists_for_service()

        workflow_fn = self._get_workflow_fn()

        execution = self._create_execution_model(inputs)
        self._execution_id = execution.id

        workflow_context = WorkflowContext(
            name=self.__class__.__name__,
            model_storage=self._model_storage,
            resource_storage=resource_storage,
            service_id=service_id,
            execution_id=execution.id,
            workflow_name=workflow_name,
            task_max_attempts=task_max_attempts,
            task_retry_interval=task_retry_interval)

        # transforming the execution inputs to dict, to pass them to the workflow function
        execution_inputs_dict = dict(inp.unwrap() for inp in self.execution.inputs.values())
        self._tasks_graph = workflow_fn(ctx=workflow_context, **execution_inputs_dict)

        executor = executor or ProcessExecutor(plugin_manager=plugin_manager)
        self._engine = Engine(
            executor=executor,
            workflow_context=workflow_context,
            tasks_graph=self._tasks_graph)

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
        self._engine.execute()

    def cancel(self):
        self._engine.cancel_execution()

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

        execution.inputs = modeling_utils.create_inputs(inputs, workflow_inputs)
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
                "Can't start execution; Service {0} has an active execution with id {1}"
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
            workflow_fn = import_fullname(workflow.implementation)
        except ImportError:
            raise exceptions.WorkflowImplementationNotFoundError(
                'Could not find workflow {0} implementation at {1}'.format(
                    self._workflow_name, workflow.implementation))

        return workflow_fn
