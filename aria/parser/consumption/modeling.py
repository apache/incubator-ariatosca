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

from ...utils.formatting import json_dumps, yaml_dumps
from .consumer import Consumer, ConsumerChain


class DeriveServiceTemplate(Consumer):
    """
    Derives the service template from the presenter.
    """

    def consume(self):
        if self.context.presentation.presenter is None:
            self.context.validation.report('DeriveServiceTemplate consumer: missing presenter')
            return

        if not hasattr(self.context.presentation.presenter, '_get_model'):
            self.context.validation.report('DeriveServiceTemplate consumer: presenter does not'
                                           ' support "_get_model"')
            return

        self.context.modeling.template = \
            self.context.presentation.presenter._get_model(self.context)


class CoerceServiceTemplateValues(Consumer):
    """
    Coerces values in the service template.
    """

    def consume(self):
        self.context.modeling.template.coerce_values(None, True)


class ValidateServiceTemplate(Consumer):
    """
    Validates the service template.
    """

    def consume(self):
        self.context.modeling.template.validate()


class ServiceTemplate(ConsumerChain):
    """
    Generates the service template from the presenter.
    """

    def __init__(self, context):
        super(ServiceTemplate, self).__init__(context, (DeriveServiceTemplate,
                                                        CoerceServiceTemplateValues,
                                                        ValidateServiceTemplate))

    def dump(self):
        if self.context.has_arg_switch('yaml'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.template_as_raw
            self.context.write(yaml_dumps(raw, indent=indent))
        elif self.context.has_arg_switch('json'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.template_as_raw
            self.context.write(json_dumps(raw, indent=indent))
        else:
            self.context.modeling.template.dump()


class Types(Consumer):
    """
    Used to just dump the types.
    """

    def dump(self):
        if self.context.has_arg_switch('yaml'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.types_as_raw
            self.context.write(yaml_dumps(raw, indent=indent))
        elif self.context.has_arg_switch('json'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.types_as_raw
            self.context.write(json_dumps(raw, indent=indent))
        else:
            self.context.modeling.template.dump_types()


class InstantiateServiceInstance(Consumer):
    """
    Instantiates the service template into a service instance.
    """

    def consume(self):
        if self.context.modeling.template is None:
            self.context.validation.report('InstantiateServiceInstance consumer: missing service '
                                           'template')
            return

        self.context.modeling.template.instantiate(None)


class CoerceServiceInstanceValues(Consumer):
    """
    Coerces values in the service instance.
    """

    def consume(self):
        self.context.modeling.instance.coerce_values(None, True)


class ValidateServiceInstance(Consumer):
    """
    Validates the service instance.
    """

    def consume(self):
        self.context.modeling.instance.validate()


class SatisfyRequirements(Consumer):
    """
    Satisfies node requirements in the service instance.
    """

    def consume(self):
        self.context.modeling.instance.satisfy_requirements()


class ValidateCapabilities(Consumer):
    """
    Validates capabilities in the service instance.
    """

    def consume(self):
        self.context.modeling.instance.validate_capabilities()


class FindHosts(Consumer):
    """
    Find hosts for all nodes in the service instance.
    """

    def consume(self):
        self.context.modeling.instance.find_hosts()


class ConfigureOperations(Consumer):
    """
    Configures all operations in the service instance.
    """

    def consume(self):
        self.context.modeling.instance.configure_operations()


class ServiceInstance(ConsumerChain):
    """
    Generates the service instance by instantiating the service template.
    """

    def __init__(self, context):
        super(ServiceInstance, self).__init__(context, (InstantiateServiceInstance,
                                                        CoerceServiceInstanceValues,
                                                        ValidateServiceInstance,
                                                        CoerceServiceInstanceValues,
                                                        SatisfyRequirements,
                                                        CoerceServiceInstanceValues,
                                                        ValidateCapabilities,
                                                        FindHosts,
                                                        ConfigureOperations,
                                                        CoerceServiceInstanceValues))

    def dump(self):
        if self.context.has_arg_switch('graph'):
            self.context.modeling.instance.dump_graph()
        elif self.context.has_arg_switch('yaml'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.instance_as_raw
            self.context.write(yaml_dumps(raw, indent=indent))
        elif self.context.has_arg_switch('json'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.instance_as_raw
            self.context.write(json_dumps(raw, indent=indent))
        else:
            self.context.modeling.instance.dump()
