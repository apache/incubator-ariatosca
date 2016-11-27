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
CLI various commands implementation
"""

import json
import os
import sys
import csv
import shutil
import tempfile
from glob import glob
from importlib import import_module

from yaml import safe_load, YAMLError

from .. import extension
from .. import (application_model_storage, application_resource_storage)
from ..logger import LoggerMixin
from ..storage import (FileSystemModelDriver, FileSystemResourceDriver)
from ..orchestrator.context.workflow import WorkflowContext
from ..orchestrator.workflows.core.engine import Engine
from ..orchestrator.workflows.executor.process import ProcessExecutor
from ..parser import iter_specifications
from ..parser.consumption import (
    ConsumptionContext,
    ConsumerChain,
    Read,
    Validate,
    Model,
    Types,
    Inputs,
    Instance
)
from ..parser.loading import LiteralLocation, UriLocation
from ..utils.application import StorageManager
from ..utils.caching import cachedmethod
from ..utils.console import (puts, Colored, indent)
from ..utils.imports import (import_fullname, import_modules)
from . import csar
from .exceptions import (
    AriaCliFormatInputsError,
    AriaCliYAMLInputsError,
    AriaCliInvalidInputsError
)
from .storage import (
    local_resource_storage,
    create_local_storage,
    local_model_storage,
    create_user_space,
    user_space,
    local_storage,
)


class BaseCommand(LoggerMixin):
    """
    Base class for CLI commands
    """

    def __repr__(self):
        return 'AriaCli({cls.__name__})'.format(cls=self.__class__)

    def __call__(self, args_namespace, unknown_args):
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

        def _format_to_dict(input_string):
            self.logger.info('Processing inputs source: {0}'.format(input_string))
            try:
                input_string = input_string.strip()
                try:
                    parsed_dict.update(json.loads(input_string))
                except BaseException:
                    parsed_dict.update((input.split('=')
                                        for input in input_string.split(';')
                                        if input))
            except Exception as exc:
                raise AriaCliFormatInputsError(str(exc), inputs=input_string)

        def _handle_inputs_source(input_path):
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
                    _handle_inputs_source(os.path.join(input_string, input_file))
                continue
            input_files = glob(input_string)
            if input_files:
                for input_file in input_files:
                    _handle_inputs_source(input_file)
                continue
            _format_to_dict(input_string)
        return parsed_dict


class InitCommand(BaseCommand):
    """
    ``init`` command implementation
    """

    _IN_VIRTUAL_ENV = hasattr(sys, 'real_prefix')

    def __call__(self, args_namespace, unknown_args):
        super(InitCommand, self).__call__(args_namespace, unknown_args)
        self._workspace_setup()
        inputs = self.parse_inputs(args_namespace.input) if args_namespace.input else None
        plan, deployment_plan = self._parse_blueprint(args_namespace.blueprint_path, inputs)
        self._create_storage(
            blueprint_plan=plan,
            blueprint_path=args_namespace.blueprint_path,
            deployment_plan=deployment_plan,
            blueprint_id=args_namespace.blueprint_id,
            deployment_id=args_namespace.deployment_id,
            main_file_name=os.path.basename(args_namespace.blueprint_path))
        self.logger.info('Initiated {0}'.format(args_namespace.blueprint_path))
        self.logger.info(
            'If you make changes to the blueprint, '
            'run `aria local init -p {0}` command again to apply them'.format(
                args_namespace.blueprint_path))

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
        pass

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


class ExecuteCommand(BaseCommand):
    """
    ``execute`` command implementation
    """

    def __call__(self, args_namespace, unknown_args):
        super(ExecuteCommand, self).__call__(args_namespace, unknown_args)
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
        executor = ProcessExecutor()
        workflow_engine = Engine(executor=executor,
                                 workflow_context=workflow_context,
                                 tasks_graph=tasks_graph)
        workflow_engine.execute()
        executor.close()

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


class ParseCommand(BaseCommand):
    def __call__(self, args_namespace, unknown_args):
        super(ParseCommand, self).__call__(args_namespace, unknown_args)

        if args_namespace.prefix:
            for prefix in args_namespace.prefix:
                extension.parser.uri_loader_prefix().append(prefix)

        cachedmethod.ENABLED = args_namespace.cached_methods

        context = ParseCommand.create_context_from_namespace(args_namespace)
        context.args = unknown_args

        consumer = ConsumerChain(context, (Read, Validate))

        consumer_class_name = args_namespace.consumer
        dumper = None
        if consumer_class_name == 'presentation':
            dumper = consumer.consumers[0]
        elif consumer_class_name == 'model':
            consumer.append(Model)
        elif consumer_class_name == 'types':
            consumer.append(Model, Types)
        elif consumer_class_name == 'instance':
            consumer.append(Model, Inputs, Instance)
        else:
            consumer.append(Model, Inputs, Instance)
            consumer.append(import_fullname(consumer_class_name))

        if dumper is None:
            # Default to last consumer
            dumper = consumer.consumers[-1]

        consumer.consume()

        if not context.validation.dump_issues():
            dumper.dump()

    @staticmethod
    def create_context_from_namespace(namespace, **kwargs):
        args = vars(namespace).copy()
        args.update(kwargs)
        return ParseCommand.create_context(**args)

    @staticmethod
    def create_context(uri,
                       loader_source,
                       reader_source,
                       presenter_source,
                       presenter,
                       debug,
                       **kwargs):
        context = ConsumptionContext()
        context.loading.loader_source = import_fullname(loader_source)()
        context.reading.reader_source = import_fullname(reader_source)()
        context.presentation.location = UriLocation(uri) if isinstance(uri, basestring) else uri
        context.presentation.presenter_source = import_fullname(presenter_source)()
        context.presentation.presenter_class = import_fullname(presenter)
        context.presentation.print_exceptions = debug
        return context


class SpecCommand(BaseCommand):
    def __call__(self, args_namespace, unknown_args):
        super(SpecCommand, self).__call__(args_namespace, unknown_args)

        # Make sure that all @dsl_specification decorators are processed
        for pkg in extension.parser.specification_package():
            import_modules(pkg)

        # TODO: scan YAML documents as well

        if args_namespace.csv:
            writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
            writer.writerow(('Specification', 'Section', 'Code', 'URL'))
            for spec, sections in iter_specifications():
                for section, details in sections:
                    writer.writerow((spec, section, details['code'], details['url']))

        else:
            for spec, sections in iter_specifications():
                puts(Colored.cyan(spec))
                with indent(2):
                    for section, details in sections:
                        puts(Colored.blue(section))
                        with indent(2):
                            for k, v in details.iteritems():
                                puts('%s: %s' % (Colored.magenta(k), v))


class BaseCSARCommand(BaseCommand):

    @staticmethod
    def _parse_and_dump(reader):
        context = ConsumptionContext()
        context.loading.prefixes += [os.path.join(reader.destination, 'definitions')]
        context.presentation.location = LiteralLocation(reader.entry_definitions_yaml)
        chain = ConsumerChain(context, (Read, Validate, Model, Instance))
        chain.consume()
        if context.validation.dump_issues():
            raise RuntimeError('Validation failed')
        dumper = chain.consumers[-1]
        dumper.dump()

    def _read(self, source, destination):
        reader = csar.read(
            source=source,
            destination=destination,
            logger=self.logger)
        self.logger.info(
            'Path: {r.destination}\n'
            'TOSCA meta file version: {r.meta_file_version}\n'
            'CSAR Version: {r.csar_version}\n'
            'Created By: {r.created_by}\n'
            'Entry definitions: {r.entry_definitions}'
            .format(r=reader))
        self._parse_and_dump(reader)

    def _validate(self, source):
        workdir = tempfile.mkdtemp()
        try:
            self._read(
                source=source,
                destination=workdir)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)


class CSARCreateCommand(BaseCSARCommand):

    def __call__(self, args_namespace, unknown_args):
        super(CSARCreateCommand, self).__call__(args_namespace, unknown_args)
        csar.write(
            source=args_namespace.source,
            entry=args_namespace.entry,
            destination=args_namespace.destination,
            logger=self.logger)
        self._validate(args_namespace.destination)


class CSAROpenCommand(BaseCSARCommand):

    def __call__(self, args_namespace, unknown_args):
        super(CSAROpenCommand, self).__call__(args_namespace, unknown_args)
        self._read(
            source=args_namespace.source,
            destination=args_namespace.destination)


class CSARValidateCommand(BaseCSARCommand):

    def __call__(self, args_namespace, unknown_args):
        super(CSARValidateCommand, self).__call__(args_namespace, unknown_args)
        self._validate(args_namespace.source)
