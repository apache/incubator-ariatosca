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
Builtin uninstall workflow
"""

from aria import workflow

from .workflows import uninstall_node_instance


@workflow
def uninstall(context, graph, node_instances=(), node_instance_sub_workflows=None):
    """
    The uninstall workflow
    :param WorkflowContext context: the workflow context
    :param TaskGraph graph: the graph which will describe the workflow.
    :param node_instances: the node instances on which to run the workflow
    :param dict node_instance_sub_workflows: a dictionary of subworkflows  with id as key and
    TaskGraph (or OperationContext) as value
    :return:
    """
    node_instance_sub_workflows = node_instance_sub_workflows or {}
    node_instances = node_instances or list(context.node_instances)

    # create install sub workflow for every node instance
    for node_instance in node_instances:
        node_instance_sub_workflow = uninstall_node_instance(
            context=context,
            node_instance=node_instance)
        node_instance_sub_workflows[node_instance.id] = node_instance_sub_workflow
        graph.add_task(node_instance_sub_workflow)

    # create dependencies between the node instance sub workflow
    for node_instance in node_instances:
        node_instance_sub_workflow = node_instance_sub_workflows[node_instance.id]
        for relationship_instance in reversed(node_instance.relationship_instances):
            graph.dependency(
                source_task=node_instance_sub_workflows[relationship_instance.target_id],
                after=[node_instance_sub_workflow])
