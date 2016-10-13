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
import os
import sys
from glob import glob
from importlib import import_module

from yaml import safe_load, YAMLError

from aria import application_model_storage, application_resource_storage
from aria.logger import LoggerMixin
from aria.storage import FileSystemModelDriver, FileSystemResourceDriver
from aria.tools.application import StorageManager
from aria.contexts import WorkflowContext
from aria.workflows.core.engine import Engine
from aria.workflows.core.executor import ThreadExecutor

from .storage import (
    local_resource_storage,
    create_local_storage,
    local_model_storage,
    create_user_space,
    user_space,
    local_storage,
)

from .exceptions import (
    AriaCliFormatInputsError,
    AriaCliYAMLInputsError,
    AriaCliInvalidInputsError
)

#######################################
from dsl_parser.parser import parse_from_path
from dsl_parser.tasks import prepare_deployment_plan
#######################################


class BaseCommand(LoggerMixin):
    def __repr__(self):
        return 'AriaCli({cls.__name__})'.format(cls=self.__class__)

    def __call__(self, args_namespace):
        """
        __call__ method is called when running command
        :param args_namespace:
        """
        pass

    def parse_inputs(self, inputs):
        """
        Returns a dictionary of inputs `resources` can be:
        - A list of files.
        - A single file
        - A directory containing multiple input files
        - A key1=value1;key2=value2 pairs string.
        - Wildcard based string (e.g. *-inputs.yaml)
        """

        parsed_dict = {}

        def format_to_dict(input_string):
            self.logger.info('Processing inputs source: {0}'.format(input_string))
            try:
                input_string = input_string.strip()
                try:
                    parsed_dict.update(json.loads(input_string))
                except:
                    parsed_dict.update((input.split('=')
                                       for input in input_string.split(';')
                                       if input))
            except Exception as exc:
                raise AriaCliFormatInputsError(str(exc), inputs=input_string)

        def handle_inputs_source(input_path):
            self.logger.info('Processing inputs source: {0}'.format(input_path))
            try:
                with open(input_path) as input_file:
                    content = safe_load(input_file)
            except YAMLError as exc:
                raise AriaCliYAMLInputsError(
                    '"{0}" is not a valid YAML. {1}'.format(input_path, str(exc)))
            if isinstance(content, dict):
                parsed_dict.update(content)
                return
            if content is None:
                return
            raise AriaCliInvalidInputsError('Invalid inputs', inputs=input_path)

        for input_string in inputs if isinstance(inputs, list) else [inputs]:
            if os.path.isdir(input_string):
                for input_file in os.listdir(input_string):
                    handle_inputs_source(os.path.join(input_string, input_file))
                continue
            input_files = glob(input_string)
            if input_files:
                for input_file in input_files:
                    handle_inputs_source(input_file)
                continue
            format_to_dict(input_string)
        return parsed_dict


class InitCommand(BaseCommand):
    _IN_VIRTUAL_ENV = hasattr(sys, 'real_prefix')

    def __call__(self, args_namespace):
        super(InitCommand, self).__call__(args_namespace)
        self.workspace_setup()
        inputs = self.parse_inputs(args_namespace.input) if args_namespace.input else None
        plan, deployment_plan = self.parse_blueprint(args_namespace.blueprint_path, inputs)
        self.create_storage(
            blueprint_plan=plan,
            blueprint_path=args_namespace.blueprint_path,
            deployment_plan=deployment_plan,
            blueprint_id=args_namespace.blueprint_id,
            deployment_id=args_namespace.deployment_id,
            main_file_name=os.path.basename(args_namespace.blueprint_path))
        self.logger.info('Initiated {0}'.format(args_namespace.blueprint_path))
        self.logger.info(
            'If you make changes to the blueprint, '
            'run `aria local init` command again to apply them'.format(
                args_namespace.blueprint_path))

    def workspace_setup(self):
        try:
            create_user_space()
            self.logger.debug(
                'created user space path in: {0}'.format(user_space()))
        except IOError:
            self.logger.debug(
                'user space path already exist - {0}'.format(user_space()))
        try:
            create_local_storage()
            self.logger.debug(
                'created local storage path in: {0}'.format(local_storage()))
        except IOError:
            self.logger.debug(
                'local storage path already exist - {0}'.format(local_storage()))
        return local_storage()

    def parse_blueprint(self, blueprint_path, inputs=None):
        plan = parse_from_path(blueprint_path)
        self.logger.info('blueprint parsed successfully')
        deployment_plan = prepare_deployment_plan(plan=plan.copy(), inputs=inputs)
        return plan, deployment_plan

    def create_storage(
            self,
            blueprint_path,
            blueprint_plan,
            deployment_plan,
            blueprint_id,
            deployment_id,
            main_file_name=None):
        resource_storage = application_resource_storage(
            FileSystemResourceDriver(local_resource_storage()))
        model_storage = application_model_storage(
            FileSystemModelDriver(local_model_storage()))
        resource_storage.setup()
        model_storage.setup()
        storage_manager = StorageManager(
            model_storage=model_storage,
            resource_storage=resource_storage,
            blueprint_path=blueprint_path,
            blueprint_id=blueprint_id,
            blueprint_plan=blueprint_plan,
            deployment_id=deployment_id,
            deployment_plan=deployment_plan
        )
        storage_manager.create_blueprint_storage(
            blueprint_path,
            main_file_name=main_file_name
        )
        storage_manager.create_nodes_storage()
        storage_manager.create_deployment_storage()
        storage_manager.create_node_instances_storage()


