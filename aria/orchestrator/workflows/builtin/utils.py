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

from ..api.task import OperationTask
from .. import exceptions


def create_node_task(interface_name, operation_name, node):
    """
    Returns a new operation task if the operation exists in the node, otherwise returns None.
    """

    try:
        return OperationTask.for_node(node=node,
                                      interface_name=interface_name,
                                      operation_name=operation_name)
    except exceptions.TaskException:
        pass
    return None


def create_relationship_tasks(interface_name, operation_name, runs_on, node):
    """
    Returns a list of operation tasks for each outbound relationship of the node if the operation
    exists there.
    """

    sequence = []
    for relationship in node.outbound_relationships:
        try:
            sequence.append(
                OperationTask.for_relationship(relationship=relationship,
                                               interface_name=interface_name,
                                               operation_name=operation_name,
                                               edge='source',
                                               runs_on=runs_on))
        except exceptions.TaskException:
            pass
    return sequence


def create_node_task_dependencies(graph, tasks_and_nodes, reverse=False):
    """
    Creates dependencies between tasks if there is a relationship (outbound) between their nodes.
    """

    def get_task(node_id):
        for task, node in tasks_and_nodes:
            if node.name == node_id:
                return task
        return None

    for task, node in tasks_and_nodes:
        dependencies = []
        for relationship in node.outbound_relationships:
            dependency = get_task(relationship.target_node.name)
            if dependency:
                dependencies.append(dependency)
        if dependencies:
            if reverse:
                for dependency in dependencies:
                    graph.add_dependency(dependency, task)
            else:
                graph.add_dependency(task, dependencies)
