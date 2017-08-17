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


# Repositories section

@pytest.mark.parametrize('value', data.NOT_A_DICT)
def test_repositories_section_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories: {{ value }}
""", dict(value=value)).assert_failure()


def test_repositories_section_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories: {}
""").assert_success()


# Repository

@pytest.mark.parametrize('value', data.NOT_A_DICT_OR_STRING)
def test_repository_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository: {{ value }}
""", dict(value=value)).assert_failure()


def test_repository_syntax_unsupported(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: a url
    unsupported: {}
""").assert_failure()


def test_repository_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository: {} # "url" is required
""").assert_failure()


# Description

@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_repository_description_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: a url
    description: {{ value }}
""", dict(value=value)).assert_failure()


def test_repository_description(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: a url
    description: a description
""").assert_success()


# URL

@pytest.mark.parametrize('value', data.NOT_A_STRING)
def test_repository_url_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: {{ value }}
""", dict(value=value)).assert_failure()


def test_repository_url_short_form(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository: a url
""").assert_success()


# Credential

@pytest.mark.parametrize('value', data.NOT_A_DICT)
def test_repository_credential_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: a url
    credential: {{ value }}
""", dict(value=value), import_profile=True).assert_failure()


def test_repository_credential_syntax_unsupported(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: a url
    credential:
      unsupported: {}
""", import_profile=True).assert_failure()


def test_repository_credential_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: a url
    credential: {}
""", import_profile=True).assert_success()


def test_repository_credential_full(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: a url
    credential:
      protocol: a protocol
      token_type: a token type
      token: a token
      keys:
        key1: value1
        key2: value2
      user: a user
""", import_profile=True).assert_success()


# Unicode

def test_repository_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  知識庫:
    url: 網址
    description: 描述
    credential:
      protocol: 協議
      token_type: 類型
      token: 代幣
      keys:
        鍵一: 值
        鍵二: 值
      user: 用戶
""", import_profile=True).assert_success()
