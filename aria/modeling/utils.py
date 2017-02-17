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

from ..parser.consumption import ConsumptionContext
from ..parser.exceptions import InvalidValueError
from ..parser.presentation import Value
from ..utils.collections import OrderedDict
from ..utils.console import puts
from .exceptions import CannotEvaluateFunctionException


def coerce_value(container, value, report_issues=False):
    if isinstance(value, Value):
        value = value.value

    if isinstance(value, list):
        return [coerce_value(container, v, report_issues) for v in value]
    elif isinstance(value, dict):
        return OrderedDict((k, coerce_value(container, v, report_issues))
                           for k, v in value.items())
    elif hasattr(value, '_evaluate'):
        context = ConsumptionContext.get_thread_local()
        try:
            value = value._evaluate(context, container)
            value = coerce_value(container, value, report_issues)
        except CannotEvaluateFunctionException:
            pass
        except InvalidValueError as e:
            if report_issues:
                context.validation.report(e.issue)
    return value


def validate_dict_values(the_dict):
    if not the_dict:
        return
    validate_list_values(the_dict.itervalues())


def validate_list_values(the_list):
    if not the_list:
        return
    for value in the_list:
        value.validate()


def coerce_dict_values(container, the_dict, report_issues=False):
    if not the_dict:
        return
    coerce_list_values(container, the_dict.itervalues(), report_issues)


def coerce_list_values(container, the_list, report_issues=False):
    if not the_list:
        return
    for value in the_list:
        value.coerce_values(container, report_issues)


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
