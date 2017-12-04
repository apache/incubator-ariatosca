# -*- coding: utf-8 -*-
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


# Keywords

TYPE_NAME_PLURAL = {
    'artifact': 'artifacts',
    'data': 'datatypes',
    'capability': 'capabilities',
    'interface': 'interfaces',
    'relationship': 'relationships',
    'node': 'nodes',
    'group': 'groups',
    'policy': 'policies'
}
TEMPLATE_NAME_SECTIONS = {
    'node': 'node_templates',
    'group': 'groups',
    'relationship': 'relationship_templates',
    'policy': 'policies'
}
PRIMITIVE_TYPE_NAMES = ('string', 'integer', 'float', 'boolean')
PARAMETER_TYPE_NAMES = PRIMITIVE_TYPE_NAMES + ('MyType',)
CONSTRAINTS_WITH_VALUE = ('equal', 'greater_than', 'greater_or_equal', 'less_than', 'less_or_equal')
CONSTRAINTS_WITH_VALUE_LIST = ('valid_values',)
CONSTRAINTS_WITH_VALUE_RANGE = ('in_range',)
CONSTRAINTS_WITH_VALUE_NON_NEGATIVE_INT = ('length', 'min_length', 'max_length')


# Values

PRIMITIVE_VALUES = ('null', 'true', 'a string', '123', '0.123', '[]', '{}')
NOT_A_DICT = ('null', 'true', 'a string', '123', '0.123', '[]')
NOT_A_DICT_WITH_ONE_KEY = NOT_A_DICT + ('{}', '{k1: v1, k2: v2}',)
NOT_A_DICT_OR_STRING = ('null', 'true', '123', '0.123', '[]')
NOT_A_LIST = ('null', 'true', 'a string', '123', '0.123', '{}')
NOT_A_LIST_OF_TWO = NOT_A_LIST + ('[]', '[a]', '[a, b, c]')
NOT_A_STRING = ('null', 'true', '123', '0.123', '[]', '{}')
NOT_A_BOOL = ('null', 'a string', '123', '0.123', '[]', '{}')
NOT_A_RANGE = NOT_A_LIST + (
    '[]', '[ 1 ]', '[ 1, 2, 3 ]',
    '[ 1, 1 ]', '[ 2, 1 ]',
    '[ 1, a string ]', '[ a string, 1 ]',
    '[ 1.5, 2 ]', '[ 1, 2.5 ]'
)
OCCURRENCES = ('[ 0, 1 ]', '[ 10, UNBOUNDED ]')
BAD_OCCURRENCES = NOT_A_RANGE + ('[ -1, 1 ]', '[ 0, unbounded ]')
GOOD_VERSIONS = ("'6.1'", '2.0.1', '3.1.0.beta', "'1.0.0.alpha-10'")
BAD_VERSIONS = ('a_string', '1.2.3.4.5', '1.2.beta', '1.0.0.alpha-x')
STATUSES = ('supported', 'unsupported', 'experimental', 'deprecated')
PARAMETER_VALUES = (
    ('string', 'a string'),
    ('integer', '1'),
    ('float', '1.1'),
    ('MyType', '{my_field: a string}')
)
ENTRY_SCHEMA_VALUES = (
    ('string', 'a string', 'another string'),
    ('integer', '1', '2'),
    ('float', '1.1', '2.2'),
    ('MyType', '{my_field: a string}', '{}')
)
ENTRY_SCHEMA_VALUES_BAD = (
    ('string', 'a string', '1'),
    ('integer', '1', 'a string'),
    ('float', '1.1', 'a string'),
    ('MyType', '{my_field: a string}', 'a string')
)
