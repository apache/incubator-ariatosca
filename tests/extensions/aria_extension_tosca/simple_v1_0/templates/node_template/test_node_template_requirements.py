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


# Section

@pytest.mark.parametrize('value', data.NOT_A_LIST)
def test_node_template_requirements_section_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType: {}
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements: {{ value }}
""", dict(value=value)).assert_failure()


def test_node_template_requirements_section_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType: {}
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements: []
""").assert_success()


# Requirement

@pytest.mark.parametrize('value', data.NOT_A_DICT_OR_STRING)
def test_node_template_requirement_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType: {}
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement: {{ value }}
""", dict(value=value)).assert_failure()


def test_node_template_requirement_syntax_unsupported(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            unsupported: {}
""").assert_failure()


def test_node_template_requirement_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement: {}
""").assert_success()


# Capability

def test_node_template_requirement_capability_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: unknown # neither a type nor a name
""").assert_failure()


# Capability type

def test_node_template_requirement_capability_type_same(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
""").assert_success()


def test_node_template_requirement_capability_type_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType:
    requirements:
      - my_requirement: MyType1
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType2
""").assert_success()


def test_node_template_requirement_capability_type_not_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1:
    derived_from: MyType2
  MyType2: {}
node_types:
  MyType:
    requirements:
      - my_requirement: MyType1
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType2
""").assert_failure()


def test_node_template_requirement_capability_type_short_form(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement: my_node1
    my_node1:
      type: MyType
""").assert_success()


# Capability definition name

def test_node_template_requirement_capability_name(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType1:
    requirements:
      - my_requirement: MyType
  MyType2:
    capabilities:
      my_capability: MyType
topology_template:
  node_templates:
    my_node1:
      type: MyType1
      requirements:
        - my_requirement:
            node: my_node2
            capability: my_capability
    my_node2:
      type: MyType2
""").assert_success()


def test_node_template_requirement_capability_name_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType1:
    requirements:
      - my_requirement: MyType1
  MyType2:
    capabilities:
      my_capability: MyType2
topology_template:
  node_templates:
    my_node1:
      type: MyType1
      requirements:
        - my_requirement:
            node: my_node2
            capability: my_capability
    my_node2:
      type: MyType2
""").assert_success()


def test_node_template_requirement_capability_name_not_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2: {}
node_types:
  MyType1:
    requirements:
      - my_requirement: MyType1
  MyType2:
    capabilities:
      my_capability: MyType2
topology_template:
  node_templates:
    my_node1:
      type: MyType1
      requirements:
        - my_requirement:
            node: my_node2
            capability: my_capability
    my_node2:
      type: MyType2
""").assert_failure()


# Node

def test_node_template_requirement_node_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            node: unknown
""").assert_failure()


# Node type

def test_node_template_requirement_node_type_undefined(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType1:
    requirements:
      - my_requirement: MyType1
  MyType2:
    capabilities:
      my_capability: MyType2
topology_template:
  node_templates:
    my_node:
      type: MyType1
      requirements:
        - my_requirement:
            node: MyType2
""").assert_success()


def test_node_template_requirement_node_type_same(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType1:
    requirements:
      - my_requirement:
          capability: MyType1
          node: MyType2
  MyType2:
    capabilities:
      my_capability: MyType2
topology_template:
  node_templates:
    my_node:
      type: MyType1
      requirements:
        - my_requirement:
            node: MyType2
""").assert_success()


def test_node_template_requirement_node_type_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType1:
    requirements:
      - my_requirement:
          capability: MyType1
          node: MyType2
  MyType2:
    capabilities:
      my_capability: MyType2
  MyType3:
    derived_from: MyType2
topology_template:
  node_templates:
    my_node:
      type: MyType1
      requirements:
        - my_requirement:
            node: MyType3
""").assert_success()


def test_node_template_requirement_node_type_not_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType1:
    requirements:
      - my_requirement:
          capability: MyType1
          node: MyType2
  MyType2:
    capabilities:
      my_capability: MyType2
  MyType3: {}
topology_template:
  node_templates:
    my_node:
      type: MyType1
      requirements:
        - my_requirement:
            node: MyType3
""").assert_failure()


