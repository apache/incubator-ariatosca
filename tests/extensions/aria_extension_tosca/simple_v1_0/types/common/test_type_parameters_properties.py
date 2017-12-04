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

"""
Unified testing for properties and inputs.

These tests are in addition to the common tests for parameters in test_type_parameters.py.

Compare with test_node_template_node_filter_constraints.py. Note that though the constraints are the
same, their syntax is very different, making it difficult to test all permutations together.
"""

import pytest

from .test_type_parameters import (MACROS, PERMUTATIONS as PARAMETER_PERMUTATIONS)
from ... import data
from ......mechanisms.utils import matrix


PERMUTATIONS = tuple(
    (macros, name, parameter_section)
    for macros, name, parameter_section in PARAMETER_PERMUTATIONS
    if parameter_section != 'attributes'
)


# Required

@pytest.mark.parametrize('macros,name,parameter_section,value', matrix(
    PERMUTATIONS,
    data.NOT_A_BOOL,
    counts=(3, 1)
))
def test_type_parameter_required_syntax_type(parser, macros, name, parameter_section, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  required: {{ value }}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_required(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  required: true
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()


# Constraints

@pytest.mark.parametrize('macros,name,parameter_section,value', matrix(
    PERMUTATIONS,
    data.NOT_A_LIST,
    counts=(3, 1)
))
def test_type_parameter_constraints_syntax_type(parser, macros, name, parameter_section, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  constraints: {{ value }}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_constraints_syntax_empty(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  constraints: []
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section,constraint', matrix(
    PERMUTATIONS,
    data.CONSTRAINTS_WITH_VALUE,
    counts=(3, 1)
))
def test_type_parameter_constraints_with_value(parser, macros, name, parameter_section, constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyDataType:
    properties:
      my_field:
        type: string
{{- additions(name != 'data') }}
{%- call parameters() %}
my_parameter:
  type: MyDataType
  constraints:
    - {{ constraint }}: {my_field: a string}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, constraint=constraint)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section,constraint', matrix(
    PERMUTATIONS,
    data.CONSTRAINTS_WITH_VALUE_LIST,
    counts=(3, 1)
))
def test_type_parameter_constraints_with_value_list(parser, macros, name, parameter_section,
                                                    constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyDataType:
    properties:
      my_field:
        type: string
{{- additions(name != 'data') }}
{%- call parameters() %}
my_parameter:
  type: MyDataType
  constraints:
    - {{ constraint }}:
      - {my_field: string one}
      - {my_field: string two}
      - {my_field: string three}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, constraint=constraint)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section,constraint', matrix(
    PERMUTATIONS,
    data.CONSTRAINTS_WITH_VALUE_RANGE,
    counts=(3, 1)
))
def test_type_parameter_constraints_with_value_range(parser, macros, name, parameter_section,
                                                     constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyDataType:
    properties:
      my_field:
        type: string
{{- additions(name != 'data') }}
{%- call parameters() %}
my_parameter:
  type: MyDataType
  constraints:
    - {{ constraint }}:
      - {my_field: string a}
      - {my_field: string b}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, constraint=constraint)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section,constraint', matrix(
    PERMUTATIONS,
    data.CONSTRAINTS_WITH_VALUE_RANGE,
    counts=(3, 1)
))
def test_type_parameter_constraints_with_value_range_too_many(parser, macros, name,
                                                              parameter_section, constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyDataType:
    properties:
      my_field:
        type: string
{{- additions(name != 'data') }}
{%- call parameters() %}
my_parameter:
  type: MyDataType
  constraints:
    - {{ constraint }}:
      - {my_field: string a}
      - {my_field: string b}
      - {my_field: string c}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, constraint=constraint)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section,constraint', matrix(
    PERMUTATIONS,
    data.CONSTRAINTS_WITH_VALUE_RANGE,
    counts=(3, 1)
))
def test_type_parameter_constraints_with_value_range_bad(macros, parser, name, parameter_section,
                                                         constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyDataType:
    properties:
      my_field:
        type: string
{{- additions(name != 'data') }}
{%- call parameters() %}
my_parameter:
  type: MyDataType
  constraints:
    - {{ constraint }}:
      - {my_field: string b}
      - {my_field: string a}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, constraint=constraint)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_constraints_pattern(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  constraints:
    - pattern: ^pattern$
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_constraints_pattern_bad(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  constraints:
    - pattern: (
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section,constraint', matrix(
    PERMUTATIONS,
    data.CONSTRAINTS_WITH_VALUE_NON_NEGATIVE_INT,
    counts=(3, 1)
))
def test_type_parameter_constraints_with_value_integer(parser, macros, name, parameter_section,
                                                       constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  constraints:
    - {{ constraint }}: 1
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, constraint=constraint)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section,constraint', matrix(
    PERMUTATIONS,
    data.CONSTRAINTS_WITH_VALUE_NON_NEGATIVE_INT,
    counts=(3, 1)
))
def test_type_parameter_constraints_with_value_integer_bad(parser, macros, name, parameter_section,
                                                           constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  constraints:
    - {{ constraint }}: -1
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, constraint=constraint)).assert_failure()


# Unicode

@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_constraints_pattern_unicode(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters('類型') %}
參數:
  type: string
  constraints:
    - pattern: ^模式$
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()
