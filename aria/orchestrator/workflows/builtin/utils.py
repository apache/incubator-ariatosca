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

from ..api.task import OperationTask, StubTask
from .. import exceptions


def create_node_task(node, interface_name, operation_name, **kwargs):
    """
    Returns a new operation task if the operation exists in the node, otherwise returns None.
    """

    try:
        if _is_empty_task(node, interface_name, operation_name):
            return StubTask()

        return OperationTask.for_node(node=node,
                                      interface_name=interface_name,
                                      operation_name=operation_name,
                                      **kwargs)
    except exceptions.OperationNotFoundException:
        # We will skip nodes which do not have the operation
        return None


def create_relationships_tasks(
        node, interface_name, source_operation_name=None, target_operation_name=None, **kwargs):
    """
    Creates a relationship task (source and target) for all of a node_instance relationships.
    :param basestring source_operation_name: the relationship operation name.
    :param basestring interface_name: the name of the interface.
    :param source_operation_name:
    :param target_operation_name:
    :param NodeInstance node: the source_node
    :return:
    """
    sub_tasks = []
    for relationship in node.outbound_relationships:
        relationship_operations = relationship_tasks(
            relationship,
            interface_name,
            source_operation_name=source_operation_name,
            target_operation_name=target_operation_name,
            **kwargs)
        sub_tasks.append(relationship_operations)
    return sub_tasks


def relationship_tasks(relationship, interface_name, source_operation_name=None,
                       target_operation_name=None, **kwargs):
    """
    Creates a relationship task source and target.
    :param Relationship relationship: the relationship instance itself
    :param source_operation_name:
    :param target_operation_name:

    :return:
    """
    operations = []
    if source_operation_name:
        try:
            if _is_empty_task(relationship, interface_name, source_operation_name):
                operations.append(StubTask())

            operations.append(
                OperationTask.for_relationship(relationship=relationship,
                                               interface_name=interface_name,
                                               operation_name=source_operation_name,
                                               **kwargs)
            )
        except exceptions.OperationNotFoundException:
            # We will skip relationships which do not have the operation
            pass
    if target_operation_name:
        try:
            if _is_empty_task(relationship, interface_name, target_operation_name):
                operations.append(StubTask())

            operations.append(
                OperationTask.for_relationship(relationship=relationship,
                                               interface_name=interface_name,
                                               operation_name=target_operation_name,
                                               **kwargs)
            )
        except exceptions.OperationNotFoundException:
            # We will skip relationships which do not have the operation
            pass

    return operations


def create_node_task_dependencies(graph, tasks_and_nodes, reverse=False):
    """
    Creates dependencies between tasks if there is a relationship (outbound) between their nodes.
    """

    def get_task(node_name):
        for task, node in tasks_and_nodes:
            if node.name == node_name:
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


def _is_empty_task(actor, interface_name, operation_name):
    interface = actor.interfaces.get(interface_name)
    if interface:
        operation = interface.operations.get(operation_name)
        if operation:
            return operation.implementation is None

    raise exceptions.OperationNotFoundException(
        'Could not find operation "{0}" on interface "{1}" for {2} "{3}"'
        .format(operation_name, interface_name, type(actor).__name__.lower(), actor.name))
