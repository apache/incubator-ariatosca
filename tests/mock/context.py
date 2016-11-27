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

from aria import application_model_storage
from aria.orchestrator import context
from aria.storage.sql_mapi import SQLAlchemyModelAPI

from . import models


def simple(api_kwargs, **kwargs):
    model_storage = application_model_storage(SQLAlchemyModelAPI, api_kwargs=api_kwargs)
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

    final_kwargs = dict(
        name='simple_context',
        model_storage=model_storage,
        resource_storage=None,
        deployment_id=deployment.id,
        workflow_name=models.WORKFLOW_NAME,
        task_max_attempts=models.TASK_MAX_ATTEMPTS,
        task_retry_interval=models.TASK_RETRY_INTERVAL
    )
    final_kwargs.update(kwargs)
    return context.workflow.WorkflowContext(**final_kwargs)
