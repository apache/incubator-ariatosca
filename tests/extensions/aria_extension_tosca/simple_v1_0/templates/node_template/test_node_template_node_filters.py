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


# Node filter in node template
MAIN_MACROS = """
{% macro additions() %}
node_types:
  MyType1: {}
  MyType2:
    properties:
      my_property:
        type: string
{%- endmacro %}
{% macro node_filter() %}
      node_filter: {{ caller()|indent(8) }}
{%- endmacro %}
"""


# Node filter in requirement
REQUIREMENT_MACROS = """
{% macro additions() %}
capability_types:
  MyType:
    properties:
      my_property:
        type: string
node_types:
  MyType1:
    requirements:
      - my_requirement:
          capability: MyType
  MyType2:
    properties:
      my_property:
        type: string
    capabilities:
      my_capability: MyType
{%- endmacro %}
{% macro node_filter() %}
      requirements:
        - my_requirement:
            node: MyType2
            node_filter: {{ caller()|indent(14) }}
{%- endmacro %}
"""

MACROS = {
    'main': MAIN_MACROS,
    'requirement': REQUIREMENT_MACROS
}

PERMUTATIONS = (
    'main', 'requirement'
)


@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_DICT))
def test_node_template_node_filter_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() -%}
{{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_syntax_unsupported(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
unsupported: {}
{% endcall %}
""").assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_syntax_empty(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() -%}
{}
{% endcall %}
""").assert_success()


# Properties section

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_LIST))
def test_node_template_node_filter_properties_section_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
properties: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_properties_section_syntax_empty(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
properties: []
{% endcall %}
""").assert_success()


# Capabilities section

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_LIST))
def test_node_template_node_filter_capabilities_section_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
capabilities: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_capabilities_section_syntax_empty(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
capabilities: []
{% endcall %}
""").assert_success()


# Capability

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_DICT))
def test_node_template_node_filter_capability_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
capabilities:
  - my_capability: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_capability_syntax_unsupported(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
capabilities:
  - my_capability:
      unsupported: {}
{% endcall %}
""").assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_capability_syntax_empty(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
capabilities:
  - my_capability: {}
{% endcall %}
""").assert_success()


# Capability properties section

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_LIST))
def test_node_template_node_filter_capability_properties_section_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
capabilities:
  - my_capability:
      properties: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_capability_properties_section_syntax_empty(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call node_filter() %}
capabilities:
  - my_capability:
      properties: []
{% endcall %}
""").assert_success()


# Unicode

def test_node_template_node_filter_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  類型: {}
node_types:
  類型一:
    requirements:
      - 需求:
          capability: 類型
  類型二:
    properties:
      屬性:
        type: string
    capabilities:
      能力: 類型
topology_template:
  node_templates:
    模板:
      type: 類型一
      node_filter:
        properties:
          - 屬性: { equal: 值 }
        capabilities:
          - my_capability:
               properties:
                 - 屬性: { equal: 值 }
      requirements:
        - 需求:
            node: 類型二
            node_filter:
              properties:
                - 屬性: { equal: 值 }
              capabilities:
                - 能力:
                    properties:
                      - 屬性: { equal: 值 }
""").assert_success()
