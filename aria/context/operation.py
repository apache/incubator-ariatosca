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
Workflow and operation contexts
"""


from .common import BaseContext


class BaseOperationContext(BaseContext):
    """
    Context object used during operation creation and execution
    """

    def __init__(self, name, workflow_context, task, **kwargs):
        super(BaseOperationContext, self).__init__(
            name=name,
            model_storage=workflow_context.model,
            resource_storage=workflow_context.resource,
            deployment_id=workflow_context._deployment_id,
            workflow_id=workflow_context._workflow_id,
            execution_id=workflow_context._execution_id,
            **kwargs)
        self._task_model = task
        self._actor = self.task.actor

    def __repr__(self):
        details = 'operation_mapping={task.operation_mapping}; ' \
                  'operation_inputs={task.inputs}'\
            .format(task=self.task)
        return '{name}({0})'.format(details, name=self.name)

    @property
    def task(self):
        """
        The task in the model storage
        :return: Task model
        """
        return self._task_model


class NodeOperationContext(BaseOperationContext):
    """
    Context for node based operations.
    """
    @property
    def node(self):
        """
        the node of the current operation
        :return:
        """
        return self._actor.node

    @property
    def node_instance(self):
        """
        The node instance of the current operation
        :return:
        """
        return self._actor


class RelationshipOperationContext(BaseOperationContext):
    """
    Context for relationship based operations.
    """
    @property
    def source_node(self):
        """
        The source node
        :return:
        """
        return self.model.node.get(self.relationship.source_id)

    @property
    def source_node_instance(self):
        """
        The source node instance
        :return:
        """
        return self.model.node_instance.get(self.relationship_instance.source_id)

    @property
    def target_node(self):
        """
        The target node
        :return:
        """
        return self.model.node.get(self.relationship.target_id)

    @property
    def target_node_instance(self):
        """
        The target node instance
        :return:
        """
        return self.model.node_instance.get(self._actor.target_id)

    @property
    def relationship(self):
        """
        The relationship of the current operation
        :return:
        """
        return self._actor.relationship

    @property
    def relationship_instance(self):
        """
        The relationship instance of the current operation
        :return:
        """
        return self._actor