# Node template

def test_node_template_requirement_node_template_undefined(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType1:
    requirements:
      - my_requirement: MyType1
  MyType2:
    capabilities:
      my_capability: MyType2
topology_template:
  node_templates:
    my_node1:
      type: MyType1
      requirements:
        - my_requirement:
            node: my_node2
    my_node2:
      type: MyType2
""").assert_success()


def test_node_template_requirement_node_template_same(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType1:
    requirements:
      - my_requirement:
          capability: MyType1
          node: MyType2
  MyType2:
    capabilities:
      my_capability: MyType2
topology_template:
  node_templates:
    my_node1:
      type: MyType1
      requirements:
        - my_requirement:
            node: my_node2
    my_node2:
      type: MyType2
""").assert_success()


def test_node_template_requirement_node_template_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType1:
    requirements:
      - my_requirement:
          capability: MyType1
          node: MyType2
  MyType2:
    capabilities:
      my_capability: MyType2
  MyType3:
    derived_from: MyType2
topology_template:
  node_templates:
    my_node1:
      type: MyType1
      requirements:
        - my_requirement:
            node: my_node2
    my_node2:
      type: MyType3
""").assert_success()


def test_node_template_requirement_node_template_not_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2: {}
node_types:
  MyType1:
    requirements:
      - my_requirement:
          capability: MyType1
          node: MyType2
  MyType2:
    capabilities:
      my_capability: MyType2
  MyType3: {}
topology_template:
  node_templates:
    my_node1:
      type: MyType1
      requirements:
        - my_requirement:
            node: my_node2
    my_node2:
      type: MyType3
""").assert_failure()


# Relationship

def test_node_template_requirement_relationship_syntax_unsupported(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship:
              type: MyType
              unsupported: {}
""").assert_failure()


def test_node_template_requirement_relationship_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship: {}
""").assert_success()


def test_node_template_requirement_relationship_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship: unknown
""").assert_failure()


# Relationship type

def test_node_template_requirement_relationship_type_same(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship:
              type: MyType
""").assert_success()


def test_node_template_requirement_relationship_type_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType1
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship:
              type: MyType2
""").assert_success()


def test_node_template_requirement_relationship_type_not_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType1:
    derived_from: MyType2
  MyType2: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType1
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship:
              type: MyType2
""").assert_failure()


def test_node_template_requirement_relationship_type_short_form(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship: MyType
""").assert_success()


# Relationship template

def test_node_template_requirement_relationship_template_same(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType
topology_template:
  relationship_templates:
    my_relationship:
      type: MyType
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship:
              type: my_relationship
""").assert_success()


def test_node_template_requirement_relationship_template_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType1
topology_template:
  relationship_templates:
    my_relationship:
      type: MyType2
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship:
              type: my_relationship
""").assert_success()


def test_node_template_requirement_relationship_template_not_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType1:
    derived_from: MyType2
  MyType2: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType1
topology_template:
  relationship_templates:
    my_relationship:
      type: MyType2
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship:
              type: my_relationship
""").assert_failure()


def test_node_template_requirement_relationship_template_short_form(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
relationship_types:
  MyType: {}
node_types:
  MyType:
    requirements:
      - my_requirement:
          capability: MyType
          relationship: MyType
topology_template:
  relationship_templates:
    my_relationship:
      type: MyType
  node_templates:
    my_node:
      type: MyType
      requirements:
        - my_requirement:
            capability: MyType
            relationship: my_relationship
""").assert_success()


# Unicode

def test_node_template_requirement_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  類型: {}
relationship_types:
  類型: {}
node_types:
  類型:
    requirements:
      - 需求:
          capability: 類型
          relationship: 類型
topology_template:
  relationship_templates:
    關係:
      type: 類型
  node_templates:
    節點:
      type: 類型
      requirements:
        - 需求:
            capability: 類型
            relationship: 關係
""").assert_success()
