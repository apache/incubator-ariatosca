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


__all__ = (
    'install_node_instance',
    'uninstall_node_instance',
    'execute_operation_on_instance',
)


# Install node instance workflow and sub workflows

@workflow(suffix_template='{node_instance.id}')
def install_node_instance(context, graph, node_instance):
    """
    A workflow which installs a node instance.
    :param WorkflowContext context: the workflow context
    :param TaskGraph graph: the tasks graph of which to edit
    :param node_instance: the node instance to install
    :return:
    """
    create_node_instance = context.operation(
        name='aria.interfaces.lifecycle.create.{0}'.format(node_instance.id),
        operation_details=node_instance.node.operations[
            'aria.interfaces.lifecycle.create'],
        node_instance=node_instance
    )
    configure_node_instance = context.operation(
        name='aria.interfaces.lifecycle.configure.{0}'.format(node_instance.id),
        operation_details=node_instance.node.operations['aria.interfaces.lifecycle.configure'],
        node_instance=node_instance
        )
    start_node_instance = context.operation(
        name='aria.interfaces.lifecycle.start.{0}'.format(node_instance.id),
        operation_details=node_instance.node.operations[
            'aria.interfaces.lifecycle.start'],
        node_instance=node_instance
    )
    graph.chain(tasks=[
        create_node_instance,
        preconfigure_relationship(context=context, node_instance=node_instance),
        configure_node_instance,
        postconfigure_relationship(context=context, node_instance=node_instance),
        start_node_instance,
        establish_relationship(context=context, node_instance=node_instance),
    ])


@workflow(suffix_template='{node_instance.id}')
def preconfigure_relationship(context, graph, node_instance):
    """

    :param context:
    :param graph:
    :param node_instance:
    :return:
    """
    graph.chain(tasks=relationships_tasks(
        operation_name='aria.interfaces.relationship_lifecycle.preconfigure',
        context=context,
        node_instance=node_instance))


@workflow(suffix_template='{node_instance.id}')
def postconfigure_relationship(context, graph, node_instance):
    """

    :param context:
    :param graph:
    :param node_instance:
    :return:
    """
    graph.chain(tasks=relationships_tasks(
        operation_name='aria.interfaces.relationship_lifecycle.postconfigure',
        context=context,
        node_instance=node_instance))


@workflow(suffix_template='{node_instance.id}')
def establish_relationship(context, graph, node_instance):
    """

    :param context:
    :param graph:
    :param node_instance:
    :return:
    """
    graph.chain(tasks=relationships_tasks(
        operation_name='aria.interfaces.relationship_lifecycle.establish',
        context=context,
        node_instance=node_instance))


# Uninstall node instance workflow and subworkflows

@workflow(suffix_template='{node_instance.id}')
def uninstall_node_instance(graph, context, node_instance):
    """
        A workflow which uninstalls a node instance.
        :param WorkflowContext context: the workflow context
        :param TaskGraph graph: the tasks graph of which to edit
        :param node_instance: the node instance to uninstall
        :return:
        """
    stop_node_instance = context.operation(
        name='aria.interfaces.lifecycle.stop.{0}'.format(node_instance.id),
        operation_details=node_instance.node.operations[
            'aria.interfaces.lifecycle.stop'],
        node_instance=node_instance
    )
    delete_node_instance = context.operation(
        name='aria.interfaces.lifecycle.delete.{0}'.format(node_instance.id),
        operation_details=node_instance.node.operations[
            'aria.interfaces.lifecycle.delete'],
        node_instance=node_instance
    )

    graph.chain(tasks=[
        stop_node_instance,
        unlink_relationship(context=context, node_instance=node_instance),
        delete_node_instance,
    ])


@workflow(suffix_template='{node_instance.id}')
def unlink_relationship(context, graph, node_instance):
    """

    :param context:
    :param graph:
    :param node_instance:
    :return:
    """
    tasks = relationships_tasks(
        operation_name='aria.interfaces.relationship_lifecycle.unlink',
        context=context,
        node_instance=node_instance
    )
    graph.chain(tasks=tasks)
    return tasks


@workflow(suffix_template='{node_instnace.id}.{operation}')
def execute_operation_on_instance(
        context,
        graph,
        node_instance,
        operation,
        operation_kwargs,
        allow_kwargs_override):
    """
    A workflow which executes a single operation
    :param WorkflowContext context: the workflow to execute.
    :param TaskGraph graph: the tasks graph of which to edit
    :param node_instance: the node instance to install
    :param basestring operation: the operation name
    :param dict operation_kwargs:
    :param bool allow_kwargs_override:
    :return:
    """

    if allow_kwargs_override is not None:
        operation_kwargs['allow_kwargs_override'] = allow_kwargs_override

    task_name = '{node_instance.id}.{operation_name}'.format(
        node_instance=node_instance,
        operation_name=operation)

    graph.add_task(
        context.operation(
            name=task_name,
            operation_details=node_instance.node.operations[operation],
            node_instance=node_instance,
            parameters=operation_kwargs)
    )


def relationships_tasks(operation_name, context, node_instance):
    """
    Creates a relationship task (source and target) for all of a node_instance relationships.
    :param basestring operation_name: the relationship operation name.
    :param WorkflowContext context:
    :param NodeInstance node_instance:
    :return:
    """
    relationships_groups = groupby(
        node_instance.relationship_instances,
        key=lambda relationship_instance: relationship_instance.relationship.target_id)

    sub_tasks = []
    for index, (_, relationship_group) in enumerate(relationships_groups):
        for relationship_instance in relationship_group:
            relationship_subgraph = relationship_tasks(
                node_instance=node_instance,
                relationship_instance=relationship_instance,
                context=context,
                operation_name=operation_name,
                index=index)
            sub_tasks.append(relationship_subgraph)
    return sub_tasks


def relationship_tasks(node_instance, relationship_instance, context, operation_name, index=None):
    """
    Creates a relationship task source and target.
    :param NodeInstance node_instance: the node instance of the relationship
    :param RelationshipInstance relationship_instance: the relationship instance itself
    :param WorkflowContext context:
    :param operation_name:
    :param index: the relationship index - enables pretty print
    :return:
    """
    index = index or node_instance.relationship_instances.index(relationship_instance)
    sub_workflow_name = '{name}.{index}.{node_instance.id}'.format(
        name=operation_name,
        index=index,
        node_instance=node_instance,
    )
    operation_name_template = '{name}.{index}.{{0}}.<{source_id}, {target_id}>'.format(
        name=operation_name,
        index=index,
        source_id=node_instance.id,
        target_id=relationship_instance.target_id,
    )
    source_operation = context.operation(
        name=operation_name_template.format('source'),
        node_instance=node_instance,
        operation_details=relationship_instance.relationship.source_operations[
            operation_name])
    target_operation = context.operation(
        name=operation_name_template.format('target'),
        node_instance=context.storage.node_instance.get(
            relationship_instance.target_id),
        operation_details=relationship_instance.relationship.target_operations[
            operation_name])
    sub_graph = context.task_graph(name=sub_workflow_name)
    sub_graph.add_task(source_operation)
    sub_graph.add_task(target_operation)
    return sub_graph
