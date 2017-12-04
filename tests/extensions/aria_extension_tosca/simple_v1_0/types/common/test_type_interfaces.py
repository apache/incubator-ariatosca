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


# Interfaces defined at a type
MAIN_MACROS = """
{% macro additions() %}
{%- endmacro %}
{% macro interfaces() %}
    interfaces: {{ caller()|indent(6) }}
{%- endmacro %}
"""

# Interfaces defined (added/overridden) at a relationship of a requirement within a node type
RELATIONSHIP_MACROS = """
{% macro additions() %}
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
{%- endmacro %}
{% macro interfaces() %}
    requirements:
      - my_requirement:
          capability: MyType
          relationship:
            type: MyType
            interfaces: {{ caller()|indent(14) }}
{%- endmacro %}
"""

MACROS = {
    'main': MAIN_MACROS,
    'relationship': RELATIONSHIP_MACROS
}

PERMUTATIONS = (
    ('main', 'node'),
    ('main', 'group'),
    ('main', 'relationship'),
    ('relationship', 'node')
)

PERMUTATIONS_NO_RELATIONSHIP = tuple(
    (macros, name)
    for macros, name in PERMUTATIONS
    if macros != 'relationship'
)


# Interfaces section

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS, data.NOT_A_DICT,
    counts=(2, 1)
))
def test_type_interfaces_section_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() -%}
{{ value }}
{% endcall %}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interfaces_section_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{{ name }}_types:
  MyType:
{%- call interfaces() -%}
{}
{% endcall %}
""", dict(name=name)).assert_success()


# Interface

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS, data.NOT_A_DICT,
    counts=(2, 1)
))
def test_type_interface_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface: {{ value }}
{% endcall %}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface: {} # "type" is required
{% endcall %}
""", dict(name=name)).assert_failure()


# Type

@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_type_override(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
{{ name }}_types:
  MyType1:
{%- call interfaces() %}
MyInterface:
  type: MyType1
{% endcall %}
  MyType2:
    derived_from: MyType1
{%- call interfaces() %}
MyInterface:
  type: MyType2
{% endcall %}
""", dict(name=name)).assert_success()


# We are skipping relationship interfaces, because node requirements can be overridden completely
@pytest.mark.parametrize('macros,name', PERMUTATIONS_NO_RELATIONSHIP)
def test_type_interface_type_override_bad(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType1: {}
  MyType2: {}
{{ name }}_types:
  MyType1:
{%- call interfaces() %}
MyInterface:
  type: MyType1
{% endcall %}
  MyType2:
    derived_from: MyType1
{%- call interfaces() %}
MyInterface:
  type: MyType2
{% endcall %}
""", dict(name=name)).assert_failure()


# Operation

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS, data.NOT_A_DICT_OR_STRING,
    counts=(2, 1)
))
def test_type_interface_operation_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation: {{ value }}
{% endcall %}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_operation_syntax_unsupported(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    unsupported: {}
{% endcall %}
""", dict(name=name)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_operation_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation: {}
{% endcall %}
""", dict(name=name)).assert_success()


# Operation description

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS, data.NOT_A_STRING,
    counts=(2, 1)
))
def test_type_interface_operation_description_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    description: {{ value }}
{% endcall %}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_operation_description(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    description: a description
{% endcall %}
""", dict(name=name)).assert_success()


# Operation implementation

@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS, data.NOT_A_DICT_OR_STRING,
    counts=(2, 1)
))
def test_type_interface_operation_implementation_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    implementation: {{ value }}
{% endcall %}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_operation_implementation_syntax_unsupported(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    implementation:
      unsupported: {}
{% endcall %}
""", dict(name=name)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_operation_implementation_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    implementation: {}
{% endcall %}
""", dict(name=name)).assert_success()


@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS, data.NOT_A_STRING,
    counts=(2, 1)
))
def test_type_interface_operation_implementation_primary_syntax_type(parser, macros, name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    implementation:
      primary: {{ value }}
{% endcall %}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_operation_implementation_primary_short_form(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    implementation: an implementation
{% endcall %}
""", dict(name=name)).assert_success()


@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS, data.NOT_A_LIST,
    counts=(2, 1)
))
def test_type_interface_operation_implementation_dependencies_syntax_type(parser, macros, name,
                                                                          value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    implementation:
      primary: an implementation
      dependencies: {{ value }}
{% endcall %}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name,value', matrix(
    PERMUTATIONS, data.NOT_A_STRING,
    counts=(2, 1)
))
def test_type_interface_operation_implementation_dependencies_syntax_element_type(parser, macros,
                                                                                  name, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    implementation:
      primary: an implementation
      dependencies:
        - {{ value }}
{% endcall %}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_operation_implementation_dependencies_syntax_empty(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  MyType: {}
{{ name }}_types:
  MyType:
{%- call interfaces() %}
MyInterface:
  type: MyType
  my_operation:
    implementation:
      primary: an implementation
      dependencies: []
{% endcall %}
""", dict(name=name)).assert_success()


# Unicode

@pytest.mark.parametrize('macros,name', PERMUTATIONS)
def test_type_interface_unicode(parser, macros, name):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
interface_types:
  類型: {}
{{ name }}_types:
  類型:
{%- call interfaces() %}
接口:
  type: 類型
  手術:
    implementation: 履行
{% endcall %}
""", dict(name=name)).assert_success()
