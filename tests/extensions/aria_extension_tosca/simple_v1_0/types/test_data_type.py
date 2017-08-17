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
from .....mechanisms.utils import matrix


# Derived from primitive

@pytest.mark.parametrize('name', data.PRIMITIVE_TYPE_NAMES)
def test_data_type_derived_from_primitive(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyType:
    derived_from: {{ name }} 
""", dict(name=name)).assert_success()


# Constraints

@pytest.mark.parametrize('name,value', matrix(
    data.PRIMITIVE_TYPE_NAMES,
    data.NOT_A_LIST
))
def test_data_type_constraints_syntax_type(parser, name, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyType:
    derived_from: string
    constraints: {{ value }}
""", dict(name=name, value=value)).assert_failure()


@pytest.mark.parametrize('name', data.PRIMITIVE_TYPE_NAMES)
def test_data_type_constraints_syntax_empty(parser, name):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyType:
    derived_from: string
    constraints: []
""", dict(name=name)).assert_success()


def test_data_type_constraints_not_derived_from_primitive(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
data_types:
  MyType:
    constraints: [] # can't have constraints if not derived from primitive
""").assert_failure()
