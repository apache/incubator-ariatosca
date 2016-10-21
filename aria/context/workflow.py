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

import threading
from uuid import uuid4
from contextlib import contextmanager

from .. import logger
from ..tools.lru_cache import lru_cache
from .. import exceptions


class ContextException(exceptions.AriaError):
    """
    Context based exception
    """
    pass


class WorkflowContext(logger.LoggerMixin):
    """
    Context object used during workflow creation and execution
    """

    def __init__(
            self,
            name,
            model_storage,
            resource_storage,
            deployment_id,
            workflow_id,
            execution_id=None,
            parameters=None,
            **kwargs):
        super(WorkflowContext, self).__init__(**kwargs)
        self.name = name
        self.id = str(uuid4())
        self.model = model_storage
        self.resource = resource_storage
        self.deployment_id = deployment_id
        self.workflow_id = workflow_id
        self.execution_id = execution_id or str(uuid4())
        self.parameters = parameters or {}

    def __repr__(self):
        return (
            '{name}(deployment_id={self.deployment_id}, '
            'workflow_id={self.workflow_id}, '
            'execution_id={self.execution_id})'.format(
                name=self.__class__.__name__, self=self))

    @property
    def blueprint_id(self):
        """
        The blueprint id
        """
        return self.deployment.blueprint_id

    @property
    @lru_cache()
    def blueprint(self):
        """
        The blueprint model
        """
        return self.model.blueprint.get(self.blueprint_id)

    @property
    @lru_cache()
    def deployment(self):
        """
        The deployment model
        """
        return self.model.deployment.get(self.deployment_id)

    @property
    def nodes(self):
        """
        Iterator over nodes
        """
        return self.model.node.iter(
            filters={'blueprint_id': self.blueprint_id})

    @property
    def node_instances(self):
        """
        Iterator over node instances
        """
        return self.model.node_instance.iter(filters={'deployment_id': self.deployment_id})

    @property
    def execution(self):
        """
        The execution model
        """
        return self.model.execution.get(self.execution_id)

    @execution.setter
    def execution(self, value):
        """
        Store the execution in the model storage
        """
        self.model.execution.store(value)

    def download_blueprint_resource(self, destination, path=None):
        """
        Download a blueprint resource from the resource storage
        """
        return self.resource.blueprint.download(
            entry_id=self.blueprint_id,
            destination=destination,
            path=path)

    def download_deployment_resource(self, destination, path=None):
        """
        Download a deployment resource from the resource storage
        """
        return self.resource.deployment.download(
            entry_id=self.deployment_id,
            destination=destination,
            path=path)

    @lru_cache()
    def get_deployment_resource_data(self, path=None):
        """
        Read a deployment resource as string from the resource storage
        """
        return self.resource.deployment.data(entry_id=self.deployment_id, path=path)

    @lru_cache()
    def get_blueprint_resource_data(self, path=None):
        """
        Read a blueprint resource as string from the resource storage
        """
        return self.resource.blueprint.data(entry_id=self.blueprint_id, path=path)


class _CurrentContext(threading.local):
    """
    Provides thread-level context, which sugarcoats the task api.
    """

    def __init__(self):
        super(_CurrentContext, self).__init__()
        self._workflow_context = None

    def _set(self, value):
        self._workflow_context = value

    def get(self):
        """
        Retrieves the current workflow context
        :return: the workflow context
        :rtype: WorkflowContext
        """
        if self._workflow_context is not None:
            return self._workflow_context
        raise ContextException("No context was set")

    @contextmanager
    def push(self, workflow_context):
        """
        Switches the current context to the provided context
        :param workflow_context: the context to switch to.
        :yields: the current context
        """
        prev_workflow_context = self._workflow_context
        self._set(workflow_context)
        try:
            yield self
        finally:
            self._set(prev_workflow_context)

current = _CurrentContext()

