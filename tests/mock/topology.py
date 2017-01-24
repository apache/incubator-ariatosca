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

from datetime import datetime

from aria.storage import model

from . import models


def create_simple_topology_single_node(model_storage, deployment_id, create_operation):
    now = datetime.utcnow()

    blueprint = model.Blueprint(name='mock-blueprint',
                                created_at=now,
                                updated_at=now,
                                plan={},
                                main_file_name='mock-file')
    model_storage.blueprint.put(blueprint)

    deployment = model.Deployment(name='mock-deployment-%d' % deployment_id,
                                  blueprint_fk=blueprint.id,
                                  created_at=now,
                                  updated_at=now)
    model_storage.deployment.put(deployment)

    node = model.Node(name='mock-node',
                      type='tosca.nodes.Compute',
                      operations={
                          'tosca.interfaces.node.lifecycle.Standard.create': {
                              'operation': create_operation,
                              'inputs': {
                                  'key': 'create',
                                  'value': True}}},
                      number_of_instances=1,
                      planned_number_of_instances=1,
                      deploy_number_of_instances=1,
                      min_number_of_instances=1,
                      max_number_of_instances=1,
                      deployment_fk=deployment.id)
    model_storage.node.put(node)

    node_instance = model.NodeInstance(name='mock-node-instance',
                                       state='',
                                       node_fk=node.id)
    model_storage.node_instance.put(node_instance)


def create_simple_topology_two_nodes(model_storage):
    blueprint = models.get_blueprint()
    model_storage.blueprint.put(blueprint)
    deployment = models.get_deployment(blueprint)
    model_storage.deployment.put(deployment)

    #################################################################################
    # Creating a simple deployment with node -> node as a graph

    dependency_node = models.get_dependency_node(deployment)
    model_storage.node.put(dependency_node)
    storage_dependency_node = model_storage.node.get(dependency_node.id)

    dependency_node_instance = models.get_dependency_node_instance(storage_dependency_node)
    model_storage.node_instance.put(dependency_node_instance)
    storage_dependency_node_instance = model_storage.node_instance.get(dependency_node_instance.id)

    dependent_node = models.get_dependent_node(deployment)
    model_storage.node.put(dependent_node)
    storage_dependent_node = model_storage.node.get(dependent_node.id)

    dependent_node_instance = models.get_dependent_node_instance(storage_dependent_node)
    model_storage.node_instance.put(dependent_node_instance)
    storage_dependent_node_instance = model_storage.node_instance.get(dependent_node_instance.id)

    relationship = models.get_relationship(storage_dependent_node, storage_dependency_node)
    model_storage.relationship.put(relationship)
    storage_relationship = model_storage.relationship.get(relationship.id)
    relationship_instance = models.get_relationship_instance(
        relationship=storage_relationship,
        target_instance=storage_dependency_node_instance,
        source_instance=storage_dependent_node_instance
    )
    model_storage.relationship_instance.put(relationship_instance)

    return deployment.id
