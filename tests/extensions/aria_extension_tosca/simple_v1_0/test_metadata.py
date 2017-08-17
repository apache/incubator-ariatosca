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

from . import data
from ....mechanisms.utils import matrix


NORMATIVE_FIELD_NAMES = ('template_name', 'template_author', 'template_version')


# Metadata section

@pytest.mark.parametrize('value', data.NOT_A_DICT)
def test_metadata_section_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
metadata: {{ value }}
""", dict(value=value)).assert_failure()


def test_metadata_section_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
metadata: {}
""").assert_success()


# Fields

@pytest.mark.parametrize('field,value', matrix(
    NORMATIVE_FIELD_NAMES,
    data.NOT_A_STRING
))
def test_metadata_normative_fields_syntax_type(parser, field, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
metadata:
    {{ field }}: {{ value }}
""", dict(field=field, value=value)).assert_failure()


@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_metadata_non_normative_fields_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
metadata:
    non_normative: {{ value }}
""", dict(value=value)).assert_failure()


# Template version

@pytest.mark.parametrize('value', data.GOOD_VERSIONS)
def test_metadata_normative_template_version(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
metadata:
    template_version: {{ value }}
""", dict(value=value)).assert_success()


@pytest.mark.parametrize('value', data.BAD_VERSIONS)
def test_metadata_normative_template_bad_version(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
metadata:
    template_version: {{ value }}
""", dict(value=value)).assert_failure()


# Unicode

def test_metadata_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
metadata:
  template_name: 詠嘆調
  template_author: 詠嘆調
  template_version: 1.0.0.詠嘆調-10
  non_normative1: 詠嘆調一
  non_normative2: 詠嘆調二
  non_normative3: 詠嘆調三
""").assert_success()
