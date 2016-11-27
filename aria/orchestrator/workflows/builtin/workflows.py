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

from itertools import groupby

from aria import workflow

from ..api import task


__all__ = (
    'install_node_instance',
    'uninstall_node_instance',
    'execute_operation_on_instance',
)


# Install node instance workflow and sub workflows

@workflow(suffix_template='{node_instance.id}')
def install_node_instance(graph, node_instance, **kwargs):
    """
    A workflow which installs a node instance.
    :param TaskGraph graph: the tasks graph of which to edit
    :param node_instance: the node instance to install
    :return:
    """
    create_node_instance = task.OperationTask.node_instance(
        instance=node_instance,
        name='aria.interfaces.lifecycle.create')

    configure_node_instance = task.OperationTask.node_instance(
        instance=node_instance,
        name='aria.interfaces.lifecycle.configure')
    start_node_instance = task.OperationTask.node_instance(
        instance=node_instance,
        name='aria.interfaces.lifecycle.start')

    graph.sequence(
        create_node_instance,
        preconfigure_relationship(graph, node_instance),
        configure_node_instance,
        postconfigure_relationship(graph, node_instance),
        start_node_instance,
        establish_relationship(graph, node_instance)
    )

    return graph


def preconfigure_relationship(graph, node_instance, **kwargs):
    """

    :param graph:
    :param node_instance:
    :return:
    """
    return relationships_tasks(
        graph=graph,
        operation_name='aria.interfaces.relationship_lifecycle.preconfigure',
        node_instance=node_instance)


def postconfigure_relationship(graph, node_instance, **kwargs):
    """

    :param graph:
    :param node_instance:
    :return:
    """
    return relationships_tasks(
        graph=graph,
        operation_name='aria.interfaces.relationship_lifecycle.postconfigure',
        node_instance=node_instance)


def establish_relationship(graph, node_instance, **kwargs):
    """

    :param graph:
    :param node_instance:
    :return:
    """
    return relationships_tasks(
        graph=graph,
        operation_name='aria.interfaces.relationship_lifecycle.establish',
        node_instance=node_instance)


# Uninstall node instance workflow and subworkflows

@workflow(suffix_template='{node_instance.id}')
def uninstall_node_instance(graph, node_instance, **kwargs):
    """
    A workflow which uninstalls a node instance.
    :param TaskGraph graph: the tasks graph of which to edit
    :param node_instance: the node instance to uninstall
    :return:
    """
    stop_node_instance = task.OperationTask.node_instance(
        instance=node_instance,
        name='aria.interfaces.lifecycle.stop')
    delete_node_instance = task.OperationTask.node_instance(
        instance=node_instance,
        name='aria.interfaces.lifecycle.delete')

    graph.sequence(
        stop_node_instance,
        unlink_relationship(graph, node_instance),
        delete_node_instance
    )


def unlink_relationship(graph, node_instance):
    """

    :param graph:
    :param node_instance:
    :return:
    """
    return relationships_tasks(
        graph=graph,
        operation_name='aria.interfaces.relationship_lifecycle.unlink',
        node_instance=node_instance
    )


def execute_operation_on_instance(
        node_instance,
        operation,
        operation_kwargs,
        allow_kwargs_override):
    """
    A workflow which executes a single operation
    :param node_instance: the node instance to install
    :param basestring operation: the operation name
    :param dict operation_kwargs:
    :param bool allow_kwargs_override:
    :return:
    """

    if allow_kwargs_override is not None:
        operation_kwargs['allow_kwargs_override'] = allow_kwargs_override

    return task.OperationTask.node_instance(
        instance=node_instance,
        name=operation,
        inputs=operation_kwargs)


def relationships_tasks(graph, operation_name, node_instance):
    """
    Creates a relationship task (source and target) for all of a node_instance relationships.
    :param basestring operation_name: the relationship operation name.
    :param WorkflowContext context:
    :param NodeInstance node_instance:
    :return:
    """
    relationships_groups = groupby(
        node_instance.outbound_relationship_instances,
        key=lambda relationship_instance: relationship_instance.target_node_instance.id)

    sub_tasks = []
    for _, (_, relationship_group) in enumerate(relationships_groups):
        for relationship_instance in relationship_group:
            relationship_operations = relationship_tasks(
                relationship_instance=relationship_instance,
                operation_name=operation_name)
            sub_tasks.append(relationship_operations)

    return graph.sequence(*sub_tasks)


def relationship_tasks(relationship_instance, operation_name):
    """
    Creates a relationship task source and target.
    :param RelationshipInstance relationship_instance: the relationship instance itself
    :param operation_name:
    :return:
    """
    source_operation = task.OperationTask.relationship_instance(
        instance=relationship_instance,
        name=operation_name,
        operation_end=task.OperationTask.SOURCE_OPERATION)
    target_operation = task.OperationTask.relationship_instance(
        instance=relationship_instance,
        name=operation_name,
        operation_end=task.OperationTask.TARGET_OPERATION)

    return source_operation, target_operation
