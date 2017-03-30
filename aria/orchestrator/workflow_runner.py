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

import sys
from datetime import datetime

from .context.workflow import WorkflowContext
from .workflows.builtin import BUILTIN_WORKFLOWS, BUILTIN_WORKFLOWS_PATH_PREFIX
from .workflows.core.engine import Engine
from .workflows.executor.process import ProcessExecutor
from ..exceptions import AriaException
from ..modeling import utils as modeling_utils
from ..modeling import models
from ..utils.imports import import_fullname


DEFAULT_TASK_MAX_ATTEMPTS = 1
DEFAULT_TASK_RETRY_INTERVAL = 1
# TODO move this constant somewhere in the DSL parser
WORKFLOW_POLICY_INTERNAL_PROPERTIES = ('implementation', 'dependencies')


class WorkflowRunner(object):

    def __init__(self, workflow_name, service_name, inputs,
                 model_storage, resource_storage, plugin_manager,
                 task_max_attempts=DEFAULT_TASK_MAX_ATTEMPTS,
                 task_retry_interval=DEFAULT_TASK_RETRY_INTERVAL):

        self._model_storage = model_storage
        self._workflow_name = workflow_name
        service = model_storage.service.get_by_name(service_name)
        # the IDs are stored rather than the models themselves, so this module could be used
        # by several threads without raising errors on model objects shared between threads
        self._service_id = service.id

        self._validate_workflow_exists_for_service()

        workflow_fn = self._get_workflow_fn()

        execution = self._create_execution_models(inputs)
        self._execution_id = execution.id

        workflow_context = WorkflowContext(
            name=self.__class__.__name__,
            model_storage=self._model_storage,
            resource_storage=resource_storage,
            service_id=service.id,
            execution_id=execution.id,
            workflow_name=workflow_name,
            task_max_attempts=task_max_attempts,
            task_retry_interval=task_retry_interval)

        # merged_inputs_dict = {input.name: input.value for input in self.execution.inputs.values()}
        # self._tasks_graph = workflow_fn(ctx=workflow_context, **merged_inputs_dict)
        self._tasks_graph = workflow_fn(ctx=workflow_context)

        self._engine = Engine(
            executor=ProcessExecutor(plugin_manager=plugin_manager),
            workflow_context=workflow_context,
            tasks_graph=self._tasks_graph)

    @property
    def execution(self):
        return self._model_storage.execution.get(self._execution_id)

    @property
    def service(self):
        return self._model_storage.service.get(self._service_id)

    def execute(self):
        #TODO uncomment, commented for testing purposes
        # self._validate_no_active_executions()
        self._engine.execute()

    def cancel(self):
        self._engine.cancel_execution()

    def _create_execution_models(self, inputs):
        execution = models.Execution(
            created_at=datetime.utcnow(),
            service=self.service,
            workflow_name=self._workflow_name)

        # workflow_inputs = {k: v for k, v in
        #                    self.service.workflows[self._workflow_name].properties
        #                    if k not in WORKFLOW_POLICY_INTERNAL_PROPERTIES}

        # input_models = modeling_utils.create_inputs(inputs, workflow_inputs)
        # execution.parameters = input_models

        self._model_storage.execution.put(execution)
        return execution

    def _validate_workflow_exists_for_service(self):
        if self._workflow_name not in self.service.workflows and \
                        self._workflow_name not in BUILTIN_WORKFLOWS:
            raise AriaException('No workflow policy {0} declared in service instance {1}'
                                .format(self._workflow_name, self.service.name))

    def _validate_no_active_executions(self):
        active_executions_filter = dict(service=self.service,
                                        status=models.Execution.ACTIVE_STATES)
        active_executions = self._model_storage.execution.list(filter=active_executions_filter)
        if active_executions:
            raise AriaException("Can't start execution; Service {0} has a running "
                                "execution with id {1}"
                                .format(self.service.name, active_executions[0].id))

    def _get_workflow_fn(self):
        if self._workflow_name in BUILTIN_WORKFLOWS:
            return import_fullname('{0}.{1}'.format(BUILTIN_WORKFLOWS_PATH_PREFIX,
                                                    self._workflow_name))

        workflow = self.service.workflows[self._workflow_name]

        try:
            # TODO: perhaps pass to import_fullname as paths instead of appending to sys path?
            sys.path.append(workflow.properties['implementation'].value)
            # sys.path.append(os.path.dirname(str(context.presentation.location)))
        except KeyError:
            # no implementation field - a script has been provided directly
            pass

        workflow_fn = import_fullname(workflow.properties['implementation'].value)
        return workflow_fn
