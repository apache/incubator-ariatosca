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


# Syntax

def test_functions_get_artifact_syntax_empty(parser):
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
        my_parameter: { get_artifact: [] } # needs at least two args
""").assert_failure()


# Arguments

def test_functions_get_artifact_2_arguments(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
node_types:
  MyType:
    properties:
      my_parameter:
        type: string
    artifacts:
      my_artifact:
        type: MyType
        file: filename
topology_template:
  node_templates:
    my_node:
      type: MyType
      properties:
        my_parameter: { get_artifact: [ my_node, my_artifact ] }
""").assert_success()


@pytest.mark.xfail(reason='not yet implemented')
def test_functions_get_artifact_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
node_types:
  MyType:
    properties:
      my_parameter:
        type: string
    artifacts:
      my_artifact:
        type: MyType
        file: filename
topology_template:
  node_templates:
    my_node:
      type: MyType
      properties:
        my_parameter: { get_artifact: [ unknown, my_artifact ] }
""").assert_failure()


def test_functions_get_artifact_3_arguments(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
node_types:
  MyType:
    properties:
      my_parameter:
        type: string
    artifacts:
      my_artifact:
        type: MyType
        file: filename
topology_template:
  node_templates:
    my_node:
      type: MyType
      properties:
        my_parameter: { get_artifact: [ my_node, my_artifact, path ] }
""").assert_success()


def test_functions_get_artifact_4_arguments(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType: {}
node_types:
  MyType:
    properties:
      my_parameter:
        type: string
    artifacts:
      my_artifact:
        type: MyType
        file: filename
topology_template:
  node_templates:
    my_node:
      type: MyType
      properties:
        my_parameter: { get_artifact: [ my_node, my_artifact, path, true ] }
""").assert_success()


# Unicode

def test_functions_get_artifact_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  類型: {}
node_types:
  類型:
    properties:
      參數:
        type: string
    artifacts:
      神器:
        type: 類型
        file: 文件名
topology_template:
  node_templates:
    模板:
      type: 類型
      properties:
        參數: { get_artifact: [ 模板, 神器, 路徑, true ] }
""").assert_success()
