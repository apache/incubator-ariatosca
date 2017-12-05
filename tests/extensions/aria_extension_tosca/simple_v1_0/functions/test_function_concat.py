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


def test_functions_concat_syntax_empty(parser):
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
      properties:
        my_parameter: { concat: [] }
""").assert_success()


def test_functions_concat_strings(parser):
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
      properties:
        my_parameter: { concat: [ a, b, c ] }
""").assert_success()


def test_functions_concat_mixed(parser):
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
      properties:
        my_parameter: { concat: [ a, 1, 1.1, null, [], {} ] }
""").assert_success()


def test_functions_concat_nested(parser):
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
      properties:
        my_parameter: { concat: [ a, { concat: [ b, c ] } ] }
""").assert_success()


# Unicode

def test_functions_concat_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  類型:
    properties:
      參數:
        type: string
topology_template:
  node_templates:
    模板:
      type: 類型
      properties:
        參數: { concat: [ 一, 二, 三 ] }
""").assert_success()
