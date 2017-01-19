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


def create_node_task(operation_name, node):
    """
    Returns a new operation task if the operation exists in the node, otherwise returns None.
    """

    if _has_operation(node.interfaces, operation_name):
        return OperationTask.node(instance=node,
                                  name=operation_name)
    return None


def create_relationship_tasks(operation_name, runs_on, node):
    """
    Returns a list of operation tasks for each outbound relationship of the node if the operation
    exists there.
    """

    sequence = []
    for relationship in node.outbound_relationships:
        if _has_operation(relationship.interfaces, operation_name):
            sequence.append(
                OperationTask.relationship(instance=relationship,
                                           name=operation_name,
                                           edge='source',
                                           runs_on=runs_on))
    return sequence


def create_node_task_dependencies(graph, tasks_and_nodes, reverse=False):
    """
    Creates dependencies between tasks if there is a relationship (outbound) between their nodes.
    """

    def get_task(node_id):
        for task, node in tasks_and_nodes:
            if node.id == node_id:
                return task
        return None

    for task, node in tasks_and_nodes:
        dependencies = []
        for relationship in node.outbound_relationships:
            dependency = get_task(relationship.target_node.id)
            if dependency:
                dependencies.append(dependency)
        if dependencies:
            if reverse:
                for dependency in dependencies:
                    graph.add_dependency(dependency, task)
            else:
                graph.add_dependency(task, dependencies)


def _has_operation(interfaces, operation_name):
    for interface in interfaces:
        if interface.operations.filter_by(name=operation_name).count() == 1:
            return True
    return False
