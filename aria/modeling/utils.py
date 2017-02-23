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

from random import randrange

from shortuuid import ShortUUID
from sqlalchemy.orm.exc import DetachedInstanceError
from networkx.release import name

from ..utils.console import puts


# UUID = ShortUUID() # default alphabet is base57, which is alphanumeric without visually ambiguous
# characters; ID length is 22
UUID = ShortUUID(alphabet='abcdefghijklmnopqrstuvwxyz0123456789')  # alphanumeric; ID length is 25


def generate_id_string(length=None):
    """
    A random string with a strong guarantee of universal uniqueness (uses UUID).

    The default length is 25 characters.
    """

    the_id = UUID.uuid()
    if length is not None:
        the_id = the_id[:length]
    return the_id


def generate_hex_string():
    """
    A random string of 5 hex digits with no guarantee of universal uniqueness.
    """

    return '%05x' % randrange(16 ** 5)


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
    for value in from_list.iteritems():
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


def dump_parameters(context, parameters, name='Properties'):
    if not parameters:
        return
    puts('%s:' % name)
    with context.style.indent:
        for parameter_name, parameter in parameters.iteritems():
            if parameter.type_name is not None:
                puts('%s = %s (%s)' % (context.style.property(parameter_name),
                                       context.style.literal(parameter.value),
                                       context.style.type(parameter.type_name)))
            else:
                puts('%s = %s' % (context.style.property(parameter_name),
                                  context.style.literal(parameter.value)))
            if parameter.description:
                puts(context.style.meta(parameter.description))


def dump_interfaces(context, interfaces, name='Interfaces'):
    if not interfaces:
        return
    puts('%s:' % name)
    with context.style.indent:
        for interface in interfaces.itervalues():
            interface.dump(context)


def pluralize(noun):
    if noun.endswith('s'):
        return '{0}es'.format(noun)
    elif noun.endswith('y'):
        return '{0}ies'.format(noun[:-1])
    else:
        return '{0}s'.format(noun)


class classproperty(object):                                                                        # pylint: disable=invalid-name
    def __init__(self, f):
        self._func = f

    def __get__(self, instance, owner):
        return self._func(owner)


def query_has_item_named(the_list, name):
        try:
            # This is most efficient, however it will not work if we don't have a session
            return the_list.filter_by(name=name).count() > 0
        except DetachedInstanceError:
            # This will always work
            return name in [v.name for v in the_list.all()]
