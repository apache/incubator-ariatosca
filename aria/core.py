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

from .modeling import models
from .modeling import utils as modeling_utils
from .exceptions import AriaException
from .parser.consumption import (
    ConsumptionContext,
    ConsumerChain,
    Read,
    Validate,
    ServiceTemplate)
from .parser.loading.location import UriLocation


class Core(object):

    def __init__(self,
                 model_storage,
                 resource_storage,
                 plugin_manager):
        self._model_storage = model_storage
        self._resource_storage = resource_storage
        self._plugin_manager = plugin_manager

    @property
    def model_storage(self):
        return self._model_storage

    @property
    def resource_storage(self):
        return self._resource_storage

    @property
    def plugin_manager(self):
        return self._plugin_manager

    def validate_service_template(self, service_template_path):
        self._parse_service_template(service_template_path)

    def create_service_template(self, service_template_path, service_template_dir,
                                service_template_name):
        context = self._parse_service_template(service_template_path)
        service_template = context.modeling.template
        service_template.name = service_template_name
        self.model_storage.service_template.put(service_template)
        self.resource_storage.service_template.upload(
            entry_id=str(service_template.id), source=service_template_dir)

    def delete_service_template(self, service_template_id):
        service_template = self.model_storage.service_template.get(service_template_id)
        if service_template.services.all():
            raise AriaException("Can't delete service template {0} - Service template has "
                                "existing services")

        self.model_storage.service_template.delete(service_template)
        self.resource_storage.service_template.delete(entry_id=str(service_template.id))

    def create_service(self, service_template_name, inputs, service_name=None):
        service_template = self.model_storage.service_template.get_by_name(service_template_name)

        # creating an empty ConsumptionContext, initiating a threadlocal context
        ConsumptionContext()
        with self.model_storage._all_api_kwargs['session'].no_autoflush:
            service = service_template.instantiate(None)

        template_inputs = service_template.inputs
        input_models = modeling_utils.create_inputs(inputs, template_inputs)
        service.inputs = {input.name: input for input in input_models}
        # TODO: now that we have inputs, we should scan properties and inputs and evaluate functions

        # first put the service model so it could have an id, as fallback for setting its name
        self.model_storage.service.put(service)
        service.name = service_name or '{0}_{1}'.format(service_template_name, service.id)
        self.model_storage.service.update(service)
        return service

    def delete_service(self, service_name, force=False):
        service = self.model_storage.service.get_by_name(service_name)

        running_executions = [e for e in service.executions
                              if e.status not in models.Execution.ACTIVE_STATES]
        if running_executions:
            raise AriaException("Can't delete service {0} - there is a running execution "
                                "for this service. Running execution id: {1}"
                                .format(service_name, running_executions[0].id))

        if not force:
            running_nodes = [n for n in service.nodes.values()
                             if n.state not in ('deleted', 'errored')]
            if running_nodes:
                raise AriaException("Can't delete service {0} - there are running nodes "
                                    "for this service. Running node ids: {1}"
                                    .format(service_name, running_nodes))

        self.model_storage.service.delete(service)

    @staticmethod
    def _parse_service_template(service_template_path):
        context = ConsumptionContext()
        context.presentation.location = UriLocation(service_template_path)
        ConsumerChain(context, (Read, Validate, ServiceTemplate)).consume()
        if context.validation.dump_issues():
            raise AriaException('Failed to parse service template')
        return context
