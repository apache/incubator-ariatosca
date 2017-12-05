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


# Targets

@pytest.mark.parametrize('value', data.NOT_A_LIST)
def test_policy_targets_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
policy_types:
  MyType: {}
topology_template:
  policies:
    my_policy:
      type: MyType
      targets: {{ value }}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_policy_targets_syntax_element_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
policy_types:
  MyType: {}
topology_template:
  policies:
    my_policy:
      type: MyType
      targets: [ {{ value }} ]
""", dict(value=value)).assert_failure()


def test_policy_targets_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
policy_types:
  MyType: {}
topology_template:
  policies:
    my_policy:
      type: MyType
      targets: []
""").assert_success()


def test_policy_targets_nodes(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType1: {}
  MyType2: {}
policy_types:
  MyType:
    targets: [ MyType1, MyType2 ]
topology_template:
  node_templates:
    my_node1:
      type: MyType1
    my_node2:
      type: MyType2
  policies:
    my_policy:
      type: MyType
      targets: [ my_node1, my_node2 ]
""").assert_success()


def test_policy_targets_nodes_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
policy_types:
  MyType:
    targets: [ MyType1 ]
topology_template:
  node_templates:
    my_node:
      type: MyType2
  policies:
    my_policy:
      type: MyType
      targets: [ my_node ]
""").assert_success()


def test_policy_targets_nodes_not_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType1:
    derived_from: MyType2
  MyType2: {}
policy_types:
  MyType:
    targets: [ MyType1 ]
topology_template:
  node_templates:
    my_node:
      type: MyType2
  policies:
    my_policy:
      type: MyType
      targets: [ my_node ]
""").assert_failure()


def test_policy_targets_groups(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType1: {}
  MyType2: {}
policy_types:
  MyType:
    targets: [ MyType1, MyType2 ]
topology_template:
  groups:
    my_group1:
      type: MyType1
    my_group2:
      type: MyType2
  policies:
    my_policy:
      type: MyType
      targets: [ my_group1, my_group2 ]
""").assert_success()


def test_policy_targets_groups_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
policy_types:
  MyType:
    targets: [ MyType1 ]
topology_template:
  groups:
    my_group:
      type: MyType2
  policies:
    my_policy:
      type: MyType
      targets: [ my_group ]
""").assert_success()


def test_policy_targets_groups_not_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
  MyType1: {}
  MyType1:
    derived_from: MyType2
  MyType2: {}
policy_types:
  MyType:
    targets: [ MyType1 ]
topology_template:
  groups:
    my_group:
      type: MyType2
  policies:
    my_policy:
      type: MyType
      targets: [ my_group ]
""").assert_failure()


def test_policy_targets_nodes_and_groups(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyNodeType: {}
group_types:
  MyGroupType: {}
policy_types:
  MyType:
    targets: [ MyNodeType, MyGroupType ]
topology_template:
  node_templates:
    my_node:
      type: MyNodeType
  groups:
    my_group:
      type: MyGroupType
  policies:
    my_policy:
      type: MyType
      targets: [ my_node, my_group ]
""").assert_success()


def test_policy_targets_ambiguous(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyNodeType: {}
group_types:
  MyGroupType: {}
policy_types:
  MyType:
    targets: [ MyNodeType, MyGroupType ]
topology_template:
  node_templates:
    my_template:
      type: MyNodeType
  groups:
    my_template:
      type: MyGroupType
  policies:
    my_policy:
      type: MyType
      targets: [ my_template ]
""").assert_success()


def test_policy_targets_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
policy_types:
  MyType: {}
topology_template:
  policies:
    my_policy:
      type: MyType
      targets: [ unknown ]
""").assert_failure()


# Unicode

def test_policy_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  類型: {}
policy_types:
  類型:
    targets: [ 類型 ]
topology_template:
  node_templates:
    節點:
      type: 類型
  policies:
    政策:
      type: 類型
      targets: [ 節點 ]
""").assert_success()
