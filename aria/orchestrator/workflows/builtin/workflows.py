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

from .utils import (create_node_instance_task, create_relationship_instance_tasks)
from ... import workflow


__all__ = (
    'install_node_instance',
    'uninstall_node_instance',
    'start_node_instance',
    'stop_node_instance',
)


@workflow(suffix_template='{node_instance.id}')
def install_node_instance(graph, node_instance, **kwargs):
    sequence = []

    # Create
    sequence.append(
        create_node_instance_task(
            'tosca.interfaces.node.lifecycle.Standard.create',
            node_instance))

    # Configure
    sequence += \
        create_relationship_instance_tasks(
            'tosca.interfaces.relationship.Configure.pre_configure_source',
            'source_operations',
            node_instance)
    sequence += \
        create_relationship_instance_tasks(
            'tosca.interfaces.relationship.Configure.pre_configure_target',
            'target_operations',
            node_instance)
    sequence.append(
        create_node_instance_task(
            'tosca.interfaces.node.lifecycle.Standard.configure',
            node_instance))
    sequence += \
        create_relationship_instance_tasks(
            'tosca.interfaces.relationship.Configure.post_configure_source',
            'source_operations',
            node_instance)
    sequence += \
        create_relationship_instance_tasks(
            'tosca.interfaces.relationship.Configure.post_configure_target',
            'target_operations',
            node_instance)

    # Start
    sequence += _create_start_tasks(node_instance)

    graph.sequence(*sequence)


@workflow(suffix_template='{node_instance.id}')
def uninstall_node_instance(graph, node_instance, **kwargs):
    # Stop
    sequence = _create_stop_tasks(node_instance)

    # Delete
    sequence.append(
        create_node_instance_task(
            'tosca.interfaces.node.lifecycle.Standard.delete',
            node_instance))

    graph.sequence(*sequence)


@workflow(suffix_template='{node_instance.id}')
def start_node_instance(graph, node_instance, **kwargs):
    graph.sequence(*_create_start_tasks(node_instance))


@workflow(suffix_template='{node_instance.id}')
def stop_node_instance(graph, node_instance, **kwargs):
    graph.sequence(*_create_stop_tasks(node_instance))


def _create_start_tasks(node_instance):
    sequence = []
    sequence.append(
        create_node_instance_task(
            'tosca.interfaces.node.lifecycle.Standard.start',
            node_instance))
    sequence += \
        create_relationship_instance_tasks(
            'tosca.interfaces.relationship.Configure.add_source',
            'source_operations',
            node_instance)
    sequence += \
        create_relationship_instance_tasks(
            'tosca.interfaces.relationship.Configure.add_target',
            'target_operations',
            node_instance)
    sequence += \
        create_relationship_instance_tasks(
            'tosca.interfaces.relationship.Configure.target_changed',
            'target_operations',
            node_instance)
    return sequence


def _create_stop_tasks(node_instance):
    sequence = []
    sequence += \
        create_relationship_instance_tasks(
            'tosca.interfaces.relationship.Configure.remove_target',
            'target_operations',
            node_instance)
    sequence += \
        create_relationship_instance_tasks(
            'tosca.interfaces.relationship.Configure.target_changed',
            'target_operations',
            node_instance)
    sequence.append(
        create_node_instance_task(
            'tosca.interfaces.node.lifecycle.Standard.stop',
            node_instance))
    return sequence
