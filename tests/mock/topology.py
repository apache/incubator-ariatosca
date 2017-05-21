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
            function=create_operation,
            arguments={'key': aria_models.Argument.wrap('key', 'create'),
                       'value': aria_models.Argument.wrap('value', True)})
    )
    node_template.interface_templates[interface_template.name] = interface_template                 # pylint: disable=unsubscriptable-object

    node = models.create_node(node_template, service, name=models.DEPENDENCY_NODE_NAME)
    interface = models.create_interface(
        service,
        'Standard', 'create',
        operation_kwargs=dict(
            function=create_operation,
            arguments={'key': aria_models.Argument.wrap('key', 'create'),
                       'value': aria_models.Argument.wrap('value', True)})
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

    dependency_node = models.create_node(
        dependency_node_template, service, models.DEPENDENCY_NODE_NAME)
    dependent_node = models.create_node(
        dependent_node_template, service, models.DEPENDENT_NODE_NAME)

    dependent_node.outbound_relationships.append(models.create_relationship(                        # pylint: disable=no-member
        source=dependent_node,
        target=dependency_node
    ))

    model_storage.service_template.put(service_template)
    model_storage.service.put(service)

    return service.id


def create_simple_topology_three_nodes(model_storage):
    #################################################################################
    # Creating a simple deployment with the following topology:
    #               node1    <----|
    #                             | <- node0
    #               node2    <----|
    # meaning node0 has two relationships: node1 and node2 (one each).

    service_id = create_simple_topology_two_nodes(model_storage)
    service = model_storage.service.get(service_id)
    third_node_template = models.create_dependency_node_template(
        service.service_template, name='another_dependency_node_template')
    third_node = models.create_node(third_node_template, service, 'another_dependency_node')
    new_relationship = models.create_relationship(
        source=model_storage.node.get_by_name(models.DEPENDENT_NODE_NAME),
        target=third_node,
    )
    model_storage.relationship.put(new_relationship)

    return service_id
