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
Provides with different tools for operations.
"""

from . import operation


class NodeToolBelt(object):
    """
    Node operation related tool belt
    """
    def __init__(self, operation_context):
        self._op_context = operation_context

    @property
    def dependent_node_instances(self):
        """
        Any node instance which has a relationship to the current node instance.
        :return:
        """
        assert isinstance(self._op_context, operation.NodeOperationContext)
        node_instances = self._op_context.model.node_instance.iter(
            filters={'deployment_id': self._op_context.deployment.id}
        )
        for node_instance in node_instances:
            for relationship_instance in node_instance.relationship_instances:
                if relationship_instance.target_id == self._op_context.node_instance.id:
                    yield node_instance

    @property
    def host_ip(self):
        """
        The host ip of the current node
        :return:
        """
        assert isinstance(self._op_context, operation.NodeOperationContext)
        host_id = self._op_context._actor.host_id
        host_instance = self._op_context.model.node_instance.get(host_id)
        return host_instance.runtime_properties.get('ip')


class RelationshipToolBelt(object):
    """
    Relationship operation related tool belt
    """
    def __init__(self, operation_context):
        self._op_context = operation_context


def toolbelt(operation_context):
    """
    Get a toolbelt according to the current operation executor
    :param operation_context:
    :return:
    """
    if isinstance(operation_context, operation.NodeOperationContext):
        return NodeToolBelt(operation_context)
    elif isinstance(operation_context, operation.RelationshipOperationContext):
        return RelationshipToolBelt(operation_context)
    else:
        raise RuntimeError("Operation context not supported")
