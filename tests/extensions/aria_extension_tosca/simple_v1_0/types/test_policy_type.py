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
def test_policy_type_targets_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
policy_types:
  MyType:
    targets: {{ value }}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_policy_type_targets_syntax_element_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
policy_types:
  MyType:
    targets: [ {{ value }} ]
""", dict(value=value)).assert_failure()


def test_policy_type_targets_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
policy_types:
  MyType:
    targets: []
""").assert_success()


def test_policy_type_targets_nodes(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType1: {}
  MyType2: {}
policy_types:
  MyType:
    targets: [ MyType1, MyType2 ]
""").assert_success()


def test_policy_type_targets_groups(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType1: {}
  MyType2: {}
policy_types:
  MyType:
    targets: [ MyType1, MyType2 ]
""").assert_success()


def test_policy_type_targets_nodes_and_groups(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType1: {}
group_types:
  MyType2: {}
policy_types:
  MyType:
    targets: [ MyType1, MyType2 ]
""").assert_success()


def test_policy_type_targets_ambiguous(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType: {}
group_types:
  MyType: {}
policy_types:
  MyType:
    targets: [ MyType ]
""").assert_success()


def test_policy_type_targets_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
policy_types:
  MyType:
    targets: [ UnknownType ]
""").assert_failure()


# Unicode

def test_policy_type_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  類型一: {}
  類型二: {}
policy_types:
  類型:
    targets: [ 類型一, 類型二 ]
""").assert_success()
