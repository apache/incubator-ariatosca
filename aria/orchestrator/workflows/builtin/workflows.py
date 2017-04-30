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
TSOCA normative lifecycle workflows.
"""

from ... import workflow
from ..api import task


NORMATIVE_STANDARD_INTERFACE = 'Standard' # 'tosca.interfaces.node.lifecycle.Standard'
NORMATIVE_CONFIGURE_INTERFACE = 'Configure' # 'tosca.interfaces.relationship.Configure'

NORMATIVE_CREATE = 'create'
NORMATIVE_CONFIGURE = 'configure'
NORMATIVE_START = 'start'
NORMATIVE_STOP = 'stop'
NORMATIVE_DELETE = 'delete'

NORMATIVE_PRE_CONFIGURE_SOURCE = 'pre_configure_source'
NORMATIVE_PRE_CONFIGURE_TARGET = 'pre_configure_target'
NORMATIVE_POST_CONFIGURE_SOURCE = 'post_configure_source'
NORMATIVE_POST_CONFIGURE_TARGET = 'post_configure_target'

NORMATIVE_ADD_SOURCE = 'add_source'
NORMATIVE_ADD_TARGET = 'add_target'
NORMATIVE_REMOVE_TARGET = 'remove_target'
NORMATIVE_REMOVE_SOURCE = 'remove_source'
NORMATIVE_TARGET_CHANGED = 'target_changed'


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
    'NORMATIVE_REMOVE_SOURCE',
    'NORMATIVE_REMOVE_TARGET',
    'NORMATIVE_TARGET_CHANGED',
    'install_node',
    'uninstall_node',
    'start_node',
    'stop_node',
)


@workflow(suffix_template='{node.name}')
def install_node(graph, node, **kwargs):
    # Create
    sequence = [task.create_task(node, NORMATIVE_STANDARD_INTERFACE, NORMATIVE_CREATE)]

    # Configure
    sequence += task.create_relationships_tasks(node,
                                                NORMATIVE_CONFIGURE_INTERFACE,
                                                NORMATIVE_PRE_CONFIGURE_SOURCE,
                                                NORMATIVE_PRE_CONFIGURE_TARGET)
    sequence.append(task.create_task(node, NORMATIVE_STANDARD_INTERFACE, NORMATIVE_CONFIGURE))
    sequence += task.create_relationships_tasks(node,
                                                NORMATIVE_CONFIGURE_INTERFACE,
                                                NORMATIVE_POST_CONFIGURE_SOURCE,
                                                NORMATIVE_POST_CONFIGURE_TARGET)
    # Start
    sequence += _create_start_tasks(node)

    graph.sequence(*sequence)


@workflow(suffix_template='{node.name}')
def uninstall_node(graph, node, **kwargs):
    # Stop
    sequence = _create_stop_tasks(node)

    # Delete
    sequence.append(task.create_task(node, NORMATIVE_STANDARD_INTERFACE, NORMATIVE_DELETE))

    graph.sequence(*sequence)


@workflow(suffix_template='{node.name}')
def start_node(graph, node, **kwargs):
    graph.sequence(*_create_start_tasks(node))


@workflow(suffix_template='{node.name}')
def stop_node(graph, node, **kwargs):
    graph.sequence(*_create_stop_tasks(node))


def _create_start_tasks(node):
    sequence = [task.create_task(node, NORMATIVE_STANDARD_INTERFACE, NORMATIVE_START)]
    sequence += task.create_relationships_tasks(node,
                                                NORMATIVE_CONFIGURE_INTERFACE,
                                                NORMATIVE_ADD_SOURCE, NORMATIVE_ADD_TARGET)
    return sequence


def _create_stop_tasks(node):
    sequence = [task.create_task(node, NORMATIVE_STANDARD_INTERFACE, NORMATIVE_STOP)]
    sequence += task.create_relationships_tasks(node,
                                                NORMATIVE_CONFIGURE_INTERFACE,
                                                NORMATIVE_REMOVE_SOURCE, NORMATIVE_REMOVE_TARGET)
    return sequence


def create_node_task_dependencies(graph, tasks_and_nodes, reverse=False):
    """
    Creates dependencies between tasks if there is a relationship (outbound) between their nodes.
    """

    def get_task(node_name):
        for api_task, task_node in tasks_and_nodes:
            if task_node.name == node_name:
                return api_task
        return None

    for api_task, node in tasks_and_nodes:
        dependencies = []
        for relationship in node.outbound_relationships:
            dependency = get_task(relationship.target_node.name)
            if dependency:
                dependencies.append(dependency)
        if dependencies:
            if reverse:
                for dependency in dependencies:
                    graph.add_dependency(dependency, api_task)
            else:
                graph.add_dependency(api_task, dependencies)
