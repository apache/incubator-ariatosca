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


def validate_value_type(value, type_name):
    """
    Validate a value is of a specific type.
    A ValueError will be raised on type mismatch.
    Supports both python and yaml type names.
    """

    #TODO add timestamp type?
    name_to_type = {
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'str': str,
        'unicode': str,
        'string': str,
        'int': int,
        'integer': int,
        'bool': bool,
        'boolean': bool,
        'float': float
    }

    type_ = name_to_type.get(type_name.lower())
    if type_ is None:
        raise RuntimeError('No supported type_name was provided')

    if not isinstance(value, type_):
        raise ValueError('Value {0} is not of type {1}'.format(value, type_name))


def convert_value_to_type(str_value, type_name):
    try:
        if type_name.lower() in ['str', 'unicode']:
            return str_value.decode('utf-8')
        elif type_name.lower() == 'int':
            return int(str_value)
        elif type_name.lower() == 'bool':
            return bool(str_value)
        elif type_name.lower() == 'float':
            return float(str_value)
        else:
            raise ValueError('No supported type_name was provided')
    except ValueError:
        raise ValueError('Trying to convert {0} to {1} failed'.format(str_value,
                                                                      type_name))
