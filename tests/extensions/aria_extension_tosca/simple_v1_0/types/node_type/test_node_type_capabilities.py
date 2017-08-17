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


# Capabilities section

@pytest.mark.parametrize('value', data.NOT_A_DICT)
def test_node_type_capabilities_section_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    capabilities: {{ value }}
""", dict(value=value)).assert_failure()


def test_node_type_capabilities_section_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    capabilities: {}
""").assert_success()


# Capability

@pytest.mark.parametrize('value', data.NOT_A_DICT)
def test_node_type_capability_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    capabilities:
      my_capability: {{ value }}
""", dict(value=value)).assert_failure()


def test_node_type_capability_syntax_unsupported(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability:
        type: MyType
        unsupported: {}
""").assert_failure()


def test_node_type_capability_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    capabilities:
      my_capability: {} # "type" is required
""").assert_failure()


# Description

@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_node_type_capability_description_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability:
        type: MyType
        description: {{ value }}
""", dict(value=value)).assert_failure()


def test_node_type_capability_description(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability:
        type: MyType
        description: a description
""").assert_success()


# Type

@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_node_type_capability_type_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    capabilities:
      my_capability:
        type: {{ value }}
""", dict(value=value)).assert_failure()


def test_node_type_capability_type_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    capabilities:
      my_capability:
        type: UnknownType
""").assert_failure()


def test_node_type_capability_type_override(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
node_types:
  MyType1:
    capabilities:
      my_capability:
        type: MyType1
  MyType2:
    derived_from: MyType1
    capabilities:
      my_capability:
        type: MyType2
""").assert_success()


def test_node_type_capability_type_override_bad(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType1: {}
  MyType2: {}
node_types:
  MyType1:
    capabilities:
      my_capability:
        type: MyType1
  MyType2:
    derived_from: MyType1
    capabilities:
      my_capability:
        type: MyType2
""").assert_failure()


# Valid source types

@pytest.mark.parametrize('value', data.NOT_A_LIST)
def test_node_type_capability_valid_source_types_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability:
        type: MyType
        valid_source_types: {{ value }}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_node_type_capability_valid_source_types_syntax_element_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability:
        type: MyType
        valid_source_types: [ {{ value }} ]
""", dict(value=value)).assert_failure()


def test_node_type_capability_valid_source_types_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability:
        type: MyType
        valid_source_types: []
""").assert_success()



def test_node_type_capability_valid_source_types(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType1:
    capabilities:
      my_capability:
        type: MyType
        valid_source_types: [ MyType1, MyType2 ]
  MyType2: {}
""").assert_success()


def test_node_type_capability_valid_source_types_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability:
        type: MyType
        valid_source_types: [ UnknownType ]
""").assert_failure()


# Occurrences

@pytest.mark.parametrize('value', data.OCCURRENCES)
def test_node_type_capability_occurrences(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability:
        type: MyType
        occurrences: {{ value }}
""", dict(value=value)).assert_success()


@pytest.mark.parametrize('value', data.BAD_OCCURRENCES)
def test_node_type_capability_occurrences_bad(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  MyType: {}
node_types:
  MyType:
    capabilities:
      my_capability:
        type: MyType
        occurrences: {{ value }}
""", dict(value=value)).assert_failure()


# Unicode

def test_node_type_capability_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
capability_types:
  類型: {}
node_types:
  類型:
    capabilities:
      能力:
        type: 類型
        properties:
          參數:
            type: string
            description: 描述
            default: 值
            status: supported
        valid_source_types: [ 類型 ]
""").assert_success()
