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
Unified testing for properties, attributes, and inputs.

Additional tests for properties are in test_type_properties.py.

Note: artifact definitions within node types use parameter assignments rather than definitions, and
thus are tested not here but under test_template_parameters.py.
"""

import pytest

from ... import data
from ......mechanisms.utils import matrix


# Defining parameters at a type
MAIN_MACROS = """
{% macro additions(section=True) %}
{%- if section %}
{{ name }}_types:
{%- endif %}
{%- endmacro %}
{% macro parameters(t='MyType', d=None) %}
  {{ t }}:
{%- if d %}
    derived_from: {{ d }}
{%- endif %}
    {{ parameter_section }}: {{ caller()|indent(6) }}
{%- endmacro %}
"""

# Defining parameters at a nested type (e.g. inputs of an operation within an interface type)
NESTED_MACROS = """
{% macro additions(section=True) %}
{%- if section %}
{{ name }}_types:
{%- endif %}
{%- endmacro %}
{% macro parameters(t='MyType', d=None) %}
  {{ t }}:
{%- if d %}
    derived_from: {{ d }}
{%- endif %}
    nested:
      {{ parameter_section }}: {{ caller()|indent(8) }}
{%- endmacro %}
"""

# Defining inputs at an interface of a type
INTERFACE_MACROS = """
{% macro additions(section=True) %}
interface_types:
  MyType: {}
{%- if section %}
{{ name }}_types:
{%- endif %}
{%- endmacro %}
{% macro parameters(t='MyType', d=None) %}
  {{ t }}:
{%- if d %}
    derived_from: {{ d }}
{%- endif %}
    interfaces:
      my_interface:
        type: MyType
        {{ parameter_section }}: {{ caller()|indent(10) }}
{%- endmacro %}
"""

# Defining inputs at an operation of an interface of a type
OPERATION_MACROS = """
{% macro additions(section=True) %}
interface_types:
  MyType: {}
{%- if section %}
{{ name }}_types:
{%- endif %}
{%- endmacro %}
{% macro parameters(t='MyType', d=None) %}
  {{ t }}:
{%- if d %}
    derived_from: {{ d }}
{%- endif %}
    interfaces:
      my_interface:
        type: MyType
        my_operation:
          {{ parameter_section }}: {{ caller()|indent(12) }}
{%- endmacro %}
"""

# Defining inputs at an interface of a relationship of a requirement of a node type
RELATIONSHIP_INTERFACE_MACROS = """
{% macro additions(section=True) %}
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
interface_types:
  MyType: {}
{%- if section %}
{{ name }}_types:
{%- endif %}
{%- endmacro %}
{% macro parameters(t='MyType', d=None) %}
  {{ t }}:
{%- if d %}
    derived_from: {{ d }}
{%- endif %}
    requirements:
      - my_requirement:
          capability: MyType
          relationship:
            type: MyType
            interfaces:
              my_interface:
                type: MyType
                {{ parameter_section }}: {{ caller()|indent(18) }}
{%- endmacro %}
"""

# Defining inputs at an operation of an interface of a relationship of a requirement of a node type
RELATIONSHIP_OPERATION_MACROS = """
{% macro additions(section=True) %}
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
interface_types:
  MyType: {}
{%- if section %}
{{ name }}_types:
{%- endif %}
{%- endmacro %}
{% macro parameters(t='MyType', d=None) %}
  {{ t }}:
{%- if d %}
    derived_from: {{ d }}
{%- endif %}
    requirements:
      - my_requirement:
          capability: MyType
          relationship:
            type: MyType
            interfaces:
              my_interface:
                type: MyType
                my_operation:
                  {{ parameter_section }}: {{ caller()|indent(20) }}
{%- endmacro %}
"""

# Defining parameters at a capability of a node type
CAPABILITY_MACROS = """
{% macro additions(section=True) %}
capability_types:
  MyType: {}
{%- if section %}
{{ name }}_types:
{%- endif %}
{%- endmacro %}
{% macro parameters(t='MyType', d=None) %}
  {{ t }}:
{%- if d %}
    derived_from: {{ d }}
{%- endif %}
    capabilities:
      my_capability:
        type: MyType
        {{ parameter_section }}: {{ caller()|indent(10) }}
{%- endmacro %}
"""

# Defining inputs/outputs at a topology template
TOPOLOGY_MACROS = """
{% macro additions(section=None) %}
topology_template:
{%- endmacro %}
{% macro parameters(t=None) %}
  {{ parameter_section }}: {{ caller()|indent(4) }}
{%- endmacro %}
"""


MACROS = {
    'main': MAIN_MACROS,
    'nested': NESTED_MACROS,
    'interface': INTERFACE_MACROS,
    'operation': OPERATION_MACROS,
    'relationship-interface': RELATIONSHIP_INTERFACE_MACROS,
    'relationship-operation': RELATIONSHIP_OPERATION_MACROS,
    'capability': CAPABILITY_MACROS,
    'topology': TOPOLOGY_MACROS
}

PERMUTATIONS_TYPE_REQUIRED = (
    ('main', 'node', 'properties'),
    ('main', 'node', 'attributes'),
    ('main', 'group', 'properties'),
    ('main', 'relationship', 'properties'),
    ('main', 'relationship', 'attributes'),
    ('main', 'capability', 'properties'),
    ('main', 'capability', 'attributes'),
    ('main', 'policy', 'properties'),
    ('main', 'interface', 'inputs'),
    ('main', 'artifact', 'properties'),
    ('main', 'data', 'properties'),
    ('nested', 'interface', 'inputs'),
    ('interface', 'node', 'inputs'),
    ('interface', 'group', 'inputs'),
    ('interface', 'relationship', 'inputs'),
    ('operation', 'node', 'inputs'),
    ('operation', 'group', 'inputs'),
    ('operation', 'relationship', 'inputs'),
    ('relationship-interface', 'node', 'inputs'),
    ('relationship-operation', 'node', 'inputs'),
    ('capability', 'node', 'properties'),
    ('capability', 'node', 'attributes'),
    ('topology', None, 'inputs')
)

PERMUTATIONS = PERMUTATIONS_TYPE_REQUIRED + (
    ('topology', None, 'outputs'),
)


# Parameters section

@pytest.mark.parametrize('macros,name,parameter_section,value', matrix(
    PERMUTATIONS,
    data.NOT_A_DICT,
    counts=(3, 1)
))
def test_type_parameters_section_syntax_type(parser, macros, name, parameter_section, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() -%}
{{ value }}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameters_section_syntax_empty(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() -%}
{}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()


# Parameter

@pytest.mark.parametrize('macros,name,parameter_section,value', matrix(
    PERMUTATIONS,
    data.NOT_A_DICT,
    counts=(3, 1)
))
def test_type_parameter_syntax_type(parser, macros, name, parameter_section, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter: {{ value }}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS_TYPE_REQUIRED)
def test_type_parameter_syntax_empty(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter: {} # type is required
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_syntax_unsupported(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  unsupported: {}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_failure()


# Description

@pytest.mark.parametrize('macros,name,parameter_section,value', matrix(
    PERMUTATIONS,
    data.NOT_A_STRING,
    counts=(3, 1)
))
def test_type_parameter_description_syntax_type(parser, macros, name, parameter_section, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  description: {{ value }}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, value=value)).assert_failure()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_description(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  description: a description
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()


# Default

@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_default(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  default: a string
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_default_bad(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: integer
  default: a string
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_failure()


# Status

@pytest.mark.parametrize('macros,name,parameter_section,value', matrix(
    PERMUTATIONS,
    data.STATUSES,
    counts=(3, 1)
))
def test_type_parameter_status(parser, macros, name, parameter_section, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  status: {{ value }}
{% endcall %}
""", dict(name=name, parameter_section=parameter_section, value=value)).assert_success()


@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_status_bad(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters() %}
my_parameter:
  type: string
  status: not a status
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_failure()


# Unicode

@pytest.mark.parametrize('macros,name,parameter_section', PERMUTATIONS)
def test_type_parameter_unicode(parser, macros, name, parameter_section):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
{%- call parameters('類型') %}
參數:
  type: string
  description: 描述
  default: 值
  status: supported
{% endcall %}
""", dict(name=name, parameter_section=parameter_section)).assert_success()
