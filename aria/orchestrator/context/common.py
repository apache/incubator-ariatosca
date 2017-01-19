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

import jinja2

from aria import logger
from aria.storage import exceptions


class BaseContext(logger.LoggerMixin):
    """
    Base context object for workflow and operation
    """

    def __init__(
            self,
            name,
            service_instance_id,
            model_storage,
            resource_storage,
            workdir=None,
            **kwargs):
        super(BaseContext, self).__init__(**kwargs)
        self._name = name
        self._id = str(uuid4())
        self._model = model_storage
        self._resource = resource_storage
        self._service_instance_id = service_instance_id
        self._workdir = workdir

    def __repr__(self):
        return (
            '{name}(name={self.name}, '
            'deployment_id={self._service_instance_id}, '
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
    def service_template(self):
        """
        The blueprint model
        """
        return self.service_instance.service_template

    @property
    def service_instance(self):
        """
        The deployment model
        """
        return self.model.service_instance.get(self._service_instance_id)

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
            self.resource.deployment.download(entry_id=str(self.service_instance.id),
                                              destination=destination,
                                              path=path)
        except exceptions.StorageError:
            self.resource.blueprint.download(entry_id=str(self.service_template.id),
                                             destination=destination,
                                             path=path)

    def download_resource_and_render(self, destination, path=None, variables=None):
        """
        Download a blueprint resource from the resource storage render its content as a jinja
        template using the provided variables. ctx is available to the template without providing it
        explicitly.
        """
        resource_content = self.get_resource(path=path)
        resource_content = self._render_resource(resource_content=resource_content,
                                                 variables=variables)
        with open(destination, 'wb') as f:
            f.write(resource_content)

    def get_resource(self, path=None):
        """
        Read a deployment resource as string from the resource storage
        """
        try:
            return self.resource.deployment.read(entry_id=str(self.service_instance.id), path=path)
        except exceptions.StorageError:
            return self.resource.deployment.read(entry_id=str(self.service_template.id), path=path)

    def get_resource_and_render(self, path=None, variables=None):
        """
        Read a deployment resource as string from the resource storage and render it as a jinja
        template using the provided variables. ctx is available to the template without providing it
        explicitly.
        """
        resource_content = self.get_resource(path=path)
        return self._render_resource(resource_content=resource_content, variables=variables)

    def _render_resource(self, resource_content, variables):
        variables = variables or {}
        if 'ctx' not in variables:
            variables['ctx'] = self
        resource_template = jinja2.Template(resource_content)
        return resource_template.render(variables)
