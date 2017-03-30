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

from json import JSONEncoder
from StringIO import StringIO

from . import exceptions
from ..parser.consumption import ConsumptionContext
from ..parser.exceptions import InvalidValueError
from ..parser.presentation import Value
from ..utils.collections import OrderedDict
from ..utils.console import puts
from ..utils.conversion import convert_value_to_type


class ModelJSONEncoder(JSONEncoder):
    def default(self, o):
        from .mixins import ModelMixin
        if isinstance(o, ModelMixin):
            if hasattr(o, 'value'):
                dict_to_return = o.to_dict(fields=('value',))
                return dict_to_return['value']
            else:
                return o.to_dict()
        else:
            return JSONEncoder.default(self, o)


def create_inputs(inputs, template_inputs):
    """
    :param inputs: key-value dict
    :param template_inputs: parameter name to parameter object dict
    :return: dict of parameter name to Parameter models
    """
    merged_inputs = _merge_and_validate_inputs(inputs, template_inputs)

    from . import models
    input_models = []
    for input_name, input_val in merged_inputs.iteritems():
        parameter = models.Parameter(
            name=input_name,
            type_name=template_inputs[input_name].type_name,
            description=template_inputs[input_name].description,
            value=input_val)
        input_models.append(parameter)

    return {input.name: input for input in input_models}


def _merge_and_validate_inputs(inputs, template_inputs):
    """
    :param inputs: key-value dict
    :param template_inputs: parameter name to parameter object dict
    :return:
    """
    merged_inputs = inputs.copy()

    missing_inputs = []
    wrong_type_inputs = {}
    for input_name, input_template in template_inputs.iteritems():
        if input_name not in inputs:
            if input_template.value is not None:
                merged_inputs[input_name] = input_template.value  # apply default value
            else:
                missing_inputs.append(input_name)
        else:
            # Validate input type
            try:
                convert_value_to_type(str(inputs[input_name]), input_template.type_name)
            except ValueError:
                wrong_type_inputs[input_name] = input_template.type_name

    if missing_inputs:
        raise exceptions.MissingRequiredInputsException(
            'Required inputs {0} have not been specified - expected inputs: {1}'
            .format(missing_inputs, template_inputs.keys()))

    if wrong_type_inputs:
        error_message = StringIO()
        for param_name, param_type in wrong_type_inputs.iteritems():
            error_message.write('Input "{0}" must be of type {1}\n'.
                                format(param_name, param_type))
        raise exceptions.InputOfWrongTypeException(error_message.getvalue())

    undeclared_inputs = [input_name for input_name in inputs.keys()
                      if input_name not in template_inputs]
    if undeclared_inputs:
        raise exceptions.UndeclaredInputsException(
            'Undeclared inputs have been specified: {0}; Expected inputs: {1}'
            .format(undeclared_inputs, template_inputs.keys()))

    return merged_inputs


def coerce_value(container, value, report_issues=False):
    if isinstance(value, Value):
        value = value.value

    if isinstance(value, list):
        return [coerce_value(container, v, report_issues) for v in value]
    elif isinstance(value, dict):
        return OrderedDict((k, coerce_value(container, v, report_issues))
                           for k, v in value.iteritems())
    elif hasattr(value, '_evaluate'):
        context = ConsumptionContext.get_thread_local()
        try:
            value = value._evaluate(context, container)
            value = coerce_value(container, value, report_issues)
        except exceptions.CannotEvaluateFunctionException:
            pass
        except InvalidValueError as e:
            if report_issues:
                context.validation.report(e.issue)
    return value


def coerce_dict_values(container, the_dict, report_issues=False):
    if not the_dict:
        return
    coerce_list_values(container, the_dict.itervalues(), report_issues)


def coerce_list_values(container, the_list, report_issues=False):
    if not the_list:
        return
    for value in the_list:
        value.coerce_values(container, report_issues)


def validate_dict_values(the_dict):
    if not the_dict:
        return
    validate_list_values(the_dict.itervalues())


def validate_list_values(the_list):
    if not the_list:
        return
    for value in the_list:
        value.validate()


def instantiate_dict(container, the_dict, from_dict):
    if not from_dict:
        return
    for name, value in from_dict.iteritems():
        value = value.instantiate(container)
        if value is not None:
            the_dict[name] = value


def instantiate_list(container, the_list, from_list):
    if not from_list:
        return
    for value in from_list:
        value = value.instantiate(container)
        if value is not None:
            the_list.append(value)


def dump_list_values(the_list, name):
    if not the_list:
        return
    puts('%s:' % name)
    context = ConsumptionContext.get_thread_local()
    with context.style.indent:
        for value in the_list:
            value.dump()


def dump_dict_values(the_dict, name):
    if not the_dict:
        return
    dump_list_values(the_dict.itervalues(), name)


def dump_interfaces(interfaces, name='Interfaces'):
    if not interfaces:
        return
    puts('%s:' % name)
    context = ConsumptionContext.get_thread_local()
    with context.style.indent:
        for interface in interfaces.itervalues():
            interface.dump()


class classproperty(object):                                                                        # pylint: disable=invalid-name
    def __init__(self, f):
        self._func = f

    def __get__(self, instance, owner):
        return self._func(owner)
