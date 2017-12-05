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

from .. import data


@pytest.mark.parametrize('value', data.NOT_A_DICT)
def test_substitution_mappings_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  substitution_mappings: {{ value }}
""", dict(value=value)).assert_failure()


def test_substitution_mappings_syntax_unsupported(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType: {}
topology_template:
  substitution_mappings:
    node_type: MyType
    unsupported: {}
""").assert_failure()


def test_substitution_mappings_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  substitution_mappings: {} # "node_type" is required
""").assert_failure()


# Node type

def test_substitution_mappings_node_type_syntax_type(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  description: a description
  substitution_mappings:
    node_type: {{ value }}
""").assert_failure()


# Requirements section

@pytest.mark.parametrize('value', data.NOT_A_DICT)
def test_substitution_mappings_requirements_section_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType: {}
topology_template:
  substitution_mappings:
    node_type: MyType
    requirements: {{ value }}
""", dict(value=value)).assert_failure()


def test_substitution_mappings_requirements_section_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType: {}
topology_template:
  substitution_mappings:
    node_type: MyType
    requirements: {}
""").assert_success()


# Requirement

@pytest.mark.parametrize('value', data.NOT_A_LIST_OF_TWO)
def test_substitution_mappings_requirement_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
topology_template:
  substitution_mappings:
    node_type: MyType
    requirements:
      my_requirement: {{ value }}
""", dict(value=value)).assert_failure()


def test_substitution_mappings_requirement_same(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
  MyInternalType:
    requirements:
      - my_internal_requirement:
          capability: MyType
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    requirements:
      my_requirement: [ my_template, my_internal_requirement ]
""").assert_success()


def test_substitution_mappings_requirement_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType1
  MyInternalType:
    requirements:
      - my_internal_requirement:
          capability: MyType2
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    requirements:
      my_requirement: [ my_template, my_internal_requirement ]
""").assert_success()


def test_substitution_mappings_requirement_bad(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType1
  MyInternalType:
    requirements:
      - my_internal_requirement:
          capability: MyType2
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    requirements:
      my_requirement: [ my_template, my_internal_requirement ]
""").assert_failure()


def test_substitution_mappings_requirement_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
  MyInternalType:
    requirements:
      - my_internal_requirement:
          capability: MyType
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    requirements:
      unknown: [ my_template, my_internal_requirement ]
""").assert_failure()


def test_substitution_mappings_requirement_unknown_mapped_template(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
  MyInternalType:
    requirements:
      - my_internal_requirement:
          capability: MyType
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    requirements:
      my_requirement: [ unknown, my_internal_requirement ]
""").assert_failure()


def test_substitution_mappings_requirement_unknown_mapped_requirement(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
  MyInternalType:
    requirements:
      - my_internal_requirement:
          capability: MyType
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    requirements:
      my_requirement: [ my_template, unknown ]
""").assert_failure()


# Capabilities section

@pytest.mark.parametrize('value', data.NOT_A_DICT)
def test_substitution_mappings_capabilities_section_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType: {}
topology_template:
  substitution_mappings:
    node_type: MyType
    capabilities: {{ value }}
""", dict(value=value)).assert_failure()


def test_substitution_mappings_capabilities_section_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType: {}
topology_template:
  substitution_mappings:
    node_type: MyType
    capabilities: {}
""").assert_success()


# Capability

@pytest.mark.parametrize('value', data.NOT_A_LIST_OF_TWO)
def test_substitution_mappings_capability_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability: MyType
topology_template:
  substitution_mappings:
    node_type: MyType
    capabilities:
      my_capability: {{ value }}
""", dict(value=value)).assert_failure()


def test_substitution_mappings_capability_same(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability: MyType
  MyInternalType:
    capabilities:
      my_internal_capability: MyType
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    capabilities:
      my_capability: [ my_template, my_internal_capability ]
""").assert_success()


def test_substitution_mappings_capability_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType:
    capabilities:
      my_capability: MyType1
  MyInternalType:
    capabilities:
      my_internal_capability: MyType2
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    capabilities:
      my_capability: [ my_template, my_internal_capability ]
""").assert_success()


def test_substitution_mappings_capability_bad(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2: {}
node_types:
  MyType:
    capabilities:
      my_capability: MyType1
  MyInternalType:
    capabilities:
      my_internal_capability: MyType2
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    capabilities:
      my_capability: [ my_template, my_internal_capability ]
""").assert_failure()


def test_substitution_mappings_capability_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability: MyType
  MyInternalType:
    capabilities:
      my_internal_capability: MyType
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    capabilities:
      unknown: [ my_template, my_internal_capability ]
""").assert_failure()


def test_substitution_mappings_capability_unknown_mapped_template(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability: MyType
  MyInternalType:
    capabilities:
      my_internal_capability: MyType
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    capabilities:
      my_capability: [ unknown, my_internal_capability ]
""").assert_failure()


def test_substitution_mappings_capability_unknown_mapped_capability(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability: MyType
  MyInternalType:
    capabilities:
      my_internal_capability: MyType
topology_template:
  node_templates:
    my_template:
      type: MyInternalType
  substitution_mappings:
    node_type: MyType
    capabilities:
      my_capability: [ my_template, unknown ]
""").assert_failure()
