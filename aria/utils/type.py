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
Type utilities.
"""

import datetime

from .specification import implements_specification


BASE_TYPES_TO_CANONICAL_NAMES = {
    # TOSCA aliases:
    None.__class__: 'null',
    basestring: 'string',
    int: 'integer',
    float: 'float',
    bool: 'boolean',
    list: 'list',
    tuple: 'list',
    dict: 'map',
    datetime.datetime: 'timestamp'
}

NAMES_TO_CANONICAL_TYPES = {
    # Python:
    'none': None.__class__,
    'basestring': unicode,
    'str': unicode,
    'unicode': unicode,
    'int': int,
    'float': float, # also a TOSCA alias
    'bool': bool,
    'list': list, # also a TOSCA alias
    'tuple': list,
    'dict': dict,
    'datetime': datetime.datetime,

    # YAML 1.2:
    'tag:yaml.org,2002:null': None.__class__,
    'tag:yaml.org,2002:str': unicode,
    'tag:yaml.org,2002:integer': int,
    'tag:yaml.org,2002:float': float,
    'tag:yaml.org,2002:bool': bool,

    # TOSCA aliases:
    'null': None.__class__,
    'string': unicode,
    'integer': int,
    'boolean': bool,

    # TOSCA custom types:
    'map': dict,
    'timestamp': datetime.datetime
}


def full_type_name(value):
    """
    The full class name of a type or instance.
    """

    if not isinstance(value, type):
        value = value.__class__
    module = str(value.__module__)
    name = str(value.__name__)
    return name if module == '__builtin__' else '{0}.{1}'.format(module, name)


@implements_specification('3.2.1-1', 'tosca-simple-1.0')
def canonical_type_name(value):
    """
    Returns the canonical TOSCA type name of a primitive value, or ``None`` if unknown.

    For a list of TOSCA type names, see the `TOSCA Simple Profile v1.0
    cos01 specification <http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/cos01
    /TOSCA-Simple-Profile-YAML-v1.0-cos01.html#_Toc373867862>`__
    """

    for the_type, name in BASE_TYPES_TO_CANONICAL_NAMES.iteritems():
        if isinstance(value, the_type):
            return name
    return None


@implements_specification('3.2.1-2', 'tosca-simple-1.0')
def canonical_type(type_name):
    """
    Return the canonical type for any Python, YAML, or TOSCA type name or alias, or ``None`` if
    unsupported.

    :param type_name: Type name (case insensitive)
    """

    return NAMES_TO_CANONICAL_TYPES.get(type_name.lower())


def validate_value_type(value, type_name):
    """
    Validate that a value is of a specific type. Supports Python, YAML, and TOSCA type names and
    aliases.

    :param type_name: type name (case insensitive)
    :raises ~exceptions.ValueError: on type mismatch
    """

    the_type = canonical_type(type_name)
    if the_type is None:
        raise RuntimeError('Unsupported type name: {0}'.format(type_name))

    # The following Python types do not inherit from the canonical type, but are considered valid
    if (the_type is unicode) and isinstance(value, str):
        return
    if (the_type is list) and isinstance(value, tuple):
        return

    if not isinstance(value, the_type):
        raise ValueError('Value {0} is not of type {1}'.format(value, type_name))


def convert_value_to_type(str_value, python_type_name):
    """
    Converts a value to a specific Python primitive type.

    :param python_type_name: Python primitive type name (case insensitive)
    :raises ~exceptions.ValueError: for unsupported types or conversion failure
    """

    python_type_name = python_type_name.lower()
    try:
        if python_type_name in ('str', 'unicode'):
            return str_value.decode('utf-8')
        elif python_type_name == 'int':
            return int(str_value)
        elif python_type_name == 'bool':
            return bool(str_value)
        elif python_type_name == 'float':
            return float(str_value)
        else:
            raise ValueError('Unsupported Python type name: {0}'.format(python_type_name))
    except ValueError:
        raise ValueError('Failed to to convert {0} to {1}'.format(str_value,
                                                                  python_type_name))