class ExecuteCommand(BaseCommand):
    def __call__(self, args_namespace):
        super(ExecuteCommand, self).__call__(args_namespace)
        parameters = (self.parse_inputs(args_namespace.parameters)
                      if args_namespace.parameters else {})
        resource_storage = application_resource_storage(
            FileSystemResourceDriver(local_resource_storage()))
        model_storage = application_model_storage(
            FileSystemModelDriver(local_model_storage()))
        deployment = model_storage.deployment.get(args_namespace.deployment_id)

        try:
            workflow = deployment.workflows[args_namespace.workflow_id]
        except KeyError:
            raise ValueError(
                '{0} workflow does not exist. existing workflows are: {1}'.format(
                    args_namespace.workflow_id,
                    deployment.workflows.keys()))

        workflow_parameters = self._merge_and_validate_execution_parameters(
            workflow,
            args_namespace.workflow_id,
            parameters
        )
        workflow_context = WorkflowContext(
            name=args_namespace.workflow_id,
            model_storage=model_storage,
            resource_storage=resource_storage,
            deployment_id=args_namespace.deployment_id,
            workflow_id=args_namespace.workflow_id,
            parameters=workflow_parameters,
        )
        workflow_function = self._load_workflow_handler(workflow['operation'])
        tasks_graph = workflow_function(workflow_context, **workflow_context.parameters)
        executor = ThreadExecutor()
        workflow_engine = Engine(executor=executor,
                                 workflow_context=workflow_context,
                                 tasks_graph=tasks_graph)
        workflow_engine.execute()
        executor.close()

    def _merge_and_validate_execution_parameters(
            self,
            workflow,
            workflow_name,
            execution_parameters):
        merged_parameters = {}
        workflow_parameters = workflow.get('parameters', {})
        missing_mandatory_parameters = set()

        for name, param in workflow_parameters.iteritems():
            if 'default' not in param:
                if name not in execution_parameters:
                    missing_mandatory_parameters.add(name)
                    continue
                merged_parameters[name] = execution_parameters[name]
                continue
            merged_parameters[name] = (execution_parameters[name] if name in execution_parameters
                                       else param['default'])

        if missing_mandatory_parameters:
            raise ValueError(
                'Workflow "{0}" must be provided with the following '
                'parameters to execute: {1}'.format(
                    workflow_name, ','.join(missing_mandatory_parameters)))

        custom_parameters = dict(
            (k, v) for (k, v) in execution_parameters.iteritems()
            if k not in workflow_parameters)

        if custom_parameters:
            raise ValueError(
                'Workflow "{0}" does not have the following parameters declared: {1}. '
                'Remove these parameters'.format(
                    workflow_name, ','.join(custom_parameters.keys())))

        return merged_parameters

    def _load_workflow_handler(self, handler_path):
        module_name, spec_handler_name = handler_path.rsplit('.', 1)
        try:
            module = import_module(module_name)
            return getattr(module, spec_handler_name)
        except ImportError:
            # todo: exception handler
            raise
        except AttributeError:
            # todo: exception handler
            raise
