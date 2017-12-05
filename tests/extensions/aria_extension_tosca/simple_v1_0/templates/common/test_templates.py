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


PERMUTATIONS = ('node', 'group', 'relationship', 'policy')


# Templates section

@pytest.mark.parametrize('name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_DICT
))
def test_templates_section_syntax_type(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  {{ section }}: {{ value }}
""", dict(section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_templates_section_syntax_empty(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  {{ section }}: {}
""", dict(section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


# Template

@pytest.mark.parametrize('name', PERMUTATIONS)
def test_template_syntax_unsupported(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType: {}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
      unsupported: {}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_failure()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_template_syntax_empty(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  {{ section }}:
    my_template: {} # "type" is required
""", dict(section=data.TEMPLATE_NAME_SECTIONS[name])).assert_failure()


# Description

@pytest.mark.parametrize('name,value', matrix(PERMUTATIONS, data.NOT_A_STRING))
def test_template_description_syntax_type(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType: {}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
      description: {{ value }}
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


# Type

@pytest.mark.parametrize('name,value', matrix(PERMUTATIONS, data.NOT_A_STRING))
def test_template_type_syntax_type(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  {{ section }}:
    my_template:
      type: {{ value }}
""", dict(section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_template_type_unknown(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  {{ section }}:
    my_template:
      type: UnknownType
""", dict(section=data.TEMPLATE_NAME_SECTIONS[name])).assert_failure()


# Unicode

@pytest.mark.parametrize('name', PERMUTATIONS)
def test_template_unicode(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
    類型: {}
topology_template:
  {{ section }}:
    模板:
      type: 類型
      description: 描述
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()
