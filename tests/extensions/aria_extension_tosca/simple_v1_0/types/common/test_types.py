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
from ......mechanisms.utils import matrix


CASES_WITHOUT_UNSUPPORTED_FIELDS = ('artifact', 'data', 'capability', 'relationship', 'node',
                                    'group', 'policy')

PERMUTATIONS = CASES_WITHOUT_UNSUPPORTED_FIELDS + ('interface',)


@pytest.mark.parametrize('name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_DICT
))
def test_type_syntax_type(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType: {{ value }}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('name', CASES_WITHOUT_UNSUPPORTED_FIELDS)
def test_type_syntax_unsupported(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType:
    unsupported: {}
""", dict(name=name)).assert_failure()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_type_syntax_empty(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType: {}
""", dict(name=name)).assert_success()


# Description

@pytest.mark.parametrize('name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_STRING
))
def test_type_description_syntax_type(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType:
    description: {{ value }}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_type_description(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType:
    description: a description
""", dict(name=name)).assert_success()


# Derived from

@pytest.mark.parametrize('name,value', matrix(
    PERMUTATIONS,
    data.NOT_A_STRING
))
def test_type_derived_from_syntax_type(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType:
    derived_from: {{ value }}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_type_derived_from(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType1: {}
  MyType2:
    derived_from: MyType1
""", dict(name=name)).assert_success()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_type_derived_from_unknown(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType:
    derived_from: UnknownType
""", dict(name=name)).assert_failure()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_type_derived_from_self(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType:
    derived_from: MyType
""", dict(name=name)).assert_failure()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_type_derived_from_circular(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType1:
    derived_from: MyType3
  MyType2:
    derived_from: MyType1
  MyType3:
    derived_from: MyType2
""", dict(name=name)).assert_failure()


# Version

@pytest.mark.parametrize('name,value', matrix(
    PERMUTATIONS,
    data.GOOD_VERSIONS
))
def test_type_version(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType:
    version: {{ value }}
""", dict(name=name, value=value)).assert_success()


@pytest.mark.parametrize('name,value', matrix(
    PERMUTATIONS,
    data.BAD_VERSIONS
))
def test_type_version_bad(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType:
    version: {{ value }}
""", dict(name=name, value=value)).assert_failure()


# Unicode

@pytest.mark.parametrize('name', PERMUTATIONS)
def test_type_unicode(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  類型一: {}
  類型二:
    derived_from: 類型一
    version: 1.0.0.詠嘆調-10
    description: 描述
""", dict(name=name)).assert_success()
