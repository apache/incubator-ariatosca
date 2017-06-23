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

# pylint: skip-file

"""
Built-in heal workflow.
"""

from aria import workflow

from .workflows import (install_node, uninstall_node)
from ..api import task


@workflow
def heal(ctx, graph, node_id):
    """
    Built-in heal workflow..

    :param ctx: workflow context
    :param graph: graph which will describe the workflow.
    :param node_id: ID of the node to heal
    :return:
    """
    failing_node = ctx.model.node.get(node_id)
    host_node = ctx.model.node.get(failing_node.host.id)
    failed_node_subgraph = _get_contained_subgraph(ctx, host_node)
    failed_node_ids = list(n.id for n in failed_node_subgraph)

    targeted_nodes = [node for node in ctx.nodes
                               if node.id not in failed_node_ids]

    uninstall_subgraph = task.WorkflowTask(
        heal_uninstall,
        failing_nodes=failed_node_subgraph,
        targeted_nodes=targeted_nodes
    )

    install_subgraph = task.WorkflowTask(
        heal_install,
        failing_nodes=failed_node_subgraph,
        targeted_nodes=targeted_nodes)

    graph.sequence(uninstall_subgraph, install_subgraph)


@workflow(suffix_template='{failing_nodes}')
def heal_uninstall(ctx, graph, failing_nodes, targeted_nodes):
    """
    Uninstall phase of the heal mechanism.

    :param ctx: workflow context
    :param graph: task graph to edit
    :param failing_nodes: failing nodes to heal
    :param targeted_nodes: targets of the relationships where the failing node are
    """
    node_sub_workflows = {}

    # Create install stub workflow for each unaffected node
    for node in targeted_nodes:
        node_stub = task.StubTask()
        node_sub_workflows[node.id] = node_stub
        graph.add_tasks(node_stub)

    # create install sub workflow for every node
    for node in failing_nodes:
        node_sub_workflow = task.WorkflowTask(uninstall_node,
                                                       node=node)
        node_sub_workflows[node.id] = node_sub_workflow
        graph.add_tasks(node_sub_workflow)

    # create dependencies between the node sub workflow
    for node in failing_nodes:
        node_sub_workflow = node_sub_workflows[node.id]
        for relationship in reversed(node.outbound_relationships):
            graph.add_dependency(
                node_sub_workflows[relationship.target_node.id],
                node_sub_workflow)

    # Add operations for intact nodes depending on a node belonging to nodes
    for node in targeted_nodes:
        node_sub_workflow = node_sub_workflows[node.id]

        for relationship in reversed(node.outbound_relationships):

            target_node = \
                ctx.model.node.get(relationship.target_node.id)
            target_node_subgraph = node_sub_workflows[target_node.id]
            graph.add_dependency(target_node_subgraph, node_sub_workflow)

            if target_node in failing_nodes:
                dependency = task.create_relationship_tasks(
                    relationship=relationship,
                    operation_name='aria.interfaces.relationship_lifecycle.unlink')
                graph.add_tasks(*dependency)
                graph.add_dependency(node_sub_workflow, dependency)


@workflow(suffix_template='{failing_nodes}')
def heal_install(ctx, graph, failing_nodes, targeted_nodes):
    """
    Install phase of the heal mechanism.

    :param ctx: workflow context
    :param graph: task graph to edit.
    :param failing_nodes: failing nodes to heal
    :param targeted_nodes: targets of the relationships where the failing node are
    """
    node_sub_workflows = {}

    # Create install sub workflow for each unaffected
    for node in targeted_nodes:
        node_stub = task.StubTask()
        node_sub_workflows[node.id] = node_stub
        graph.add_tasks(node_stub)

    # create install sub workflow for every node
    for node in failing_nodes:
        node_sub_workflow = task.WorkflowTask(install_node,
                                                       node=node)
        node_sub_workflows[node.id] = node_sub_workflow
        graph.add_tasks(node_sub_workflow)

    # create dependencies between the node sub workflow
    for node in failing_nodes:
        node_sub_workflow = node_sub_workflows[node.id]
        if node.outbound_relationships:
            dependencies = \
                [node_sub_workflows[relationship.target_node.id]
                 for relationship in node.outbound_relationships]
            graph.add_dependency(node_sub_workflow, dependencies)

    # Add operations for intact nodes depending on a node
    # belonging to nodes
    for node in targeted_nodes:
        node_sub_workflow = node_sub_workflows[node.id]

        for relationship in node.outbound_relationships:
            target_node = ctx.model.node.get(
                relationship.target_node.id)
            target_node_subworkflow = node_sub_workflows[target_node.id]
            graph.add_dependency(node_sub_workflow, target_node_subworkflow)

            if target_node in failing_nodes:
                dependent = task.create_relationship_tasks(
                    relationship=relationship,
                    operation_name='aria.interfaces.relationship_lifecycle.establish')
                graph.add_tasks(*dependent)
                graph.add_dependency(dependent, node_sub_workflow)


def _get_contained_subgraph(context, host_node):
    contained_instances = [node
                           for node in context.nodes
                           if node.host_fk == host_node.id and
                           node.host_fk != node.id]
    result = [host_node]

    if not contained_instances:
        return result

    result.extend(contained_instances)
    for node in contained_instances:
        result.extend(_get_contained_subgraph(context, node))

    return set(result)
