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


def convert_value_to_type(str_value, type_name):
    """Supports both python and yaml type names"""
    #TODO add timestamp type?
    try:
        if type_name.lower() in ['str', 'unicode', 'string']:
            return str_value.decode('utf-8')
        elif type_name.lower() in ['int', 'integer']:
            return int(str_value)
        elif type_name.lower() in ['bool', 'boolean']:
            return bool(str_value)
        elif type_name.lower() == 'float':
            return float(str_value)
        else:
            raise ValueError('No supported type_name was provided')
    except ValueError:
        raise ValueError('Trying to convert {0} to {1} failed'.format(str_value,
                                                                      type_name))
