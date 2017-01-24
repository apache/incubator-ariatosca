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

def create_node_tasks(ctx, graph, operation_name, relationship_source_operation=None,
                      relationship_target_operation=None):
    for node_instance in ctx.model.node_instance.iter():
        if relationship_source_operation:
            create_relationship_tasks(ctx, graph, relationship_source_operation,
                                      node_instance, 'source_operations')

        if operation_name in node_instance.node.operations:
            task = create_node_instance_task(node_instance, operation_name)
            graph.add_tasks(task)

        if relationship_target_operation:
            create_relationship_tasks(ctx, graph, relationship_target_operation,
                                      node_instance, 'target_operations')

def create_relationship_tasks(ctx, graph, operation_name, node_instance, operations_attr):
    for relationship_instance in ctx.model.relationship_instance.iter():
        if relationship_instance.source_node_instance.id == node_instance.id:
            if operation_name in getattr(relationship_instance.relationship, operations_attr):
                task = create_relationship_instance_task(relationship_instance,
                                                         operation_name,
                                                         operations_attr)
                graph.add_tasks(task)

def create_node_instance_task(node_instance, operation_name): # pylint: disable=no-self-use
    return OperationTask.node_instance(
        instance=node_instance,
        name=operation_name,
        inputs=None,
        max_attempts=None,
        retry_interval=None,
        ignore_failure=None)

def create_relationship_instance_task(relationship_instance, operation_name, end): # pylint: disable=no-self-use
    return OperationTask.relationship_instance(
        instance=relationship_instance,
        name=operation_name,
        operation_end=end,
        inputs=None,
        max_attempts=None,
        retry_interval=None,
        ignore_failure=None)
