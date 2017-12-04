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
Here we are testing not only artifacts attached to node templates, but also artifacts attached to
node types. The reason is that artifacts attached node types use the same property assignment
(rather than definition) syntax we see in templates.
"""

import pytest

from ... import data
from ......mechanisms.utils import matrix


# Artifacts attached to a node template
TEMPLATE_MACROS = """
{% macro artifacts() %}
node_types:
  MyType: {}
topology_template:
  node_templates:
    my_node:
      type: MyType
      artifacts: {{ caller()|indent(8) }}
{%- endmacro %}
"""

# Artifacts attached to a node type
TYPE_MACROS = """
{% macro artifacts() %}
node_types:
  MyType:
    artifacts: {{ caller()|indent(6) }}
{%- endmacro %}
"""

MACROS = {
    'template': TEMPLATE_MACROS,
    'type': TYPE_MACROS
}

PERMUTATIONS = (
    'template',
    'type'
)



# Artifacts section

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_DICT))
def test_node_template_artifacts_section_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{%- call artifacts() -%}
{{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifacts_section_syntax_empty(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{%- call artifacts() -%}
{}
{% endcall %}
""").assert_success()


# Artifact

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_DICT))
def test_node_template_artifact_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{%- call artifacts() %}
my_artifact: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifact_syntax_unsupported(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{%- call artifacts() %}
my_artifact:
  type: MyType
  unsupported: {}
{% endcall %}
""").assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifact_syntax_empty(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{%- call artifacts() %}
my_artifact: {} # "type" and "file" are required
{% endcall %}
""").assert_failure()


# Type

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_STRING))
def test_node_template_artifact_type_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{%- call artifacts() %}
my_artifact:
  type: {{ value }}
  file: a file
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifact_type_unknown(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
{%- call artifacts() %}
my_artifact:
  type: UnknownType
  file: a file
{% endcall %}
""").assert_failure()


# File

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_STRING))
def test_node_template_artifact_file_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
{%- call artifacts() %}
my_artifact:
  type: MyType
  file: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifact_file(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
{%- call artifacts() %}
my_artifact:
  type: MyType
  file: a file
{% endcall %}
""").assert_success()


# Description

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_STRING))
def test_node_template_artifact_description_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
{%- call artifacts() %}
my_artifact:
  type: MyType
  file: a file
  description: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifact_description(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
{%- call artifacts() %}
my_artifact:
  type: MyType
  file: a file
  description: a description
{% endcall %}
""").assert_success()


# Repository

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_STRING))
def test_node_template_artifact_repository_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
{%- call artifacts() %}
my_artifact:
  type: MyType
  file: a file
  repository: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifact_repository_unknown(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
{%- call artifacts() %}
my_artifact:
  type: MyType
  file: a file
  repository: unknown
{% endcall %}
""").assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifact_repository(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: a url
artifact_types:
  MyType: {}
{%- call artifacts() %}
my_artifact:
  type: MyType
  file: a file
  repository: my_repository
{% endcall %}
""").assert_success()


# Deploy path

@pytest.mark.parametrize('macros,value', matrix(PERMUTATIONS, data.NOT_A_STRING))
def test_node_template_artifact_deploy_path_syntax_type(parser, macros, value):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
{%- call artifacts() %}
my_artifact:
  type: MyType
  file: a file
  deploy_path: {{ value }}
{% endcall %}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifact_deploy_path(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
{%- call artifacts() %}
my_artifact:
  type: MyType
  file: a file
  deploy_path: a path
{% endcall %}
""").assert_success()


# Unicode

@pytest.mark.parametrize('macros', PERMUTATIONS)
def test_node_template_artifact_unicode(parser, macros):
    parser.parse_literal(MACROS[macros] + """
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  知識庫:
    url: 網址
artifact_types:
  類型: {}
{%- call artifacts() %}
神器:
  type: 類型
  file: 文件
  repository: 知識庫
  deploy_path: 路徑
{% endcall %}
""").assert_success()
