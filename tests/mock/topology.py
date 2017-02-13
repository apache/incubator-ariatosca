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

from aria.storage.modeling import model

from . import models


def create_simple_topology_single_node(model_storage, create_operation):
    service_template = models.get_blueprint()
    model_storage.service_template.put(service_template)

    service_instance = models.get_deployment(service_template)
    model_storage.service_instance.put(service_instance)

    node_template = models.get_dependency_node(service_instance)
    node_template.interface_templates = [models.get_interface_template(
        'tosca.interfaces.node.lifecycle.Standard.create',
        operation_kwargs=dict(
            implementation=create_operation,
            inputs=[model.Parameter(name='key', str_value='create', type='str'),
                    model.Parameter(name='value', str_value=str(True), type='bool')]
        )
    )]
    model_storage.node_template.put(node_template)

    node = models.get_dependency_node_instance(node_template, service_instance)
    node.interfaces = [models.get_interface(
        'tosca.interfaces.node.lifecycle.Standard.create',
        operation_kwargs=dict(
            implementation=create_operation,
            inputs=[model.Parameter(name='key', str_value='create', type='str'),
                    model.Parameter(name='value', str_value=str(True), type='bool')])
    )]
    model_storage.node.put(node)


def create_simple_topology_two_nodes(model_storage):
    blueprint = models.get_blueprint()
    model_storage.service_template.put(blueprint)
    deployment = models.get_deployment(blueprint)
    model_storage.service_instance.put(deployment)

    #################################################################################
    # Creating a simple deployment with node -> node as a graph

    dependency_node = models.get_dependency_node(deployment)
    model_storage.node_template.put(dependency_node)
    storage_dependency_node = model_storage.node_template.get(dependency_node.id)

    dependency_node_instance = models.get_dependency_node_instance(storage_dependency_node,
                                                                   deployment)
    model_storage.node.put(dependency_node_instance)
    storage_dependency_node_instance = model_storage.node.get(dependency_node_instance.id)

    req_template, cap_template = models.get_relationship(storage_dependency_node)
    model_storage.requirement_template.put(req_template)
    model_storage.capability_template.put(cap_template)

    dependent_node = models.get_dependent_node(deployment, req_template, cap_template)
    model_storage.node_template.put(dependent_node)
    storage_dependent_node = model_storage.node_template.get(dependent_node.id)

    dependent_node_instance = models.get_dependent_node_instance(storage_dependent_node, deployment)
    model_storage.node.put(dependent_node_instance)
    storage_dependent_node_instance = model_storage.node.get(dependent_node_instance.id)

    relationship_instance = models.get_relationship_instance(
        target_instance=storage_dependency_node_instance,
        source_instance=storage_dependent_node_instance
    )
    model_storage.relationship.put(relationship_instance)

    return deployment.id
