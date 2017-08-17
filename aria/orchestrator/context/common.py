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
Common code for contexts.
"""

import logging
from contextlib import contextmanager
from functools import partial

import jinja2

from aria import (
    logger as aria_logger,
    modeling
)
from aria.storage import exceptions

from ...utils.uuid import generate_uuid


class BaseContext(object):
    """
    Base class for contexts.
    """

    INSTRUMENTATION_FIELDS = (
        modeling.models.Service.inputs,
        modeling.models.ServiceTemplate.inputs,
        modeling.models.Policy.properties,
        modeling.models.PolicyTemplate.properties,
        modeling.models.Node.attributes,
        modeling.models.Node.properties,
        modeling.models.NodeTemplate.attributes,
        modeling.models.NodeTemplate.properties,
        modeling.models.Group.properties,
        modeling.models.GroupTemplate.properties,
        modeling.models.Capability.properties,
        # TODO ARIA-279: modeling.models.Capability.attributes,
        modeling.models.CapabilityTemplate.properties,
        # TODO ARIA-279: modeling.models.CapabilityTemplate.attributes
        modeling.models.Relationship.properties,
        modeling.models.Artifact.properties,
        modeling.models.ArtifactTemplate.properties,
        modeling.models.Interface.inputs,
        modeling.models.InterfaceTemplate.inputs,
        modeling.models.Operation.inputs,
        modeling.models.OperationTemplate.inputs
    )

    class PrefixedLogger(object):
        def __init__(self, base_logger, task_id=None):
            self._logger = base_logger
            self._task_id = task_id

        def __getattr__(self, attribute):
            if attribute.upper() in logging._levelNames:
                return partial(self._logger_with_task_id, _level=attribute)
            else:
                return getattr(self._logger, attribute)

        def _logger_with_task_id(self, *args, **kwargs):
            level = kwargs.pop('_level')
            kwargs.setdefault('extra', {})['task_id'] = self._task_id
            return getattr(self._logger, level)(*args, **kwargs)

    def __init__(self,
                 name,
                 service_id,
                 model_storage,
                 resource_storage,
                 execution_id,
                 workdir=None,
                 **kwargs):
        super(BaseContext, self).__init__(**kwargs)
        self._name = name
        self._id = generate_uuid(variant='uuid')
        self._model = model_storage
        self._resource = resource_storage
        self._service_id = service_id
        self._workdir = workdir
        self._execution_id = execution_id
        self.logger = None

    def _register_logger(self, level=None, task_id=None):
        self.logger = self.PrefixedLogger(
            logging.getLogger(aria_logger.TASK_LOGGER_NAME), task_id=task_id)
        self.logger.setLevel(level or logging.DEBUG)
        if not self.logger.handlers:
            self.logger.addHandler(self._get_sqla_handler())

    def _get_sqla_handler(self):
        return aria_logger.create_sqla_log_handler(model=self._model,
                                                   log_cls=modeling.models.Log,
                                                   execution_id=self._execution_id)

    def __repr__(self):
        return (                                                                                    # pylint: disable=redundant-keyword-arg
            u'{name}(name={self.name}, '
            u'deployment_id={self._service_id}, '
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
    def model(self):
        """
        Storage model API ("MAPI").
        """
        return self._model

    @property
    def resource(self):
        """
        Storage resource API ("RAPI").
        """
        return self._resource

    @property
    def service_template(self):
        """
        Service template model.
        """
        return self.service.service_template

    @property
    def service(self):
        """
        Service instance model.
        """
        return self.model.service.get(self._service_id)

    @property
    def name(self):
        """
        Operation name.
        """
        return self._name

    @property
    def id(self):
        """
        Operation ID.
        """
        return self._id

    def download_resource(self, destination, path=None):
        """
        Download a service template resource from the storage resource API ("RAPI").
        """
        try:
            self.resource.service.download(entry_id=str(self.service.id),
                                           destination=destination,
                                           path=path)
        except exceptions.StorageError:
            self.resource.service_template.download(entry_id=str(self.service_template.id),
                                                    destination=destination,
                                                    path=path)

    def download_resource_and_render(self, destination, path=None, variables=None):
        """
        Downloads a service template resource from the resource storage and renders its content as a
        Jinja template using the provided variables. ``ctx`` is available to the template without
        providing it explicitly.
        """
        resource_content = self.get_resource(path=path)
        resource_content = self._render_resource(resource_content=resource_content,
                                                 variables=variables)
        with open(destination, 'wb') as f:
            f.write(resource_content)

    def get_resource(self, path=None):
        """
        Reads a service instance resource as string from the resource storage.
        """
        try:
            return self.resource.service.read(entry_id=str(self.service.id), path=path)
        except exceptions.StorageError:
            return self.resource.service_template.read(entry_id=str(self.service_template.id),
                                                       path=path)

    def get_resource_and_render(self, path=None, variables=None):
        """
        Reads a service instance resource as string from the resource storage and renders it as a
        Jinja template using the provided variables. ``ctx`` is available to the template without
        providing it explicitly.
        """
        resource_content = self.get_resource(path=path)
        return self._render_resource(resource_content=resource_content, variables=variables)

    def _render_resource(self, resource_content, variables):
        variables = variables or {}
        variables.setdefault('ctx', self)
        resource_template = jinja2.Template(resource_content)
        return resource_template.render(variables)
