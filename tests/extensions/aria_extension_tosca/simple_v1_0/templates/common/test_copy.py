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


PERMUTATIONS = ('node', 'relationship')


@pytest.mark.parametrize('name,value', matrix(PERMUTATIONS, data.NOT_A_STRING))
def test_templates_copy_syntax_type(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType: {}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
    copying_template:
      copy: {{ value }} 
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name], value=value)).assert_failure()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_templates_copy(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType: {}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
    copying_template:
      copy: my_template
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_success()


@pytest.mark.parametrize('name', PERMUTATIONS)
def test_templates_copy_unknown(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
{{ name }}_types:
  MyType: {}
topology_template:
  {{ section }}:
    my_template:
      type: MyType
    copying_template:
      copy: unknown
""", dict(name=name, section=data.TEMPLATE_NAME_SECTIONS[name])).assert_failure()
