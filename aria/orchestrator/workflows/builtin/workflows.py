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

"""
A set of builtin workflows.
"""

from .utils import (create_node_task, create_relationship_tasks)
from ... import workflow


NORMATIVE_STANDARD_INTERFACE = 'Standard' # 'tosca.interfaces.node.lifecycle.Standard'
NORMATIVE_CONFIGURE_INTERFACE = 'Configure' # 'tosca.interfaces.relationship.Configure'

NORMATIVE_CREATE = NORMATIVE_STANDARD_INTERFACE + '.create'
NORMATIVE_START = NORMATIVE_STANDARD_INTERFACE + '.start'
NORMATIVE_STOP = NORMATIVE_STANDARD_INTERFACE + '.stop'
NORMATIVE_DELETE = NORMATIVE_STANDARD_INTERFACE + '.delete'

NORMATIVE_CONFIGURE = NORMATIVE_STANDARD_INTERFACE + '.configure'
NORMATIVE_PRE_CONFIGURE_SOURCE = NORMATIVE_CONFIGURE_INTERFACE + '.pre_configure_source'
NORMATIVE_PRE_CONFIGURE_TARGET = NORMATIVE_CONFIGURE_INTERFACE + '.pre_configure_target'
NORMATIVE_POST_CONFIGURE_SOURCE = NORMATIVE_CONFIGURE_INTERFACE + '.post_configure_source'
NORMATIVE_POST_CONFIGURE_TARGET = NORMATIVE_CONFIGURE_INTERFACE + '.post_configure_target'

NORMATIVE_ADD_SOURCE = NORMATIVE_CONFIGURE_INTERFACE + '.add_source'
NORMATIVE_ADD_TARGET = NORMATIVE_CONFIGURE_INTERFACE + '.add_target'
NORMATIVE_REMOVE_TARGET = NORMATIVE_CONFIGURE_INTERFACE + '.remove_target'
NORMATIVE_TARGET_CHANGED = NORMATIVE_CONFIGURE_INTERFACE + '.target_changed'


__all__ = (
    'NORMATIVE_STANDARD_INTERFACE',
    'NORMATIVE_CONFIGURE_INTERFACE',
    'NORMATIVE_CREATE',
    'NORMATIVE_START',
    'NORMATIVE_STOP',
    'NORMATIVE_DELETE',
    'NORMATIVE_CONFIGURE',
    'NORMATIVE_PRE_CONFIGURE_SOURCE',
    'NORMATIVE_PRE_CONFIGURE_TARGET',
    'NORMATIVE_POST_CONFIGURE_SOURCE',
    'NORMATIVE_POST_CONFIGURE_TARGET',
    'NORMATIVE_ADD_SOURCE',
    'NORMATIVE_ADD_TARGET',
    'NORMATIVE_REMOVE_TARGET',
    'NORMATIVE_TARGET_CHANGED',
    'install_node',
    'uninstall_node',
    'start_node',
    'stop_node',
)


@workflow(suffix_template='{node.id}')
def install_node(graph, node, **kwargs):
    sequence = []

    # Create
    sequence.append(
        create_node_task(
            NORMATIVE_CREATE,
            node))

    # Configure
    sequence += \
        create_relationship_tasks(
            NORMATIVE_PRE_CONFIGURE_SOURCE,
            'source',
            node)
    sequence += \
        create_relationship_tasks(
            NORMATIVE_PRE_CONFIGURE_TARGET,
            'target',
            node)
    sequence.append(
        create_node_task(
            NORMATIVE_CONFIGURE,
            node))
    sequence += \
        create_relationship_tasks(
            NORMATIVE_POST_CONFIGURE_SOURCE,
            'source',
            node)
    sequence += \
        create_relationship_tasks(
            NORMATIVE_POST_CONFIGURE_TARGET,
            'target',
            node)

    # Start
    sequence += _create_start_tasks(node)

    graph.sequence(*sequence)


@workflow(suffix_template='{node.id}')
def uninstall_node(graph, node, **kwargs):
    # Stop
    sequence = _create_stop_tasks(node)

    # Delete
    sequence.append(
        create_node_task(
            NORMATIVE_DELETE,
            node))

    graph.sequence(*sequence)


@workflow(suffix_template='{node.id}')
def start_node(graph, node, **kwargs):
    graph.sequence(*_create_start_tasks(node))


@workflow(suffix_template='{node.id}')
def stop_node(graph, node, **kwargs):
    graph.sequence(*_create_stop_tasks(node))


def _create_start_tasks(node):
    sequence = []
    sequence.append(
        create_node_task(
            NORMATIVE_START,
            node))
    sequence += \
        create_relationship_tasks(
            NORMATIVE_ADD_SOURCE,
            'source',
            node)
    sequence += \
        create_relationship_tasks(
            NORMATIVE_ADD_TARGET,
            'target',
            node)
    sequence += \
        create_relationship_tasks(
            NORMATIVE_TARGET_CHANGED,
            'target',
            node)
    return sequence


def _create_stop_tasks(node):
    sequence = []
    sequence += \
        create_relationship_tasks(
            NORMATIVE_REMOVE_TARGET,
            'target',
            node)
    sequence += \
        create_relationship_tasks(
            NORMATIVE_TARGET_CHANGED,
            'target',
            node)
    sequence.append(
        create_node_task(
            NORMATIVE_STOP,
            node))
    return sequence
