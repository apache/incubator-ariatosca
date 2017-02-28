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

import aria
from aria.utils import file
from .common import BaseContext


class BaseOperationContext(BaseContext):
    """
    Context object used during operation creation and execution
    """

    def __init__(self,
                 name,
                 model_storage,
                 resource_storage,
                 service_id,
                 task_id,
                 actor_id,
                 **kwargs):
        super(BaseOperationContext, self).__init__(
            name=name,
            model_storage=model_storage,
            resource_storage=resource_storage,
            service_id=service_id,
            **kwargs)
        self._task_id = task_id
        self._actor_id = actor_id
        self._task = None

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
        if not self._task:
            self._task = self.model.task.get(self._task_id)
        return self._task

    @property
    def plugin_workdir(self):
        """
        A work directory that is unique to the plugin and the deployment id
        """
        if not self.task.plugin_name:
            return None
        plugin_workdir = '{0}/plugins/{1}/{2}'.format(self._workdir,
                                                      self.service.id,
                                                      self.task.plugin_name)
        file.makedirs(plugin_workdir)
        return plugin_workdir

    @property
    def serialization_dict(self):
        context_cls = self.__class__
        context_dict = {
            'name': self.name,
            'service_id': self._service_id,
            'task_id': self._task_id,
            'actor_id': self._actor_id,
            'workdir': self._workdir,
            'model_storage': self.model.serialization_dict if self.model else None,
            'resource_storage': self.resource.serialization_dict if self.resource else None
        }
        return {
            'context_cls': context_cls,
            'context': context_dict
        }

    @classmethod
    def deserialize_from_dict(cls, model_storage=None, resource_storage=None, **kwargs):
        if model_storage:
            model_storage = aria.application_model_storage(**model_storage)
        if resource_storage:
            resource_storage = aria.application_resource_storage(**resource_storage)

        return cls(model_storage=model_storage, resource_storage=resource_storage, **kwargs)


class NodeOperationContext(BaseOperationContext):
    """
    Context for node based operations.
    """
    @property
    def node_template(self):
        """
        the node of the current operation
        :return:
        """
        return self.node.node_template

    @property
    def node(self):
        """
        The node instance of the current operation
        :return:
        """
        return self.model.node.get(self._actor_id)


class RelationshipOperationContext(BaseOperationContext):
    """
    Context for relationship based operations.
    """
    @property
    def source_node_template(self):
        """
        The source node
        :return:
        """
        return self.source_node.node_template

    @property
    def source_node(self):
        """
        The source node instance
        :return:
        """
        return self.relationship.source_node

    @property
    def target_node_template(self):
        """
        The target node
        :return:
        """
        return self.target_node.node_template

    @property
    def target_node(self):
        """
        The target node instance
        :return:
        """
        return self.relationship.target_node

    @property
    def relationship(self):
        """
        The relationship instance of the current operation
        :return:
        """
        return self.model.relationship.get(self._actor_id)
