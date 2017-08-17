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
Unified testing for properties (including inputs).

These tests are in addition to the common tests for parameters in test_template_parameters.py.
"""

import pytest

from .test_template_parameters import (MACROS, PERMUTATIONS as PARAMETER_PERMUTATIONS)
from ... import data
from ......mechanisms.utils import matrix


PERMUTATIONS = tuple(
    (macros, name, parameter_section)
    for macros, name, parameter_section in PARAMETER_PERMUTATIONS
    if parameter_section != 'attributes'
)


# Required

@pytest.mark.parametrize('macros,name,parameter_section,type_name', matrix(
    PERMUTATIONS,
    data.PARAMETER_TYPE_NAMES,
    counts=(3, 1)
))
def test_template_parameter_required(parser, macros, name, parameter_section, type_name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
data_types:
  MyType:
    properties:
      my_field:
        type: string
{{ name }}_types:
  MyType:
{%- call type_parameters() %}
my_parameter:
  type: {{ type_name }}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call parameters() -%}
{}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], parameter_section=parameter_section,
          type_name=type_name)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section,type_name', matrix(
    PERMUTATIONS,
    data.PARAMETER_TYPE_NAMES,
    counts=(3, 1)
))
def test_template_parameter_not_required(parser, macros, name, parameter_section, type_name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
data_types:
  MyType:
    properties:
      my_field:
        type: string
{{ name }}_types:
  MyType:
{%- call type_parameters() %}
my_parameter:
  type: {{ type_name }}
  required: false
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call parameters() -%}
{}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], parameter_section=parameter_section,
          type_name=type_name)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section,type_name,value', matrix(
    PERMUTATIONS,
    data.PARAMETER_VALUES,
    counts=(3, 2)
))
def test_template_parameter_required_with_default(parser, macros, name, parameter_section,
                                                  type_name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
data_types:
  MyType:
    properties:
      my_field:
        type: string
{{ name }}_types:
  MyType:
{%- call type_parameters() %}
my_parameter:
  type: {{ type_name }}
  default: {{ value }}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call parameters() -%}
{}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], parameter_section=parameter_section,
          type_name=type_name, value=value)).assert_success()
