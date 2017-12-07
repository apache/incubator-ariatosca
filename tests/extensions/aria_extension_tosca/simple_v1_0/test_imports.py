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

from tests.helpers import get_resource_uri
from . import data
from ....mechanisms.web_server import WebServer


# Fixtures

NODE_TYPE_IMPORT = """
node_types:
  MyNode: {}
"""

NODE_TYPE_IMPORT_UNICODE = """
node_types:
  類型: {}
"""

BAD_IMPORT = """
node_types:
  MyNode:
    derived_from: UnknownType
"""

PLUGIN_RESOURCES = "plugins"

@pytest.fixture(scope='session')
def repository():
    repository = WebServer()
    repository.add_text_yaml('/imports/node-type.yaml', NODE_TYPE_IMPORT)
    repository.add_text_yaml('/imports/{0}.yaml'.format(WebServer.escape('節點類型')),
                             NODE_TYPE_IMPORT_UNICODE)
    repository.add_text_yaml('/imports/bad.yaml', BAD_IMPORT)
    with repository:
        yield repository.root


# Imports section

@pytest.mark.parametrize('value', data.NOT_A_LIST)
def test_imports_section_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports: {{ value }}
""", dict(value=value)).assert_failure()


def test_imports_section_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports: []
""").assert_success()


# Import

@pytest.mark.parametrize('value', data.NOT_A_DICT_OR_STRING)
def test_import_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - {{ value }}
""", dict(value=value)).assert_failure()


def test_import_syntax_unsupported(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - unsupported: {}
""").assert_failure()


def test_import_syntax_empty(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - {} # "file" is required
""").assert_failure()


# File

@pytest.mark.parametrize('value', data.NOT_A_DICT_OR_STRING)
def test_import_file_syntax_type(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - file: {{ value }}
""", dict(value=value)).assert_failure()


def test_import_file_short_form(parser, repository):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - {{ repository }}/imports/node-type.yaml
topology_template:
  node_templates:
    my_node:
      type: MyNode
""", dict(repository=repository)).assert_success()


def test_import_file(parser, repository):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - file: {{ repository }}/imports/node-type.yaml
topology_template:
  node_templates:
    my_node:
      type: MyNode
""", dict(repository=repository)).assert_success()


# Repository

@pytest.mark.xfail(reason='not yet implemented')
def test_import_repository(parser, repository):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
repositories:
  my_repository:
    url: {{ repository }}/imports/
imports:
  - file: node-type.yaml
    repository: my_repository
topology_template:
  node_templates:
    my_node:
      type: MyNode
""", dict(repository=repository)).assert_success()

#Plugin

def test_import_plugin(parser):
    plugin_dir = get_resource_uri(PLUGIN_RESOURCES)
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - aria-1.0
  - file: import-plugin-1.0.0
    repository: plugins
topology_template:
  node_templates:
    Network:
      type: myapp.nodes.Network
""", plugin_dir=plugin_dir).assert_success()

# Namespace

@pytest.mark.xfail(reason='not yet implemented')
def test_import_namespace(parser, repository):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - file: {{ repository }}/imports/node-type.yaml
    namespace_uri:
    namespace_prefix: my_namespace
topology_template:
  node_templates:
    my_node:
      type: my_namespace.MyNode
""", dict(repository=repository)).assert_success()


# Bad imports

def test_import_not_found(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - does_not_exist
""").assert_failure()


def test_import_bad(parser, repository):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - {{ repository }}/imports/bad.yaml
topology_template:
  node_templates:
    my_node:
      type: MyNode
""", dict(repository=repository)).assert_failure()


# Unicode

def test_import_unicode(parser, repository):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
imports:
  - {{ repository }}/imports/節點類型.yaml
topology_template:
  node_templates:
    模板:
      type: 類型
""", dict(repository=repository)).assert_success()
