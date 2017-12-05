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
Compare with test_type_properties.py. Note that though the constraints are the same, their syntax
is very different, making it difficult to test all permutations together.
"""


import pytest

from ... import data
from ......mechanisms.utils import matrix


# Properties for node filter in node template
MAIN_MACROS = """
{% macro additions() %}
data_types:
  MyType:
    properties:
      my_field:
        type: string
node_types:
  MyType1: {}
  MyType2:
    properties:
      data_property:
        type: MyType
      string_property:
        type: string
{%- endmacro %}
{% macro properties() %}
      node_filter:
        properties: {{ caller()|indent(10) }}
{%- endmacro %}
"""

# Capability properties for node filter in node template
MAIN_CAPABILITY_MACROS = """
{% macro additions() %}
data_types:
  MyType:
    properties:
      my_field:
        type: string
capability_types:
  MyType:
    properties:
      data_property:
        type: MyType
      string_property:
        type: string
node_types:
  MyType1: {}
  MyType2:
    capabilities:
      my_capability: MyType
{%- endmacro %}
{% macro properties() %}
      node_filter:
        capabilities:
          - my_capability:
              properties: {{ caller()|indent(16) }}
{%- endmacro %}
"""

# Properties for node filter in requirement
REQUIREMENT_MACROS = """
{% macro additions() %}
data_types:
  MyType:
    properties:
      my_field:
        type: string
capability_types:
  MyType: {}
node_types:
  MyType1:
    requirements:
      - my_requirement:
          capability: MyType
  MyType2:
    properties:
      data_property:
        type: MyType
      string_property:
        type: string
    capabilities:
      my_capability: MyType
{%- endmacro %}
{% macro properties() %}
      requirements:
        - my_requirement:
            node: MyType2
            node_filter:
              properties: {{ caller()|indent(16) }}
{%- endmacro %}
"""

# Capability properties for node filter in requirement
REQUIREMENT_CAPABILITY_MACROS = """
{% macro additions() %}
data_types:
  MyType:
    properties:
      my_field:
        type: string
capability_types:
  MyType:
    properties:
      data_property:
        type: MyType
      string_property:
        type: string
node_types:
  MyType1:
    requirements:
      - my_requirement:
          capability: MyType
  MyType2:
    capabilities:
      my_capability: MyType
{%- endmacro %}
{% macro properties() %}
      requirements:
        - my_requirement:
            node: MyType2
            node_filter:
              capabilities:
                - my_capability:
                    properties: {{ caller()|indent(22) }}
{%- endmacro %}
"""

MACROS = {
    'main': MAIN_MACROS,
    'requirement': REQUIREMENT_MACROS,
    'main-capability': MAIN_CAPABILITY_MACROS,
    'requirement-capability': REQUIREMENT_CAPABILITY_MACROS
}

PERMUTATIONS = (
    'main', 'requirement', 'main-capability', 'requirement-capability'
)



@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_DICT_WITH_ONE_KEY))
def test_node_template_node_filter_constraints_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- data_property: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_constraints_syntax_empty(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- data_property: {}
{% endcall %}
""").assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_constraints_syntax_unsupported(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- data_property: { unsupported: a string }
{% endcall %}
""").assert_failure()


@pytest.mark.parametrize('macros,constraint', matrix(PERMUTATIONS, data.CONSTRAINTS_WITH_VALUE))
def test_node_template_node_filter_constraints_with_value(parser, macros, constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- data_property: { {{ constraint }}: {my_field: a string} }
{% endcall %}
""", dict(constraint=constraint)).assert_success()


@pytest.mark.parametrize('macros,constraint', matrix(PERMUTATIONS,
                                                     data.CONSTRAINTS_WITH_VALUE_LIST))
def test_node_template_node_filter_constraints_with_value_list(parser, macros, constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- data_property: { {{ constraint }}: [ {my_field: a}, {my_field: b}, {my_field: c} ] }
{% endcall %}
""", dict(constraint=constraint)).assert_success()


@pytest.mark.parametrize('macros,constraint', matrix(PERMUTATIONS,
                                                     data.CONSTRAINTS_WITH_VALUE_RANGE))
def test_node_template_node_filter_constraints_with_value_range(parser, macros, constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- data_property: { {{ constraint }}: [ {my_field: string a}, {my_field: string b} ] }
{% endcall %}
""", dict(constraint=constraint)).assert_success()


@pytest.mark.parametrize('macros,constraint', matrix(PERMUTATIONS,
                                                     data.CONSTRAINTS_WITH_VALUE_RANGE))
def test_node_template_node_filter_constraints_with_value_range_too_many(parser, macros,
                                                                         constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- data_property: { {{ constraint }}: [ {my_field: a}, {my_field: b}, {my_field: c} ] }
{% endcall %}
""", dict(constraint=constraint)).assert_failure()


@pytest.mark.parametrize('macros,constraint', matrix(PERMUTATIONS,
                                                     data.CONSTRAINTS_WITH_VALUE_RANGE))
def test_node_template_node_filter_constraints_with_value_range_bad(parser, macros, constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- data_property: { {{ constraint }}: [ {my_field: string b}, {my_field: string a} ] }
{% endcall %}
""", dict(constraint=constraint)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_constraints_pattern(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- string_property: { pattern: ^pattern$ }
{% endcall %}
""").assert_success()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_node_filter_constraints_pattern_bad(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- string_property: { pattern: ( }
{% endcall %}
""").assert_failure()


@pytest.mark.parametrize('macros,constraint', matrix(PERMUTATIONS,
                                                     data.CONSTRAINTS_WITH_VALUE_NON_NEGATIVE_INT))
def test_node_template_node_filter_constraints_with_value_integer(parser, macros, constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- string_property: { {{ constraint }}: 1 }
{% endcall %}
""", dict(constraint=constraint)).assert_success()


@pytest.mark.parametrize('macros,constraint', matrix(PERMUTATIONS,
                                                     data.CONSTRAINTS_WITH_VALUE_NON_NEGATIVE_INT))
def test_node_template_node_filter_constraints_with_value_integer_bad(parser, macros, constraint):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{{- additions() }}
topology_template:
  node_templates:
    my_node:
      type: MyType1
{%- call properties() %}
- string_property: { {{ constraint }}: -1 }
{% endcall %}
""", dict(constraint=constraint)).assert_failure()
