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


# Syntax

def test_functions_get_operation_output_syntax_empty(parser):
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
        my_parameter: { get_operation_output: [] } # needs at least two args
""").assert_failure()


# Arguments

def test_functions_get_operation_output(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  MyType:
    my_operation: {}
node_types:
  MyType:
    properties:
      my_parameter:
        type: string
    interfaces:
      MyInterface:
        type: MyType
topology_template:
  node_templates:
    my_node:
      type: MyType
      properties:
        my_parameter: { get_operation_output: [ my_node, MyInterface, my_operation, my_variable ] }
""").assert_success()


# Unicode

def test_functions_get_operation_output_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
interface_types:
  類型:
    手術: {}
node_types:
  類型:
    properties:
      參數:
        type: string
    interfaces:
      接口:
        type: 類型
topology_template:
  node_templates:
    模板:
      type: 類型
      properties:
        參數: { get_operation_output: [ 模板, 接口, 手術, 變量 ] }
""").assert_success()
