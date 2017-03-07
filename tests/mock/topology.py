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

from aria.modeling import models as aria_models

from . import models


def create_simple_topology_single_node(model_storage, create_operation):
    service_template = models.create_service_template()
    service = models.create_service(service_template)

    node_template = models.create_dependency_node_template(service_template)
    interface_template = models.create_interface_template(
        service_template,
        'Standard', 'create',
        operation_kwargs=dict(
            implementation=create_operation,
            inputs={'key': aria_models.Parameter(name='key', value='create', type_name='string'),
                    'value': aria_models.Parameter(name='value', value=True, type_name='boolean')})
    )
    node_template.interface_templates[interface_template.name] = interface_template                 # pylint: disable=unsubscriptable-object

    node = models.create_dependency_node(node_template, service)
    interface = models.create_interface(
        service,
        'Standard', 'create',
        operation_kwargs=dict(
            implementation=create_operation,
            inputs={'key': aria_models.Parameter(name='key', value='create', type_name='string'),
                    'value': aria_models.Parameter(name='value', value=True, type_name='boolean')})
    )
    node.interfaces[interface.name] = interface                                                     # pylint: disable=unsubscriptable-object

    model_storage.service_template.put(service_template)
    model_storage.service.put(service)


def create_simple_topology_two_nodes(model_storage):
    service_template = models.create_service_template()
    service = models.create_service(service_template)

    # Creating a simple service with node -> node as a graph

    dependency_node_template = models.create_dependency_node_template(service_template)
    dependent_node_template = models.create_dependent_node_template(service_template,
                                                                    dependency_node_template)

    dependency_node = models.create_dependency_node(dependency_node_template, service)
    dependent_node = models.create_dependent_node(dependent_node_template, service)

    dependent_node.outbound_relationships.append(models.create_relationship(                        # pylint: disable=no-member
        source=dependent_node,
        target=dependency_node
    ))

    model_storage.service_template.put(service_template)
    model_storage.service.put(service)

    return service.id
