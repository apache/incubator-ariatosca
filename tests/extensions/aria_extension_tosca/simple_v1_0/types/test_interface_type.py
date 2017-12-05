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


# Operation

def test_interface_type_operation_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation: {}
""").assert_success()


# Operation description

@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_interface_type_operation_description_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation:
      description: {{ value }}
""", dict(value=value)).assert_failure()


def test_interface_type_operation_description(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation:
      description: a description
""").assert_success()


# Operation implementation

@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_interface_type_operation_implementation_primary_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation:
      implementation:
        primary: {{ value }}
""", dict(value=value)).assert_failure()


def test_interface_type_operation_implementation_primary(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation:
      implementation:
        primary: an implementation
""").assert_success()


def test_interface_type_operation_implementation_primary_short_form(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation:
      implementation: an implementation
""").assert_success()


@pytest.mark.parametrize('value', data.NOT_A_LIST)
def test_interface_type_operation_dependencies_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation:
      implementation:
        primary: an implementation
        dependencies: {{ value }}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_interface_type_operation_dependencies_syntax_element_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation:
      implementation:
        primary: an implementation
        dependencies:
          - {{ value }}
""", dict(value=value)).assert_failure()


def test_interface_type_operation_dependencies_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation:
      implementation:
        primary: an implementation
        dependencies: []
""").assert_success()


# Unicode

def test_interface_type_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  類型:
    inputs:
      輸入:
        type: string
    手術:
      description: 描述
      implementation:
        primary: 履行
        dependencies:
          - 依賴
      inputs:
        輸入:
          type: string
""").assert_success()
