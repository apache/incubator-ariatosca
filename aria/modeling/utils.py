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
Miscellaneous modeling utilities.
"""

import os
from json import JSONEncoder
from StringIO import StringIO

from . import exceptions
from ..parser.consumption import ConsumptionContext
from ..utils.console import puts
from ..utils.type import validate_value_type
from ..utils.collections import OrderedDict
from ..utils.formatting import string_list_as_string


class ModelJSONEncoder(JSONEncoder):
    """
    JSON encoder that automatically unwraps ``value`` attributes.
    """
    def __init__(self, *args, **kwargs):
        # Just here to make sure Sphinx doesn't grab the base constructor's docstring
        super(ModelJSONEncoder, self).__init__(*args, **kwargs)

    def default(self, o):  # pylint: disable=method-hidden
        from .mixins import ModelMixin
        if isinstance(o, ModelMixin):
            if hasattr(o, 'value'):
                dict_to_return = o.to_dict(fields=('value',))
                return dict_to_return['value']
            else:
                return o.to_dict()
        else:
            return JSONEncoder.default(self, o)


class NodeTemplateContainerHolder(object):
    """
    Wrapper that allows using a :class:`~aria.modeling.models.NodeTemplate` model directly as the
    ``container_holder`` input for :func:`~aria.modeling.functions.evaluate`.
    """

    def __init__(self, node_template):
        self.container = node_template
        self.service = None

    @property
    def service_template(self):
        return self.container.service_template


def merge_parameter_values(parameter_values, declared_parameters, model_cls):
    """
    Merges parameter values according to those declared by a type.

    Exceptions will be raised for validation errors.

    :param parameter_values: provided parameter values or None
    :type parameter_values: {:obj:`basestring`: object}
    :param declared_parameters: declared parameters
    :type declared_parameters: {:obj:`basestring`: :class:`~aria.modeling.models.Parameter`}
    :return: the merged parameters
    :rtype: {:obj:`basestring`: :class:`~aria.modeling.models.Parameter`}
    :raises ~aria.modeling.exceptions.UndeclaredParametersException: if a key in
     ``parameter_values`` does not exist in ``declared_parameters``
    :raises ~aria.modeling.exceptions.MissingRequiredParametersException: if a key in
     ``declared_parameters`` does not exist in ``parameter_values`` and also has no default value
    :raises ~aria.modeling.exceptions.ParametersOfWrongTypeException: if a value in
      ``parameter_values`` does not match its type in ``declared_parameters``
    """

    parameter_values = parameter_values or {}

    undeclared_names = list(set(parameter_values.keys()).difference(declared_parameters.keys()))
    if undeclared_names:
        raise exceptions.UndeclaredParametersException(
            'Undeclared parameters have been provided: {0}; Declared: {1}'
            .format(string_list_as_string(undeclared_names),
                    string_list_as_string(declared_parameters.keys())))

    parameters = OrderedDict()

    missing_names = []
    wrong_type_values = OrderedDict()
    for declared_parameter_name, declared_parameter in declared_parameters.iteritems():
        if declared_parameter_name in parameter_values:
            # Value has been provided
            value = parameter_values[declared_parameter_name]

            # Validate type
            type_name = declared_parameter.type_name
            try:
                validate_value_type(value, type_name)
            except ValueError:
                wrong_type_values[declared_parameter_name] = type_name
            except RuntimeError:
                # TODO: This error shouldn't be raised (or caught), but right now we lack support
                # for custom data_types, which will raise this error. Skipping their validation.
                pass

            # Wrap in Parameter model
            parameters[declared_parameter_name] = model_cls( # pylint: disable=unexpected-keyword-arg
                name=declared_parameter_name,
                type_name=type_name,
                description=declared_parameter.description,
                value=value)
        elif declared_parameter.value is not None:
            # Copy default value from declaration
            parameters[declared_parameter_name] = declared_parameter.instantiate(None)
        else:
            # Required value has not been provided
            missing_names.append(declared_parameter_name)

    if missing_names:
        raise exceptions.MissingRequiredParametersException(
            'Declared parameters {0} have not been provided values'
            .format(string_list_as_string(missing_names)))

    if wrong_type_values:
        error_message = StringIO()
        for param_name, param_type in wrong_type_values.iteritems():
            error_message.write('Parameter "{0}" is not of declared type "{1}"{2}'
                                .format(param_name, param_type, os.linesep))
        raise exceptions.ParametersOfWrongTypeException(error_message.getvalue())

    return parameters


def coerce_dict_values(the_dict, report_issues=False):
    if not the_dict:
        return
    coerce_list_values(the_dict.itervalues(), report_issues)


def coerce_list_values(the_list, report_issues=False):
    if not the_list:
        return
    for value in the_list:
        value.coerce_values(report_issues)


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
        self.__doct__ = f.__doc__

    def __get__(self, instance, owner):
        return self._func(owner)


def fix_doc(cls):
    """
    Class decorator to use the last base class's docstring and make sure Sphinx doesn't grab the
    base constructor's docstring.
    """
    original_init = cls.__init__
    def init(*args, **kwargs):
        original_init(*args, **kwargs)

    cls.__init__ = init
    cls.__doc__ = cls.__bases__[-1].__doc__

    return cls
