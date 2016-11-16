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


class Derive(Consumer):
    """
    Derives the service model.
    """

    def consume(self):
        if self.context.presentation.presenter is None:
            self.context.validation.report('Derive consumer: missing presenter')
            return

        if not hasattr(self.context.presentation.presenter, '_get_service_model'):
            self.context.validation.report('Derive consumer: presenter does not support '
                                           '"_get_service_model"')
            return

        self.context.modeling.model = \
            self.context.presentation.presenter._get_service_model(self.context)


class CoerceModelValues(Consumer):
    """
    Coerces values in the service model.
    """

    def consume(self):
        self.context.modeling.model.coerce_values(self.context, None, True)


class ValidateModel(Consumer):
    """
    Validates the service model.
    """

    def consume(self):
        self.context.modeling.model.validate(self.context)

class Model(ConsumerChain):
    """
    Generates the service model by deriving it from the presentation.
    """

    def __init__(self, context):
        super(Model, self).__init__(context, (Derive, CoerceModelValues, ValidateModel))

    def dump(self):
        if self.context.has_arg_switch('yaml'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.model_as_raw
            self.context.write(yaml_dumps(raw, indent=indent))
        elif self.context.has_arg_switch('json'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.model_as_raw
            self.context.write(json_dumps(raw, indent=indent))
        else:
            self.context.modeling.model.dump(self.context)

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
            self.context.modeling.dump_types(self.context)

class Instantiate(Consumer):
    """
    Instantiates the service model.
    """

    def consume(self):
        if self.context.modeling.model is None:
            self.context.validation.report('Instantiate consumer: missing service model')
            return

        self.context.modeling.model.instantiate(self.context, None)

class CoerceInstanceValues(Consumer):
    """
    Coerces values in the service instance.
    """

    def consume(self):
        self.context.modeling.instance.coerce_values(self.context, None, True)

class ValidateInstance(Consumer):
    """
    Validates the service instance.
    """

    def consume(self):
        self.context.modeling.instance.validate(self.context)

class SatisfyRequirements(Consumer):
    """
    Satisfies node requirements in the service instance.
    """

    def consume(self):
        self.context.modeling.instance.satisfy_requirements(self.context)

class ValidateCapabilities(Consumer):
    """
    Validates capabilities in the service instance.
    """

    def consume(self):
        self.context.modeling.instance.validate_capabilities(self.context)

class Instance(ConsumerChain):
    """
    Generates the service instance by instantiating the service model.
    """

    def __init__(self, context):
        super(Instance, self).__init__(context, (Instantiate, CoerceInstanceValues,
                                                 ValidateInstance, CoerceInstanceValues,
                                                 SatisfyRequirements, CoerceInstanceValues,
                                                 ValidateCapabilities, CoerceInstanceValues))

    def dump(self):
        if self.context.has_arg_switch('graph'):
            self.context.modeling.instance.dump_graph(self.context)
        elif self.context.has_arg_switch('yaml'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.instance_as_raw
            self.context.write(yaml_dumps(raw, indent=indent))
        elif self.context.has_arg_switch('json'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.modeling.instance_as_raw
            self.context.write(json_dumps(raw, indent=indent))
        else:
            self.context.modeling.instance.dump(self.context)
