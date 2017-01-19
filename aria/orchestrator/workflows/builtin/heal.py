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
Builtin heal workflow
"""

from aria import workflow

from .workflows import (install_node, uninstall_node)
from ..api import task


@workflow
def heal(ctx, graph, node_instance_id):
    """
    The heal workflow

    :param WorkflowContext ctx: the workflow context
    :param TaskGraph graph: the graph which will describe the workflow.
    :param node_instance_id: the id of the node instance to heal
    :return:
    """
    failing_node = ctx.model.node.get(node_instance_id)
    host_node = ctx.model.node.get(failing_node.host.id)
    failed_node_instance_subgraph = _get_contained_subgraph(ctx, host_node)
    failed_node_instance_ids = list(n.id for n in failed_node_instance_subgraph)

    targeted_node_instances = [node_instance for node_instance in ctx.node_instances
                               if node_instance.id not in failed_node_instance_ids]

    uninstall_subgraph = task.WorkflowTask(
        heal_uninstall,
        failing_node_instances=failed_node_instance_subgraph,
        targeted_node_instances=targeted_node_instances
    )

    install_subgraph = task.WorkflowTask(
        heal_install,
        failing_node_instances=failed_node_instance_subgraph,
        targeted_node_instances=targeted_node_instances)

    graph.sequence(uninstall_subgraph, install_subgraph)


@workflow(suffix_template='{failing_node_instances}')
def heal_uninstall(ctx, graph, failing_node_instances, targeted_node_instances):
    """
    the uninstall part of the heal mechanism
    :param WorkflowContext ctx: the workflow context
    :param TaskGraph graph: the task graph to edit.
    :param failing_node_instances: the failing nodes to heal.
    :param targeted_node_instances: the targets of the relationships where the failing node are
    source
    :return:
    """
    node_instance_sub_workflows = {}

    # Create install stub workflow for each unaffected node instance
    for node_instance in targeted_node_instances:
        node_instance_stub = task.StubTask()
        node_instance_sub_workflows[node_instance.id] = node_instance_stub
        graph.add_tasks(node_instance_stub)

    # create install sub workflow for every node instance
    for node_instance in failing_node_instances:
        node_instance_sub_workflow = task.WorkflowTask(uninstall_node,
                                                       node_instance=node_instance)
        node_instance_sub_workflows[node_instance.id] = node_instance_sub_workflow
        graph.add_tasks(node_instance_sub_workflow)

    # create dependencies between the node instance sub workflow
    for node_instance in failing_node_instances:
        node_instance_sub_workflow = node_instance_sub_workflows[node_instance.id]
        for relationship_instance in reversed(node_instance.outbound_relationship_instances):
            graph.add_dependency(
                node_instance_sub_workflows[relationship_instance.target_node_instance.id],
                node_instance_sub_workflow)

    # Add operations for intact nodes depending on a node instance belonging to node_instances
    for node_instance in targeted_node_instances:
        node_instance_sub_workflow = node_instance_sub_workflows[node_instance.id]

        for relationship_instance in reversed(node_instance.outbound_relationship_instances):

            target_node_instance = \
                ctx.model.node.get(relationship_instance.target_node_instance.id)
            target_node_instance_subgraph = node_instance_sub_workflows[target_node_instance.id]
            graph.add_dependency(target_node_instance_subgraph, node_instance_sub_workflow)

            if target_node_instance in failing_node_instances:
                dependency = relationship_tasks(
                    relationship_instance=relationship_instance,
                    operation_name='aria.interfaces.relationship_lifecycle.unlink')
                graph.add_tasks(*dependency)
                graph.add_dependency(node_instance_sub_workflow, dependency)


@workflow(suffix_template='{failing_node_instances}')
def heal_install(ctx, graph, failing_node_instances, targeted_node_instances):
    """
    the install part of the heal mechanism
    :param WorkflowContext ctx: the workflow context
    :param TaskGraph graph: the task graph to edit.
    :param failing_node_instances: the failing nodes to heal.
    :param targeted_node_instances: the targets of the relationships where the failing node are
    source
    :return:
    """
    node_instance_sub_workflows = {}

    # Create install sub workflow for each unaffected
    for node_instance in targeted_node_instances:
        node_instance_stub = task.StubTask()
        node_instance_sub_workflows[node_instance.id] = node_instance_stub
        graph.add_tasks(node_instance_stub)

    # create install sub workflow for every node instance
    for node_instance in failing_node_instances:
        node_instance_sub_workflow = task.WorkflowTask(install_node,
                                                       node_instance=node_instance)
        node_instance_sub_workflows[node_instance.id] = node_instance_sub_workflow
        graph.add_tasks(node_instance_sub_workflow)

    # create dependencies between the node instance sub workflow
    for node_instance in failing_node_instances:
        node_instance_sub_workflow = node_instance_sub_workflows[node_instance.id]
        if node_instance.outbound_relationship_instances:
            dependencies = \
                [node_instance_sub_workflows[relationship_instance.target_node_instance.id]
                 for relationship_instance in node_instance.outbound_relationship_instances]
            graph.add_dependency(node_instance_sub_workflow, dependencies)

    # Add operations for intact nodes depending on a node instance
    # belonging to node_instances
    for node_instance in targeted_node_instances:
        node_instance_sub_workflow = node_instance_sub_workflows[node_instance.id]

        for relationship_instance in node_instance.outbound_relationship_instances:
            target_node_instance = ctx.model.node.get(
                relationship_instance.target_node_instance.id)
            target_node_instance_subworkflow = node_instance_sub_workflows[target_node_instance.id]
            graph.add_dependency(node_instance_sub_workflow, target_node_instance_subworkflow)

            if target_node_instance in failing_node_instances:
                dependent = relationship_tasks(
                    relationship_instance=relationship_instance,
                    operation_name='aria.interfaces.relationship_lifecycle.establish')
                graph.add_tasks(*dependent)
                graph.add_dependency(dependent, node_instance_sub_workflow)


def _get_contained_subgraph(context, host_node_instance):
    contained_instances = [node_instance
                           for node_instance in context.node_instances
                           if node_instance.host_fk == host_node_instance.id and
                           node_instance.host_fk != node_instance.id]
    result = [host_node_instance]

    if not contained_instances:
        return result

    result.extend(contained_instances)
    for node_instance in contained_instances:
        result.extend(_get_contained_subgraph(context, node_instance))

    return set(result)
