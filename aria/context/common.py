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
A common context for both workflow and operation
"""
from uuid import uuid4

from .. import (
    logger,
    exceptions,
)
from ..tools.lru_cache import lru_cache


class BaseContext(logger.LoggerMixin):
    """
    Base context object for workflow and operation
    """

    def __init__(
            self,
            name,
            model_storage,
            resource_storage,
            deployment_id,
            workflow_id,
            execution_id=None,
            task_max_attempts=1,
            task_retry_interval=0,
            task_ignore_failure=False,
            **kwargs):
        super(BaseContext, self).__init__(**kwargs)
        self._name = name
        self._id = str(uuid4())
        self._model = model_storage
        self._resource = resource_storage
        self._deployment_id = deployment_id
        self._workflow_id = workflow_id
        self._execution_id = execution_id or str(uuid4())
        self._task_max_attempts = task_max_attempts
        self._task_retry_interval = task_retry_interval
        self._task_ignore_failure = task_ignore_failure

    def __repr__(self):
        return (
            '{name}(name={self.name}, '
            'deployment_id={self._deployment_id}, '
            'workflow_id={self._workflow_id}, '
            'execution_id={self._execution_id})'
            .format(name=self.__class__.__name__, self=self))

    @property
    def model(self):
        """
        Access to the model storage
        :return:
        """
        return self._model

    @property
    def resource(self):
        """
        Access to the resource storage
        :return:
        """
        return self._resource

    @property
    @lru_cache()
    def blueprint(self):
        """
        The blueprint model
        """
        return self.model.blueprint.get(self.deployment.blueprint_id)

    @property
    @lru_cache()
    def deployment(self):
        """
        The deployment model
        """
        return self.model.deployment.get(self._deployment_id)

    @property
    def execution(self):
        """
        The execution model
        """
        return self.model.execution.get(self._execution_id)

    @execution.setter
    def execution(self, value):
        """
        Store the execution in the model storage
        """
        self.model.execution.store(value)

    @property
    def name(self):
        """
        The operation name
        :return:
        """
        return self._name

    @property
    def id(self):
        """
        The operation id
        :return:
        """
        return self._id

    def download_resource(self, destination, path=None):
        """
        Download a blueprint resource from the resource storage
        """
        try:
            return self.resource.deployment.download(entry_id=self.deployment.id,
                                                     destination=destination,
                                                     path=path)
        except exceptions.StorageError:
            return self.resource.blueprint.download(entry_id=self.blueprint.id,
                                                    destination=destination,
                                                    path=path)

    @lru_cache()
    def get_resource(self, path=None):
        """
        Read a deployment resource as string from the resource storage
        """
        try:
            return self.resource.deployment.data(entry_id=self.deployment.id, path=path)
        except exceptions.StorageError:
            return self.resource.blueprint.data(entry_id=self.blueprint.id, path=path)
