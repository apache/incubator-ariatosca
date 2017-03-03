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
    model_storage.service_template.put(service_template)

    service = models.create_service(service_template)
    model_storage.service.put(service)

    node_template = models.create_dependency_node_template(service)
    node_template.interface_templates = [models.create_interface_template(
        'tosca.interfaces.node.lifecycle.Standard.create',
        operation_kwargs=dict(
            implementation=create_operation,
            inputs=[aria_models.Parameter(name='key', value='create', type_name='string'),
                    aria_models.Parameter(name='value', value=True, type_name='boolean')]
        )
    )]
    model_storage.node_template.put(node_template)

    node = models.create_dependency_node(node_template, service)
    node.interfaces = [models.create_interface(
        'tosca.interfaces.node.lifecycle.Standard.create',
        operation_kwargs=dict(
            implementation=create_operation,
            inputs=[aria_models.Parameter(name='key', value='create', type_name='string'),
                    aria_models.Parameter(name='value', value=True, type_name='boolean')])
    )]
    model_storage.node.put(node)


def create_simple_topology_two_nodes(model_storage):
    blueprint = models.create_service_template()
    model_storage.service_template.put(blueprint)
    deployment = models.create_service(blueprint)
    model_storage.service.put(deployment)

    #################################################################################
    # Creating a simple deployment with node -> node as a graph

    dependency_node = models.create_dependency_node_template(deployment)
    model_storage.node_template.put(dependency_node)
    storage_dependency_node = model_storage.node_template.get(dependency_node.id)

    dependency_node_instance = models.create_dependency_node(storage_dependency_node,
                                                                   deployment)
    model_storage.node.put(dependency_node_instance)
    storage_dependency_node_instance = model_storage.node.get(dependency_node_instance.id)

    req_template, cap_template = models.create_requirement(storage_dependency_node)
    model_storage.requirement_template.put(req_template)
    model_storage.capability_template.put(cap_template)

    dependent_node = models.create_dependent_node_template(deployment, req_template, cap_template)
    model_storage.node_template.put(dependent_node)
    storage_dependent_node = model_storage.node_template.get(dependent_node.id)

    dependent_node_instance = models.create_dependent_node(storage_dependent_node, deployment)
    model_storage.node.put(dependent_node_instance)
    storage_dependent_node_instance = model_storage.node.get(dependent_node_instance.id)

    relationship_instance = models.create_relationship(
        target_instance=storage_dependency_node_instance,
        source_instance=storage_dependent_node_instance
    )
    model_storage.relationship.put(relationship_instance)

    return deployment.id
