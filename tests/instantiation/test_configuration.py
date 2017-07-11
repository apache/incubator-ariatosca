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

from tests.parser.service_templates import consume_literal
from aria.modeling.utils import parameters_as_values


TEMPLATE = """
tosca_definitions_version: tosca_simple_yaml_1_0

interface_types:
  MyInterface:
    derived_from: tosca.interfaces.Root   
    inputs:
      interface_string:
        type: string
        default: value1
      interface_integer:
        type: integer
        default: 1
    operation:
      implementation: operation.sh
      inputs:
        operation_string:
          type: string
          default: value2
        operation_integer:
          type: integer
          default: 2
        interface_integer: # will override interface input
          type: integer
          default: 3

node_types:
  LocalNode:
    derived_from: tosca.nodes.Root
    interfaces:
      MyInterface:
        type: MyInterface

  RemoteNode:
    derived_from: tosca.nodes.Compute
    interfaces:
      MyInterface:
        type: MyInterface

topology_template:
  node_templates:
    local_node:
      type: LocalNode

    remote_node:
      type: RemoteNode   
"""


BROKEN_TEMPLATE = """
tosca_definitions_version: tosca_simple_yaml_1_0

interface_types:
  MyInterface:
    derived_from: tosca.interfaces.Root   
    inputs:
      ctx: # reserved name
        type: string
        default: value1
      interface_integer:
        type: integer
        default: 1
    operation:
      implementation: operation.sh
      inputs:
        operation_string:
          type: string
          default: value2
        toolbelt: # reserved name
          type: integer
          default: 2

node_types:
  LocalNode:
    derived_from: tosca.nodes.Root
    interfaces:
      MyInterface:
        type: MyInterface

topology_template:
  node_templates:
    local_node:
      type: LocalNode
"""


@pytest.fixture
def service():
    context, _ = consume_literal(TEMPLATE)
    yield context.modeling.instance


@pytest.fixture
def broken_service_issues():
    context, _ = consume_literal(BROKEN_TEMPLATE, no_issues=False)
    yield context.validation.issues


def test_local(service):
    interface = service.nodes['local_node_1'].interfaces['MyInterface']
    operation = interface.operations['operation']
    assert parameters_as_values(interface.inputs) == {
        'interface_string': 'value1',
        'interface_integer': 1
    }
    assert parameters_as_values(operation.inputs) == {
        'operation_string': 'value2',
        'operation_integer': 2,
        'interface_integer': 3
    }
    assert parameters_as_values(operation.arguments) == {
        'process': {},
        'script_path': 'operation.sh',
        'interface_string': 'value1',
        'interface_integer': 3,
        'operation_string': 'value2',
        'operation_integer': 2
    }


def test_remote(service):
    interface = service.nodes['remote_node_1'].interfaces['MyInterface']
    operation = interface.operations['operation']
    assert parameters_as_values(interface.inputs) == {
        'interface_string': 'value1',
        'interface_integer': 1
    }
    assert parameters_as_values(operation.inputs) == {
        'operation_string': 'value2',
        'operation_integer': 2,
        'interface_integer': 3
    }
    assert parameters_as_values(operation.arguments) == {
        'process': {},
        'use_sudo': False,
        'fabric_env': {'user': '', 'password': '', 'key': None, 'key_filename': None},
        'script_path': 'operation.sh',
        'hide_output': [],
        'interface_string': 'value1',
        'interface_integer': 3,
        'operation_string': 'value2',
        'operation_integer': 2
    }


def test_reserved_arguments(broken_service_issues):
    assert len(broken_service_issues) == 1
    message = broken_service_issues[0].message
    assert message.startswith('using reserved arguments in operation "operation":')
    assert '"ctx"' in message
    assert '"toolbelt"' in message
