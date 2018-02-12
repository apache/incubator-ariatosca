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
ARIA core module.
"""

from . import exceptions
from .parser import consumption
from .parser.loading.location import UriLocation
from .orchestrator import topology
from .utils import collections


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
        self.parse_service_template(service_template_path)

    def create_service_template(self, service_template_path, service_template_dir,
                                service_template_name):
        context = self.parse_service_template(service_template_path)
        service_template = context.modeling.template
        service_template.name = service_template_name
        self.model_storage.service_template.put(service_template)
        self.resource_storage.service_template.upload(
            entry_id=str(service_template.id), source=service_template_dir)
        return service_template

    def delete_service_template(self, service_template_id):
        service_template = self.model_storage.service_template.get(service_template_id)
        if service_template.services:
            raise exceptions.DependentServicesError(
                'Can\'t delete service template `{0}` - service template has existing services'
                .format(service_template.name))

        self.model_storage.service_template.delete(service_template)
        self.resource_storage.service_template.delete(entry_id=str(service_template.id))

    def create_service(self, service_template_id, inputs, service_name=None):
        service_template = self.model_storage.service_template.get(service_template_id)

        storage_session = self.model_storage._all_api_kwargs['session']
        # setting no autoflush for the duration of instantiation - this helps avoid dependency
        # constraints as they're being set up
        with storage_session.no_autoflush:
            topology_ = topology.Topology()
            service = topology_.instantiate(
                service_template, inputs=inputs, plugins=self.model_storage.plugin.list())
            topology_.coerce(service, report_issues=True)

            topology_.validate(service)
            topology_.satisfy_requirements(service)
            topology_.coerce(service, report_issues=True)

            topology_.validate_capabilities(service)
            topology_.assign_hosts(service)
            topology_.configure_operations(service)
            topology_.coerce(service, report_issues=True)
            if topology_.dump_issues():
                raise exceptions.InstantiationError('Failed to instantiate service template `{0}`'
                                                    .format(service_template.name))

        storage_session.flush()  # flushing so service.id would auto-populate
        service.name = service_name or '{0}_{1}'.format(service_template.name, service.id)
        self.model_storage.service.put(service)
        return service

    def delete_service(self, service_id, force=False):
        service = self.model_storage.service.get(service_id)

        active_executions = [e for e in service.executions if e.is_active()]
        if active_executions:
            raise exceptions.DependentActiveExecutionsError(
                'Can\'t delete service `{0}` - there is an active execution for this service. '
                'Active execution ID: {1}'.format(service.name, active_executions[0].id))

        if not force:
            available_nodes = [str(n.id) for n in service.nodes.itervalues() if n.is_available()]
            if available_nodes:
                raise exceptions.DependentAvailableNodesError(
                    'Can\'t delete service `{0}` - there are available nodes for this service. '
                    'Available node IDs: {1}'.format(service.name, ', '.join(available_nodes)))

        self.model_storage.service.delete(service)

    def parse_service_template(self, service_template_path):
        plugin_dir = self.plugin_manager._plugins_dir
        context = consumption.ConsumptionContext()
        context.presentation.location = UriLocation(service_template_path)
        #Add plugin resource storage to import location prefixes
        context.loading.prefixes = collections.StrictList([plugin_dir])
        # Most of the parser uses the topology package in order to manipulate the models.
        # However, here we use the Consumer mechanism, but this should change in the future.
        consumption.ConsumerChain(
            context,
            (
                consumption.Read,
                consumption.Validate,
                consumption.ServiceTemplate
            )).consume()
        if context.validation.dump_issues():
            raise exceptions.ParsingError('Failed to parse service template')
        return context
