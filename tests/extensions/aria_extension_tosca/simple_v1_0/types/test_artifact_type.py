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


# MIME type

@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_artifact_type_mime_type_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType:
    mime_type: {{ value }}
""", dict(value=value)).assert_failure()


# File extension

@pytest.mark.parametrize('value', data.NOT_A_LIST)
def test_artifact_type_file_ext_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType:
    file_ext: {{ value }}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_artifact_type_file_ext_syntax_element_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType:
    file_ext: [ {{ value }} ]
""", dict(value=value)).assert_failure()


def test_artifact_type_file_ext_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  MyType:
    file_ext: []
""").assert_success()


# Unicode


def test_artifact_type_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
artifact_types:
  類型:
    file_ext: [ 延期一, 延期二 ]
""").assert_success()
