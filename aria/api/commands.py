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
ARIA commands implementation. Each command represents one action and may be reused.
"""

import os
import sys

from importlib import import_module

from .. import extension
from ..orchestrator import WORKFLOW_DECORATOR_RESERVED_ARGUMENTS
from ..orchestrator.runner import Runner
from ..orchestrator.workflows.builtin import BUILTIN_WORKFLOWS
from ..packager import csar
from ..parser import specification
from ..parser.consumption import (
    ConsumptionContextBuilder,
    ConsumerChainBuilder
)
from ..parser.inputs import InputsParser
from ..parser.modeling import initialize_storage
from ..utils.application import StorageManager
from ..utils.caching import cachedmethod
from ..utils.collections import OrderedDict
from ..utils.imports import (import_fullname, import_modules)
from .components import Command


class ParseCommand(Command):
    """
    :code:`parse` command.

    Given a blueprint, emits information in human-readable, JSON or YAML format from various phases
    of the ARIA parser.
    """

    class InputData(Command.InputData):

        MANDATORY_FIELDS = []

        OPTIONAL_FIELDS = [
            'reader_source',
            'verbosity',
            'presenter_source',
            'uri',
            'literal_location',
            'presenter',
            'prefix',
            'debug',
            'cached_methods',
            'consumer',
            'loader_source',
            'inputs'
        ]

        def __init__(self, data, unknown_data=[]):
            super(ParseCommand.InputData, self).__init__(data, unknown_data)

    @classmethod
    def name(cls):
        return "parse"

    @staticmethod
    def _configure(command_data):
        if command_data.prefix:
            for prefix in command_data.prefix:
                extension.parser.uri_loader_prefix().append(prefix)

        cachedmethod.ENABLED = command_data.cached_methods

    def execute(self, command_data):
        ParseCommand._configure(command_data)
        command_data.inputs = InputsParser.as_dict(command_data.inputs, self.logger)

        context = ConsumptionContextBuilder(*command_data.unknown_data,
                                            out=self.receiver,
                                            **vars(command_data)).build()

        consumer = ConsumerChainBuilder(command_data.consumer).build(context)
        consumer.consume()

        if not context.validation.dump_issues():
            consumer.dump()


class WorkflowCommand(Command):
    """
    :code:`workflow` command.
    """

    WORKFLOW_POLICY_INTERNAL_PROPERTIES = ('function', 'implementation', 'dependencies')

    class InputData(Command.InputData):

        MANDATORY_FIELDS = [
            'uri',
            'workflow'
        ]

        OPTIONAL_FIELDS = [
            'deployment_id'
        ]

        def __init__(self, data, unknown_data=[]):
            super(WorkflowCommand.InputData, self).__init__(data, unknown_data)

    @classmethod
    def name(cls):
        return "workflow"

    @staticmethod
    def _configure(command_data):
        if command_data.prefix:
            for prefix in command_data.prefix:
                extension.parser.uri_loader_prefix().append(prefix)

        cachedmethod.ENABLED = command_data.cached_methods

    def execute(self, command_data):
        deployment_id = command_data.deployment_id or 1
        context = self._parse(command_data.uri)
        workflow_fn, inputs = self._get_workflow(context, command_data.workflow)
        self._run(context, command_data.workflow, workflow_fn, inputs, deployment_id)

    def _parse(self, uri):
        context = ConsumptionContextBuilder(uri=uri).build()
        consumer = ConsumerChainBuilder().build(context)
        consumer.consume()

        if context.validation.dump_issues():
            exit(1)

        return context

    def _get_workflow(self, context, workflow_name):
        if workflow_name in BUILTIN_WORKFLOWS:
            workflow_fn = import_fullname('aria.orchestrator.workflows.builtin.%s' % workflow_name)
            inputs = {}
        else:
            try:
                policy = context.modeling.instance.policies[workflow_name]
            except KeyError:
                raise AttributeError('workflow policy does not exist: "%s"' % workflow_name)
            if context.modeling.policy_types.get_role(policy.type_name) != 'workflow':
                raise AttributeError('policy is not a workflow: "%s"' % workflow_name)

            try:
                sys.path.append(policy.properties['implementation'].value)
            except KeyError:
                pass

            workflow_fn = import_fullname(policy.properties['function'].value)

            for k in policy.properties:
                if k in WORKFLOW_DECORATOR_RESERVED_ARGUMENTS:
                    raise AttributeError('workflow policy "%s" defines a reserved property: "%s"' %
                                         (workflow_name, k))

            inputs = OrderedDict([
                (k, v.value) for k, v in policy.properties.iteritems()
                if k not in WorkflowCommand.WORKFLOW_POLICY_INTERNAL_PROPERTIES
            ])

        return workflow_fn, inputs

    def _run(self, context, workflow_name, workflow_fn, inputs, deployment_id):
        # Storage
        def _initialize_storage(model_storage):
            initialize_storage(context, model_storage, deployment_id)

        # Create runner
        runner = Runner(workflow_name, workflow_fn, inputs, _initialize_storage, deployment_id)

        # Run
        runner.run()


class InitCommand(Command):
    """
    :code:`init` command.

    Broken. Currently maintained for reference.
    """

    class InputData(Command.InputData):

        MANDATORY_FIELDS = [
            'blueprint_id',
            'blueprint_path',
            'deployment_id'
        ]

        OPTIONAL_FIELDS = [
            'input',
            'verbosity'
        ]

        def __init__(self, data, unknown_data=[]):
            super(InitCommand.InputData, self).__init__(data, unknown_data)

    _IN_VIRTUAL_ENV = hasattr(sys, 'real_prefix')

    @classmethod
    def name(cls):
        return "init"

    def _workspace_setup(self):
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

    def _parse_blueprint(self, blueprint_path, inputs=None):
        # TODO
        return None, None

    @staticmethod
    def _create_storage(
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

    def execute(self, command_data):
        self._workspace_setup()

        inputs = \
            (InputsParser(self.logger).parse(command_data.input) if command_data.input else {})
        plan, deployment_plan = self._parse_blueprint(command_data.blueprint_path, inputs)

        self._create_storage(
            blueprint_plan=plan,
            blueprint_path=command_data.blueprint_path,
            deployment_plan=deployment_plan,
            blueprint_id=command_data.blueprint_id,
            deployment_id=command_data.deployment_id,
            main_file_name=os.path.basename(command_data.blueprint_path))

        self.logger.info('Initiated {0}'.format(command_data.blueprint_path))
        self.logger.info(
            'If you make changes to the blueprint, '
            'run `aria local init -p {0}` command again to apply them'.format(
                command_data.blueprint_path))


class ExecuteCommand(Command):
    """
    :code:`execute` command.

    Broken. Currently maintained for reference.
    """

    class InputData(Command.InputData):

        MANDATORY_FIELDS = [
            'deployment_id'
        ]

        OPTIONAL_FIELDS = [
            'deployment_id',
            'parameters',
            'task_retries',
            'task_retry_interval',
            'workflow_id',
            'verbosity'
        ]

        def __init__(self, data, unknown_data=[]):
            super(ExecuteCommand.InputData, self).__init__(data, unknown_data)

    @classmethod
    def name(cls):
        return "execute"

    @staticmethod
    def _merge_and_validate_execution_parameters(
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

    @staticmethod
    def _load_workflow_handler(handler_path):
        module_name, spec_handler_name = handler_path.rsplit('.', 1)
        try:
            module = import_module(module_name)
            return getattr(module, spec_handler_name)
        except ImportError:
            # TODO: exception handler
            raise
        except AttributeError:
            # TODO: exception handler
            raise

    def execute(self, command_data):
        parameters = (InputsParser(self.logger)
                      .parse(command_data.parameters)
                      if command_data.parameters
                      else {})

        resource_storage = application_resource_storage(
            FileSystemResourceDriver(local_resource_storage()))
        model_storage = application_model_storage(
            FileSystemModelDriver(local_model_storage()))
        deployment = model_storage.deployment.get(command_data.deployment_id)

        try:
            workflow = deployment.workflows[command_data.workflow_id]
        except KeyError:
            raise ValueError(
                '{0} workflow does not exist. existing workflows are: {1}'.format(
                    command_data.workflow_id,
                    deployment.workflows.keys()))

        workflow_parameters = self._merge_and_validate_execution_parameters(
            workflow,
            command_data.workflow_id,
            parameters
        )
        workflow_context = WorkflowContext(
            name=command_data.workflow_id,
            model_storage=model_storage,
            resource_storage=resource_storage,
            deployment_id=command_data.deployment_id,
            workflow_id=command_data.workflow_id,
            parameters=workflow_parameters,
        )
        workflow_function = self._load_workflow_handler(workflow['operation'])
        tasks_graph = workflow_function(workflow_context, **workflow_context.parameters)
        executor = ProcessExecutor()
        workflow_engine = Engine(executor=executor,
                                 workflow_context=workflow_context,
                                 tasks_graph=tasks_graph)
        workflow_engine.execute()
        executor.close()


class CSARCreateCommand(Command):
    """
    ``csar-create`` command implementation
    """

    class InputData(Command.InputData):

        MANDATORY_FIELDS = [
            'destination',
            'entry',
            'source'
        ]

        OPTIONAL_FIELDS = [
            'verbosity'
        ]

        def __init__(self, data, unknown_data=[]):
            super(CSARCreateCommand.InputData, self).__init__(data, unknown_data)

    @classmethod
    def name(cls):
        return "csar-create"

    def execute(self, command_data):
        csar.write(command_data.source, command_data.entry, command_data.destination, self.logger)
        csar.validate(command_data.destination, self.receiver, self.logger)


class CSAROpenCommand(Command):
    """
    ``csar-open`` command implementation
    """

    class InputData(Command.InputData):

        MANDATORY_FIELDS = [
            'destination',
            'source'
        ]

        OPTIONAL_FIELDS = [
            'verbosity'
        ]

        def __init__(self, data, unknown_data=[]):
            super(CSAROpenCommand.InputData, self).__init__(data, unknown_data)

    @classmethod
    def name(cls):
        return "csar-open"

    def execute(self, command_data):
        csar.read(command_data.source, command_data.destination, self.receiver, self.logger)


class CSARValidateCommand(Command):
    """
    ``csar-validate`` command implementation
    """

    class InputData(Command.InputData):

        MANDATORY_FIELDS = [
            'source'
        ]

        OPTIONAL_FIELDS = [
            'verbosity'
        ]

        def __init__(self, data, unknown_data=[]):
            super(CSARValidateCommand.InputData, self).__init__(data, unknown_data)

    @classmethod
    def name(cls):
        return "csar-validate"

    def execute(self, command_data):
        csar.validate(command_data.source, self.receiver, self.logger)


class SpecCommand(Command):
    """
    :code:`spec` command.

    Emits all uses of :code:`@dsl_specification` in the codebase, in human-readable or CSV format.
    """

    class InputData(Command.InputData):

        MANDATORY_FIELDS = []

        OPTIONAL_FIELDS = [
            'csv',
            'verbosity'
        ]

        def __init__(self, data, unknown_data=[]):
            super(SpecCommand.InputData, self).__init__(data, unknown_data)

    @classmethod
    def name(cls):
        return "spec"

    def execute(self, command_data):
        # Make sure that all @dsl_specification decorators are processed
        for pkg in extension.parser.specification_package():
            import_modules(pkg)

        # TODO: scan YAML documents as well

        if command_data.csv:
            specification.dump_as_csv(self.receiver)
        else:
            specification.dump(self.receiver.receive)
