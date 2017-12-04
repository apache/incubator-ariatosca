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

    def default(self, o):                                                                           # pylint: disable=method-hidden
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


def validate_no_undeclared_inputs(declared_inputs, supplied_inputs):

    undeclared_inputs = [input for input in supplied_inputs if input not in declared_inputs]
    if undeclared_inputs:
        raise exceptions.UndeclaredInputsException(
            'Undeclared inputs have been provided: {0}; Declared inputs: {1}'
            .format(string_list_as_string(undeclared_inputs),
                    string_list_as_string(declared_inputs.keys())))


def validate_required_inputs_are_supplied(declared_inputs, supplied_inputs):
    required_inputs = [input for input in declared_inputs.values() if input.required]
    missing_required_inputs = [input for input in required_inputs
                               if input.name not in supplied_inputs and not input.value]
    if missing_required_inputs:
        raise exceptions.MissingRequiredInputsException(
            'Required inputs {0} have not been provided values'
            .format(string_list_as_string(missing_required_inputs)))


def merge_parameter_values(provided_values, declared_parameters, model_cls=None):
    """
    Merges parameter values according to those declared by a type.

    Exceptions will be raised for validation errors.

    :param provided_values: provided parameter values or None
    :type provided_values: {:obj:`basestring`: object}
    :param declared_parameters: declared parameters
    :type declared_parameters: {:obj:`basestring`: :class:`~aria.modeling.models.Parameter`}
    :param model_cls: the model class that should be created from a provided value
    :type model_cls: :class:`~aria.modeling.models.Input` or :class:`~aria.modeling.models.Argument`
    :return: the merged parameters
    :rtype: {:obj:`basestring`: :class:`~aria.modeling.models.Parameter`}
    :raises ~aria.modeling.exceptions.UndeclaredInputsException: if a key in
     ``parameter_values`` does not exist in ``declared_parameters``
    :raises ~aria.modeling.exceptions.MissingRequiredInputsException: if a key in
     ``declared_parameters`` does not exist in ``parameter_values`` and also has no default value
    :raises ~aria.modeling.exceptions.ParametersOfWrongTypeException: if a value in
      ``parameter_values`` does not match its type in ``declared_parameters``
    """

    provided_values = provided_values or {}
    provided_values_of_wrong_type = OrderedDict()
    model_parameters = OrderedDict()
    model_cls = model_cls or _get_class_from_sql_relationship(declared_parameters)

    for declared_parameter_name, declared_parameter in declared_parameters.iteritems():
        if declared_parameter_name in provided_values:
            # a value has been provided
            value = provided_values[declared_parameter_name]

            # Validate type
            type_name = declared_parameter.type_name
            try:
                validate_value_type(value, type_name)
            except ValueError:
                provided_values_of_wrong_type[declared_parameter_name] = type_name
            except RuntimeError:
                # TODO This error shouldn't be raised (or caught), but right now we lack support
                # for custom data_types, which will raise this error. Skipping their validation.
                pass
            model_parameters[declared_parameter_name] = model_cls(                                  # pylint: disable=unexpected-keyword-arg
                name=declared_parameter_name,
                type_name=type_name,
                description=declared_parameter.description,
                value=value)
        else:
            # Copy default value from declaration
            model_parameters[declared_parameter_name] = model_cls(
                value=declared_parameter._value,
                name=declared_parameter.name,
                type_name=declared_parameter.type_name,
                description=declared_parameter.description)

    if provided_values_of_wrong_type:
        error_message = StringIO()
        for param_name, param_type in provided_values_of_wrong_type.iteritems():
            error_message.write('Parameter "{0}" is not of declared type "{1}"{2}'
                                .format(param_name, param_type, os.linesep))
        raise exceptions.ParametersOfWrongTypeException(error_message.getvalue())

    return model_parameters


def parameters_as_values(the_dict):
    return dict((k, v.value) for k, v in the_dict.iteritems())


def dict_as_arguments(the_dict):
    return OrderedDict((name, value.as_argument()) for name, value in the_dict.iteritems())


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


def _get_class_from_sql_relationship(field):
    class_ = field._sa_adapter.owner_state.class_
    prop_name = field._sa_adapter.attr.key
    return getattr(class_, prop_name).property.mapper.class_
