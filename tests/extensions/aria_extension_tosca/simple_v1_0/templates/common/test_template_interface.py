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

import pytest

from ... import data
from ......mechanisms.utils import matrix


MAIN_MACROS = """
{% macro additions() %}
{%- endmacro %}
{% macro type_interfaces() %}
    interfaces: {{ caller()|indent(6) }}
{%- endmacro %}
{% macro interfaces() %}
      interfaces: {{ caller()|indent(8) }}
{%- endmacro %}
"""

RELATIONSHIP_MACROS = """
{% macro additions() %}
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
{%- endmacro %}
{% macro type_interfaces() %}
    requirements:
      - my_requirement:
          capability: MyType
          relationship:
            type: MyType
            interfaces: {{ caller()|indent(14) }}
{%- endmacro %}
{% macro interfaces() %}
      requirements:
        - my_requirement:
            relationship:
              interfaces: {{ caller()|indent(16) }}
{%- endmacro %}
"""

RELATIONSHIP_TYPE_MACROS = """
{% macro additions() %}
capability_types:
  MyType: {}
{%- endmacro %}
{% macro type_interfaces() %}
    requirements:
      - my_requirement:
          capability: MyType
          relationship:
            type: MyType
relationship_types:
  MyType:
    interfaces: {{ caller()|indent(6) }}
{%- endmacro %}
{% macro interfaces() %}
      requirements:
        - my_requirement:
            relationship:
              interfaces: {{ caller()|indent(16) }}
{%- endmacro %}
"""

RELATIONSHIP_TEMPLATE_MACROS = """
{% macro additions() %}
capability_types:
  MyType: {}
{%- endmacro %}
{% macro type_interfaces() %}
    requirements:
      - my_requirement:
          capability: MyType
          relationship:
            type: MyType
relationship_types:
  MyType:
    interfaces: {{ caller()|indent(6) }}
{%- endmacro %}
{% macro interfaces() %}
      requirements:
        - my_requirement:
            relationship: my_template
  relationship_templates:
    my_template:
      type: MyType
      interfaces: {{ caller()|indent(8) }}
{%- endmacro %}
"""

MACROS = {
    'main': MAIN_MACROS,
    'relationship': RELATIONSHIP_MACROS,
    'relationship-type': RELATIONSHIP_TYPE_MACROS,
    'relationship-template': RELATIONSHIP_TEMPLATE_MACROS
}

PERMUTATIONS = (
    ('main', 'node'),
    ('main', 'group'),
    ('main', 'relationship'),
    ('relationship', 'node'),
    ('relationship-type', 'node'),
    ('relationship-template', 'node')
)


# Interfaces section

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_DICT,
    counts=(2, 1)
))
def test_template_interfaces_section_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() -%}
{}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() -%}
{{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interfaces_section_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() -%}
{}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() -%}
{}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


# Interface

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_DICT,
    counts=(2, 1)
))
def test_template_interface_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface: {}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


# Interface input

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_DICT,
    counts=(2, 1)
))
def test_template_interface_inputs_section_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  inputs: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_inputs_section_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  inputs: {}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


@pytest.mark.parametrize('macros,name,type_name,value', matrix(
    PERMUTATIONS,
    data.PARAMETER_VALUES,
    counts=(2, 2)
))
def test_template_interface_input_from_type(parser, macros, name, type_name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
data_types:
  MyType:
    properties:
      my_field:
        type: string
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  inputs:
    my_input:
      type: {{ type_name }}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  inputs:
    my_input: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], type_name=type_name,
          value=value)).assert_success()


@pytest.mark.parametrize('macros,name,type_name,value', matrix(
    PERMUTATIONS,
    data.PARAMETER_VALUES,
    counts=(2, 2)
))
def test_template_interface_input_from_interface_type(parser, macros, name, type_name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
data_types:
  MyType:
    properties:
      my_field:
        type: string
interface_types:
  MyType:
    inputs:
      my_input:
        type: {{ type_name }}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  inputs:
    my_input: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], type_name=type_name,
          value=value)).assert_success()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_input_missing(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  inputs:
    my_input: a value
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name]),
                         adhoc_inputs=False).assert_failure()


# Operation

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_DICT_OR_STRING,
    counts=(2, 1)
))
def test_template_interface_operation_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_syntax_unsupported(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    unsupported: {}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation: {}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_from_type(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation: {}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_from_interface_type(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType:
    my_operation: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation: {}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_missing(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation: {}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_failure()


# Operation implementation

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_DICT_OR_STRING,
    counts=(2, 1)
))
def test_template_interface_operation_implementation_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    implementation: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_implementation_syntax_unsupported(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    implementation:
      unsupported: {}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_implementation_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    implementation: {}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_STRING,
    counts=(2, 1)
))
def test_template_interface_operation_implementation_primary_syntax_type(parser, macros, name,
                                                                         value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    implementation:
      primary: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_implementation_primary_short_form(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    implementation: an implementation
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_LIST,
    counts=(2, 1)
))
def test_template_interface_operation_implementation_dependencies_syntax_type(parser, macros, name,
                                                                              value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    implementation:
      dependencies: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_STRING,
    counts=(2, 1)
))
def test_template_interface_operation_implementation_dependencies_syntax_element_type(parser,
                                                                                      macros, name,
                                                                                      value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    implementation:
      dependencies:
        - {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_implementation_dependencies_syntax_empty(parser, macros,
                                                                               name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    implementation:
      dependencies: []
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


# Operation input

@pytest.mark.parametrize('macros,name,type_name,value', matrix(
    PERMUTATIONS,
    data.PARAMETER_VALUES,
    counts=(2, 2)
))
def test_template_interface_operation_input_from_type(parser, macros, name, type_name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
data_types:
  MyType:
    properties:
      my_field:
        type: string
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    inputs:
      my_input:
        type: {{ type_name }}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    inputs:
      my_input: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], type_name=type_name,
          value=value)).assert_success()


@pytest.mark.parametrize('macros,name,type_name,value', matrix(
    PERMUTATIONS,
    data.PARAMETER_VALUES,
    counts=(2, 2)
))
def test_template_interface_operation_input_from_interface_type(parser, macros, name, type_name,
                                                                value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
data_types:
  MyType:
    properties:
      my_field:
        type: string
interface_types:
  MyType:
    my_operation:
      inputs:
        my_input:
          type: {{ type_name }}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    inputs:
      my_input: {{ value }}
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], type_name=type_name,
          value=value)).assert_success()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_operation_input_missing(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call type_interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
{%- call interfaces() %}
MyInterface:
  my_operation:
    inputs:
      my_input: a value
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name]),
                         adhoc_inputs=False).assert_failure()


# Unicode

@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_template_interface_unicode(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  類型: {}
{{ name }}_types:
  類型:
{%- call type_interfaces() %}
接口:
  type: 類型
  手術:
    inputs:
      輸入:
        type: string
{% endcall %}
topology_template:
  {{ section }}:
    模板:
      type: 類型
{%- call interfaces() %}
接口:
  手術:
    inputs:
      輸入: 值
{% endcall %}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()
