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

from copy import deepcopy

from ..parser.exceptions import InvalidValueError
from ..parser.presentation import Value
from ..utils.collections import OrderedDict
from ..utils.console import puts
from .exceptions import CannotEvaluateFunctionException


def coerce_value(context, container, value, report_issues=False):
    if isinstance(value, Value):
        value = value.value

    if isinstance(value, list):
        return [coerce_value(context, container, v, report_issues) for v in value]
    elif isinstance(value, dict):
        return OrderedDict((k, coerce_value(context, container, v, report_issues))
                           for k, v in value.items())
    elif hasattr(value, '_evaluate'):
        try:
            value = value._evaluate(context, container)
            value = coerce_value(context, container, value, report_issues)
        except CannotEvaluateFunctionException:
            pass
        except InvalidValueError as e:
            if report_issues:
                context.validation.report(e.issue)
    return value


def validate_dict_values(context, the_dict):
    if not the_dict:
        return
    validate_list_values(context, the_dict.itervalues())


def validate_list_values(context, the_list):
    if not the_list:
        return
    for value in the_list:
        value.validate(context)


def coerce_dict_values(context, container, the_dict, report_issues=False):
    if not the_dict:
        return
    coerce_list_values(context, container, the_dict.itervalues(), report_issues)


def coerce_list_values(context, container, the_list, report_issues=False):
    if not the_list:
        return
    for value in the_list:
        value.coerce_values(context, container, report_issues)


def instantiate_dict(context, container, the_dict, from_dict):
    if not from_dict:
        return
    for name, value in from_dict.iteritems():
        value = value.instantiate(context, container)
        if value is not None:
            the_dict[name] = value


def instantiate_list(context, container, the_list, from_list):
    if not from_list:
        return
    for value in from_list:
        value = value.instantiate(context, container)
        if value is not None:
            the_list.append(value)


def dump_list_values(context, the_list, name):
    if not the_list:
        return
    puts('%s:' % name)
    with context.style.indent:
        for value in the_list:
            value.dump(context)


def dump_dict_values(context, the_dict, name):
    if not the_dict:
        return
    dump_list_values(context, the_dict.itervalues(), name)


def dump_interfaces(context, interfaces, name='Interfaces'):
    if not interfaces:
        return
    puts('%s:' % name)
    with context.style.indent:
        for interface in interfaces.itervalues():
            interface.dump(context)




def deepcopy_with_locators(value):
    """
    Like :code:`deepcopy`, but also copies over locators.
    """

    res = deepcopy(value)
    copy_locators(res, value)
    return res


def copy_locators(target, source):
    """
    Copies over :code:`_locator` for all elements, recursively.

    Assumes that target and source have exactly the same list/dict structure.
    """

    locator = getattr(source, '_locator', None)
    if locator is not None:
        try:
            setattr(target, '_locator', locator)
        except AttributeError:
            pass

    if isinstance(target, list) and isinstance(source, list):
        for i, _ in enumerate(target):
            copy_locators(target[i], source[i])
    elif isinstance(target, dict) and isinstance(source, dict):
        for k, v in target.items():
            copy_locators(v, source[k])


class classproperty(object):                                                                        # pylint: disable=invalid-name
    def __init__(self, f):
        self._func = f

    def __get__(self, instance, owner):
        return self._func(owner)
