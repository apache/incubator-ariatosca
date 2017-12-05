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
def test_group_type_members_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType:
    members: {{ value }}
""", dict(value=value)).assert_failure()


@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_group_type_members_syntax_element_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType:
    members: [ {{ value }} ]
""", dict(value=value)).assert_failure()


def test_group_type_members_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType:
    members: []
""").assert_success()


def test_group_type_members(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  MyType1: {}
  MyType2: {}
group_types:
  MyType:
    members: [ MyType1, MyType2 ]
""").assert_success()


def test_group_type_members_unknown(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
group_types:
  MyType:
    members: [ UnknownType ]
""").assert_failure()


# Unicode

def test_group_type_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
node_types:
  類型一: {}
  類型二: {}
group_types:
  類型:
    members: [ 類型一, 類型二 ]
""").assert_success()
