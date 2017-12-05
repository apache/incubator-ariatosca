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


# TODO:
#  other keywords (HOST, SOURCE, TARGET)
#  requirements
#  capabilities


PERMUTATIONS = (
    ('get_property', 'properties'),
    ('get_attribute', 'attributes')
)


# Syntax

@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_syntax_empty(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    {{ section }}:
      my_parameter:
        type: string
topology_template:
  node_templates:
    my_node:
      type: MyType
      {{ section }}:
        my_parameter: { {{ function }}: [] } # needs at least two args
""", dict(function=function, section=section)).assert_failure()


@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_syntax_single(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    {{ section }}:
      my_parameter:
        type: string
topology_template:
  node_templates:
    my_node:
      type: MyType
      {{ section }}:
        my_parameter: { {{ function }}: [ SELF ] } # needs at least two args
""", dict(function=function, section=section)).assert_failure()


# Entities

@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_same(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    {{ section }}:
      my_parameter1:
        type: string
      my_parameter2:
        type: string
        default: a value
topology_template:
  node_templates:
    my_node:
      type: MyType
      {{ section }}:
        my_parameter1: { {{ function }}: [ my_node, my_parameter2 ] }
""", dict(function=function, section=section)).assert_success()


@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_other(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    {{ section }}:
      my_parameter1:
        type: string
      my_parameter2:
        type: string
        default: a value
topology_template:
  node_templates:
    my_node1:
      type: MyType
      {{ section }}:
        my_parameter1: { {{ function }}: [ my_node2, my_parameter2 ] }
    my_node2:
      type: MyType
      {{ section }}:
        my_parameter1: a value
""", dict(function=function, section=section)).assert_success()


@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_unknown(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    properties:
      my_parameter:
        type: string
topology_template:
  node_templates:
    my_node:
      type: MyType
      {{ section }}:
        my_parameter: { get_property: [ unknown, my_parameter ] }
""", dict(function=function, section=section)).assert_failure()


# Cyclical

@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_cyclical_simple(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    {{ section }}:
      my_parameter:
        type: string
topology_template:
  node_templates:
    my_node:
      type: MyType
      {{ section }}:
        my_parameter: { {{ function }}: [ my_node, my_parameter ] }
""", dict(function=function, section=section)).assert_failure()


@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_cyclical_complex(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    {{ section }}:
      my_parameter1:
        type: string
      my_parameter2:
        type: string
topology_template:
  node_templates:
    my_node:
      type: MyType
      {{ section }}:
        my_parameter1: { {{ function }}: [ my_node, my_parameter2 ] }
        my_parameter2: { {{ function }}: [ my_node, my_parameter1 ] }
""", dict(function=function, section=section)).assert_failure()


@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_sub(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyType:
    properties:
      my_field:
        type: string
node_types:
  MyType:
    {{ section }}:
      my_parameter1:
        type: string
      my_parameter2:
        type: MyType
        default:
          my_field: a value
topology_template:
  node_templates:
    my_node:
      type: MyType
      {{ section }}:
        my_parameter1: { {{ function }}: [ my_node, my_parameter2, my_field ] }
""", dict(function=function, section=section)).assert_success()


# Keywords

@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_self(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType:
    {{ section }}:
      my_parameter1:
        type: string
      my_parameter2:
        type: string
        default: a value
topology_template:
  node_templates:
    my_node:
      type: MyType
      {{ section }}:
        my_parameter1: { {{ function }}: [ SELF, my_parameter2 ] }
""", dict(function=function, section=section)).assert_success()


# Unicode

@pytest.mark.parametrize('function,section', PERMUTATIONS)
def test_functions_modelable_entity_unicode(parser, function, section):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  類型:
    {{ section }}:
      參數一:
        type: string
      參數二:
        type: string
        default: 值
topology_template:
  node_templates:
    模板:
      type: 類型
      {{ section }}:
        參數一: { {{ function }}: [ 模板, 參數二 ] }
""", dict(function=function, section=section)).assert_success()
