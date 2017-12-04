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


@pytest.mark.parametrize('value', data.PRIMITIVE_VALUES)
def test_dsl_definitions_syntax_anything(parser, value):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
dsl_definitions: {{ value }}
""", dict(value=value)).assert_success()


def test_dsl_definitions_anchor(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
dsl_definitions:
  key: &ANCHOR
    field: a value
""").assert_success()


# Unicode

def test_dsl_definitions_unicode(parser):
    parser.parse_literal("""
tosca_definitions_version: tosca_simple_yaml_1_0
dsl_definitions:
  定義: &ANCHOR # YAML does not allow the anchor name to be Unicode
    領域: 值
""").assert_success()
