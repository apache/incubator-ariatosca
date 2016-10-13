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

from aria import workflow

from .uninstall import uninstall
from .install import install
from .workflows import relationship_tasks


@workflow
def heal(context, graph, node_instance_id):
    failing_node = context.storage.node_instance.get(node_instance_id)
    host_node = context.storage.node_instance.get(failing_node.host_id)
    failed_node_instance_subgraph = _get_contained_subgraph(context, host_node)
    failed_node_instance_ids = list(n.id for n in failed_node_instance_subgraph)

    targeted_node_instances = [
        context.storage.node_instance.get(relationship_instance.target_id)
        for node_instance in failed_node_instance_subgraph
        for relationship_instance in node_instance.relationship_instances
        if relationship_instance.target_id not in failed_node_instance_ids
    ]

    graph.chain([
        heal_uninstall(
            context=context,
            failing_node_instances=failed_node_instance_subgraph,
            targeted_node_instances=targeted_node_instances),
        heal_install(
            context=context,
            failing_node_instances=failed_node_instance_subgraph,
            targeted_node_instances=targeted_node_instances)
    ])


@workflow(suffix_template='{failing_node_instances}')
def heal_uninstall(context, graph, failing_node_instances, targeted_node_instances):
    node_instance_sub_workflows = {}

    # Create install stub workflow for each unaffected node instance
    for node_instance in targeted_node_instances:
        node_instance_sub_workflow = context.task_graph(
            name='uninstall_stub_{0}'.format(node_instance.id))
        node_instance_sub_workflows[node_instance.id] = node_instance_sub_workflow
        graph.add_task(node_instance_sub_workflow)

    # Create install sub workflow for each failing node
    uninstall(
        context=context,
        graph=graph,
        node_instances=failing_node_instances,
        node_instance_sub_workflows=node_instance_sub_workflows)

    # Add operations for intact nodes depending on a node instance
    # belonging to node_instances
    for node_instance in targeted_node_instances:
        node_instance_sub_workflow = node_instance_sub_workflows[node_instance.id]

        for relationship_instance in reversed(node_instance.relationship_instances):
            target_node_instance = context.storage.node_instance.get(
                relationship_instance.target_id)
            if target_node_instance in failing_node_instances:
                after_tasks = [node_instance_sub_workflows[relationship.target_id]
                               for relationship in node_instance.relationship_instances]

            elif target_node_instance in targeted_node_instances:
                after_tasks = [relationship_tasks(
                    node_instance=node_instance,
                    relationship_instance=relationship_instance,
                    context=context,
                    operation_name='cloudify.interfaces.relationship_lifecycle.unlink')]

            if after_tasks:
                graph.dependency(source_task=node_instance_sub_workflow, after=after_tasks)


@workflow(suffix_template='{failing_node_instances}')
def heal_install(context, graph, failing_node_instances, targeted_node_instances):
    node_instance_sub_workflows = {}

    # Create install sub workflow for each unaffected
    for node_instance in targeted_node_instances:
        node_instance_sub_workflow = context.task_graph(
            name='install_stub_{0}'.format(node_instance.id))
        node_instance_sub_workflows[node_instance.id] = node_instance_sub_workflow
        graph.add_task(node_instance_sub_workflow)

    # create install sub workflow for every node instance
    install(
        context=context,
        graph=graph,
        node_instances=failing_node_instances,
        node_instance_sub_workflows=node_instance_sub_workflows)

    # Add operations for intact nodes depending on a node instance
    # belonging to node_instances
    for node_instance in targeted_node_instances:
        node_instance_sub_workflow = node_instance_sub_workflows[node_instance.id]

        for relationship_instance in node_instance.relationship_instances:
            target_node_instance = context.storage.node_instance.get(
                relationship_instance.target_id)
            if target_node_instance in failing_node_instances:
                after_tasks = [node_instance_sub_workflows[relationship.target_id]
                               for relationship in node_instance.relationship_instances]

            elif target_node_instance in targeted_node_instances:
                after_tasks = [relationship_tasks(
                    node_instance=node_instance,
                    relationship_instance=relationship_instance,
                    context=context,
                    operation_name='cloudify.interfaces.relationship_lifecycle.establish')]
                
            if after_tasks:
                graph.dependency(source_task=node_instance_sub_workflow, after=after_tasks)


def _get_contained_subgraph(context, host_node_instance):
    contained_instances = set(node_instance
                              for node_instance in context.node_instances
                              if node_instance.host_id == host_node_instance.id and
                              node_instance.id != node_instance.host_id)
    result = {host_node_instance}

    if not contained_instances:
        return result

    result.update(contained_instances)
    for node_instance in contained_instances:
        result.update(_get_contained_subgraph(context, node_instance))

    return result


