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


# Members

@pytest.mark.parametrize('value', data.NOT_A_LIST)
def test_group_members_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType: {}
topology_template:
  groups:
    my_group:
      type: MyType
      members: {{ value }}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_group_members_syntax_element_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType: {}
topology_template:
  groups:
    my_group:
      type: MyType
      members: [ {{ value }} ]
""", dict(value=value)).assert_failure()


def test_group_members_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType: {}
topology_template:
  groups:
    my_group:
      type: MyType
      members: []
""").assert_success()


def test_group_members(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType1: {}
  MyType2: {}
group_types:
  MyType:
    members: [ MyType1, MyType2 ]
topology_template:
  node_templates:
    my_node1:
      type: MyType1
    my_node2:
      type: MyType2
  groups:
    my_group:
      type: MyType
      members: [ my_node1, my_node2 ]
""").assert_success()


def test_group_members_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
group_types:
  MyType:
    members: [ MyType1 ]
topology_template:
  node_templates:
    my_node:
      type: MyType2
  groups:
    my_group:
      type: MyType
      members: [ my_node ]
""").assert_success()


def test_group_members_not_derived(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType1: {}
  MyType2: {}
group_types:
  MyType:
    members: [ MyType1 ]
topology_template:
  node_templates:
    my_node:
      type: MyType2
  groups:
    my_group:
      type: MyType
      members: [ my_node ]
""").assert_failure()


def test_group_members_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType: {}
topology_template:
  groups:
    my_group:
      type: MyType
      members: [ unknown ]
""").assert_failure()


# Unicode

def test_group_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  類型: {}
group_types:
  類型:
    members: [ 類型 ]
topology_template:
  node_templates:
    節點:
      type: 類型
  groups:
    政策:
      type: 類型
      members: [ 節點 ]
""").assert_success()
