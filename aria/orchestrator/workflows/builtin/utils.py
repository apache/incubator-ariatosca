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


def create_node_instance_task(operation_name, node_instance):
    """
    Returns a new operation task if the operation exists in the node instance, otherwise returns
    None.
    """

    if operation_name in node_instance.node.operations:
        return OperationTask.node_instance(instance=node_instance,
                                           name=operation_name)
    return None


def create_relationship_instance_tasks(operation_name, operations_attr, node_instance):
    """
    Returns a list of operation tasks for each outbound relationship of the node instance if
    the operation exists there.
    """

    sequence = []
    for relationship_instance in node_instance.outbound_relationship_instances:
        if operation_name in getattr(relationship_instance.relationship, operations_attr):
            sequence.append(
                OperationTask.relationship_instance(instance=relationship_instance,
                                                    name=operation_name,
                                                    operation_end=operations_attr))
    return sequence


def create_node_instance_task_dependencies(graph, tasks_and_node_instances, reverse=False):
    """
    Creates dependencies between tasks if there is an outbound relationship between their node
    instances.
    """

    def get_task(node_instance_id):
        for task, node_instance in tasks_and_node_instances:
            if node_instance.id == node_instance_id:
                return task
        return None

    for task, node_instance in tasks_and_node_instances:
        dependencies = []
        for relationship_instance in node_instance.outbound_relationship_instances:
            dependency = get_task(relationship_instance.target_node_instance.id)
            if dependency:
                dependencies.append(dependency)
        if dependencies:
            if reverse:
                for dependency in dependencies:
                    graph.add_dependency(dependency, task)
            else:
                graph.add_dependency(task, dependencies)
