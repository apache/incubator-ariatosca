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
Validation utilities.
"""

from .formatting import string_list_as_string


class ValidatorMixin(object):
    """
    A mix0in that should be added to classes that require validating user input.
    """

    _ARGUMENT_TYPE_MESSAGE = '{name} argument must be {type} based, got {arg!r}'
    _ARGUMENT_CHOICE_MESSAGE = '{name} argument must be in {choices}, got {arg!r}'

    @classmethod
    def validate_in_choice(cls, name, argument, choices):
        """
        Validate ``argument`` is in ``choices``
        """
        if argument not in choices:
            raise TypeError(cls._ARGUMENT_CHOICE_MESSAGE.format(
                name=name, choices=choices, arg=argument))

    @classmethod
    def validate_type(cls, argument_name, argument, expected_type):
        """
        Validate ``argument`` is a subclass of ``expected_type``
        """
        if not issubclass(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))

    @classmethod
    def validate_instance(cls, argument_name, argument, expected_type):
        """
        Validate ``argument`` is a instance of ``expected_type``
        """
        if not isinstance(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))

    @classmethod
    def validate_callable(cls, argument_name, argument):
        """
        Validate ``argument`` is callable
        """
        if not callable(argument):
            raise TypeError(cls._ARGUMENT_TYPE_MESSAGE.format(
                name=argument_name, type='callable', arg=argument))


def validate_function_arguments(func, func_kwargs):
    """
    Validates all required arguments are supplied to ``func`` and that no additional arguments are
    supplied.
    """

    _kwargs_flags = 8

    has_kwargs = func.func_code.co_flags & _kwargs_flags != 0
    args_count = func.func_code.co_argcount

    # all args without the ones with default values
    args = func.func_code.co_varnames[:args_count]
    non_default_args = args[:len(func.func_defaults)] if func.func_defaults else args

    # Check if any args without default values is missing in the func_kwargs
    for arg in non_default_args:
        if arg not in func_kwargs:
            raise ValueError(
                'The argument "{arg}" is not provided and does not have a default value for '
                'function "{func.__name__}"'.format(arg=arg, func=func))

    # check if there are any extra kwargs
    extra_kwargs = [arg for arg in func_kwargs.keys() if arg not in args]

    # assert that the function has kwargs
    if extra_kwargs and not has_kwargs:
        raise ValueError("The following extra kwargs were supplied: {extra_kwargs}".format(
            extra_kwargs=string_list_as_string(extra_kwargs)
        ))
