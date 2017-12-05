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


PERMUTATIONS = tuple(
    (macros, name, parameter_section)
    for macros, name, parameter_section in PARAMETER_PERMUTATIONS
    if name is not None
)

PERMUTATIONS_NO_RELATIONSHIP = tuple(
    (macros, name, parameter_section)
    for macros, name, parameter_section in PERMUTATIONS
    if macros not in ('relationship-interface', 'relationship-operation')
)


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_add(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters('MyType1') %}
my_parameter1:
  type: string
{% endcall %}
{%- call parameters('MyType2', 'MyType1') %}
my_parameter2:
  type: string
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_add_default(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters('MyType1') %}
my_parameter:
  type: string
{% endcall %}
{%- call parameters('MyType2', 'MyType1') %}
my_parameter:
  type: string
  default: my value
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_type_override(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyDataType1: {}
  MyDataType2:
    derived_from: MyDataType1
{{- additions(name != 'data') }}
{%- call parameters('MyType1') %}
my_parameter:
  type: MyDataType1
{% endcall %}
{%- call parameters('MyType2', 'MyType1') %}
my_parameter:
  type: MyDataType2
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()


# We are skipping relationship interfaces, because node requirements can be overridden completely
@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS_NO_RELATIONSHIP)
def test_type_parameter_type_override_bad(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyDataType1: {}
  MyDataType2: {}
{{- additions(name != 'data') }}
{%- call parameters('MyType1') %}
my_parameter:
  type: MyDataType1
{% endcall %}
{%- call parameters('MyType2', 'MyType1') %}
my_parameter:
  type: MyDataType2
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_failure()
