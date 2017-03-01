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
Builtin execute_operation workflow
"""

from ..api.task import OperationTask
from ... import workflow


@workflow
def execute_operation(
        ctx,
        graph,
        operation,
        operation_kwargs,
        allow_kwargs_override,
        run_by_dependency_order,
        type_names,
        node_template_ids,
        node_ids,
        **kwargs):
    """
    The execute_operation workflow

    :param WorkflowContext workflow_context: the workflow context
    :param TaskGraph graph: the graph which will describe the workflow.
    :param basestring operation: the operation name to execute
    :param dict operation_kwargs:
    :param bool allow_kwargs_override:
    :param bool run_by_dependency_order:
    :param type_names:
    :param node_template_ids:
    :param node_ids:
    :param kwargs:
    :return:
    """
    subgraphs = {}
    # filtering node instances
    filtered_nodes = list(_filter_node_instances(
        context=ctx,
        node_template_ids=node_template_ids,
        node_ids=node_ids,
        type_names=type_names))

    if run_by_dependency_order:
        filtered_node_instances_ids = set(node_instance.id
                                          for node_instance in filtered_nodes)
        for node in ctx.node_instances:
            if node.id not in filtered_node_instances_ids:
                subgraphs[node.id] = ctx.task_graph(
                    name='execute_operation_stub_{0}'.format(node.id))

    # registering actual tasks to sequences
    for node in filtered_nodes:
        graph.add_tasks(
            _create_node_instance_task(
                node=node,
                operation=operation,
                operation_kwargs=operation_kwargs,
                allow_kwargs_override=allow_kwargs_override
            )
        )

    for _, node_instance_sub_workflow in subgraphs.items():
        graph.add_tasks(node_instance_sub_workflow)

    # adding tasks dependencies if required
    if run_by_dependency_order:
        for node in ctx.nodes:
            for relationship in node.relationships:
                graph.add_dependency(
                    source_task=subgraphs[node.id], after=[subgraphs[relationship.target_id]])


def _filter_node_instances(context, node_template_ids=(), node_ids=(), type_names=()):
    def _is_node_by_id(node_id):
        return not node_template_ids or node_id in node_template_ids

    def _is_node_instance_by_id(node_instance_id):
        return not node_ids or node_instance_id in node_ids

    def _is_node_by_type(node_type_hierarchy):
        return not type_names or node_type_hierarchy in type_names

    for node in context.nodes:
        if all((_is_node_by_id(node.node_template.id),
                _is_node_instance_by_id(node.id),
                _is_node_by_type(node.node_template.type_hierarchy))):
            yield node


def _create_node_instance_task(
        node,
        operation,
        operation_kwargs,
        allow_kwargs_override):
    """
    A workflow which executes a single operation
    :param node: the node instance to install
    :param basestring operation: the operation name
    :param dict operation_kwargs:
    :param bool allow_kwargs_override:
    :return:
    """

    if allow_kwargs_override is not None:
        operation_kwargs['allow_kwargs_override'] = allow_kwargs_override

    return OperationTask.for_node(
        node=node,
        interface_name=None, # TODO
        operation_name=operation,
        inputs=operation_kwargs)
