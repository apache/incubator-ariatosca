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
import logging
from contextlib import contextmanager
from datetime import datetime
from functools import partial
from uuid import uuid4

import jinja2

from aria import logger as aria_logger
from aria.storage import (
    exceptions,
    modeling
)


class BaseContext(object):
    """
    Base context object for workflow and operation
    """

    class PrefixedLogger(object):
        def __init__(self, logger, prefix=''):
            self._logger = logger
            self._prefix = prefix

        def __getattr__(self, item):
            if item.upper() in logging._levelNames:
                return partial(getattr(self._logger, item), extra={'prefix': self._prefix})
            else:
                return getattr(self._logger, item)

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
        self.logger = None

    def _create_execution(self):
        now = datetime.utcnow()
        execution = self.model.execution.model_cls(
            service_instance=self.service_instance,
            workflow_name=self._workflow_name,
            created_at=now,
            parameters=self.parameters,
        )
        self.model.execution.put(execution)
        return execution.id

    def _register_logger(self, logger_name=None, level=None):
        self.logger = self.PrefixedLogger(logging.getLogger(logger_name or self.__class__.__name__),
                                          self.logging_id)
        self.logger.addHandler(aria_logger.create_console_log_handler())
        self.logger.addHandler(self._get_sqla_handler())
        self.logger.setLevel(level or logging.DEBUG)

    def _get_sqla_handler(self):
        api_kwargs = {}
        if self._model._initiator:
            api_kwargs.update(self._model._initiator(**self._model._initiator_kwargs))
        api_kwargs.update(**self._model._api_kwargs)
        return aria_logger.create_sqla_log_handler(log_cls=modeling.model.Log,
                                                   execution_id=self._execution_id,
                                                   **api_kwargs)

    def __repr__(self):
        return (
            '{name}(name={self.name}, '
            'deployment_id={self._service_instance_id}, '
            .format(name=self.__class__.__name__, self=self))

    @contextmanager
    def logging_handlers(self, handlers=None):
        handlers = handlers or []
        try:
            for handler in handlers:
                self.logger.addHandler(handler)
            yield self.logger
        finally:
            for handler in handlers:
                self.logger.removeHandler(handler)

    @property
    def logging_id(self):
        raise NotImplementedError

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
