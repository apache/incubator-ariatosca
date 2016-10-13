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

import itertools
from datetime import datetime

from aria.storage import models
from aria.deployment import modify_deployment as extract_deployment_modification


def modify_deployment(context, modified_nodes, modification_context=None):
    deployment = context.deployment
    active_modifications = filter(
        lambda dm: dm == models.DeploymentModification.STARTED,
        context.storage.deployment_modification)
    if active_modifications:
        # TODO: raise proper exception
        raise Exception(
            'Cannot start deployment modification while there are '
            'existing started deployment modifications. Currently '
            'started deployment modifications: {0}'
            .format(active_modifications))

    nodes = set(context.nodes)
    node_instances = set(context.node_instances)
    node_instances_modification = extract_deployment_modification(
        nodes=nodes,
        previous_nodes=nodes,
        previous_node_instances=node_instances,
        scaling_groups=deployment.scaling_groups,
        modified_nodes=modified_nodes)

    modification = models.DeploymentModification(
        created_at=datetime.now(),
        ended_at=None,
        status=models.DeploymentModification.STARTED,
        deployment_id=context.deployment_id,
        modified_nodes=modified_nodes,
        added_and_related=node_instances_modification['added_and_related'],
        removed_and_related=node_instances_modification['removed_and_related'],
        extended_and_related=node_instances_modification['extended_and_related'],
        reduced_and_related=node_instances_modification['reduced_and_related'],
        # before_modification=node_instances,
        # node_instances=node_instances_modification,
        context=modification_context)

    context.storage.deployment_modification.store(modification)

    for node_id, modified_node in modified_nodes.items():
        if node_id in deployment.scaling_groups:
            deployment.scaling_groups[node_id]['properties'].update({
                'planned_instances': modified_node['instances']
            })
        else:
            node = context.storage.node.get(node_id)
            node.planned_number_of_instances = modified_node['instances']
            context.storage.node.store(node)
    context.storage.deployment.store(deployment)

    added_and_related = node_instances_modification['added_and_related']
    added_node_instances = []
    for node_instance in added_and_related:
        if hasattr(node_instance, 'modification') and node_instance.modification == 'added':
            added_node_instances.append(node_instance)
        else:
            current_instance = context.storage.node_instance.get(node_instance.id)
            target_names = [r.target_id for r in current_instance.node.relationships]
            current_relationship_groups = {
                target_name: list(group)
                for target_name, group in itertools.groupby(
                    current_instance.relationship_instances,
                    key=lambda r: r.target_name)
                }
            new_relationship_groups = {
                target_name: list(group)
                for target_name, group in itertools.groupby(
                node_instance.relationship_instances,
                key=lambda r: r.target_name)
                }
            new_relationships = []
            for target_name in target_names:
                new_relationships += current_relationship_groups.get(
                    target_name, [])
                new_relationships += new_relationship_groups.get(
                    target_name, [])

            updated_node_instance = models.NodeInstance(
                id=node_instance.id,
                deployment_id=context.deployment_id,
                relationship_instances=new_relationships,
                version=current_instance.version,
                node=context.storage.node.get(node_instance.node.id),
                host_id=None,
                runtime_properties={})

            context.storage.node_instance.store(updated_node_instance)

    _create_deployment_node_instances(context, added_node_instances)
    return modification


def _create_deployment_node_instances(context,
                                      dsl_node_instances):
    node_instances = []
    for node_instance in dsl_node_instances:
        instance = models.NodeInstance(
            id=node_instance.id,
            node=node_instance.node,
            host_id=node_instance.host_id,
            relationship_instances=node_instance.relationship_instances,
            deployment_id=context.deployment_id,
            runtime_properties={},
            version=None,
            scaling_groups=node_instance.scaling_groups)
        node_instances.append(instance)

    for node_instance in node_instances:
        context.storage.node_instance.store(node_instance)


def finish_deployment_modification(context, modification_id):
    modification = context.storage.deployment_modification.get(modification_id)

    if modification.status in models.DeploymentModification.END_STATES:
        raise Exception(
            'Cannot finish deployment modification: {0}. It is already in'
            ' {1} status.'.format(modification_id,
                                  modification.status))

    for node_id, modified_node in modification.modified_nodes.items():
        if node_id in context.deployment.scaling_groups:
            context.deployment.scaling_groups[node_id]['properties'].update({
                'current_instances': modified_node['instances']
            })
        else:
            node_dict = context.storage.node.get(node_id).fields_dict
            node_dict['number_of_instances'] = modified_node['instances']
            context.storage.node.store(models.Node(**node_dict))

    context.storage.deployment.store(context.deployment)

    for node_instance in modification.removed_and_related:
        if node_instance.get('modification') == 'removed':
            context.storage.node_instance.delete(node_instance.id)
            pass
        else:
            removed_relationship_target_ids = set(
                [rel.target_id for rel in node_instance.relationships])
            current = context.storage.node_instance.get(node_instance.id)
            new_relationships = [rel for rel in current.relationships
                                 if rel.target_id not in removed_relationship_target_ids]
            context.storage.node_instance.store(models.NodeInstance(
                id=node_instance.id,
                relationships=new_relationships,
                version=current.version,
                node_id=None,
                host_id=None,
                deployment_id=None,
                state=None,
                runtime_properties=None))

    now = datetime.now()

    context.storage.deployment_modification.store(
        models.DeploymentModification(
            id=modification_id,
            status=models.DeploymentModification.FINISHED,
            ended_at=now,
            created_at=modification.created_at,
            deployment_id=modification.deployment_id,
            modified_nodes=modification.modified_nodes,
            added_and_related=modification.added_and_related,
            removed_and_related=modification.removed_and_related,
            extended_and_related=modification.extended_and_related,
            reduced_and_related=modification.reduced_and_related,
            context=None))


def rollback_deployment_modification(context, modification_id):
    pass
    # modification = context.storage.deployment_modification.get(modification_id)
    #
    # if modification.status in models.DeploymentModification.END_STATES:
    #     raise Exception(
    #         'Cannot rollback deployment modification: {0}. It is already '
    #         'in {1} status.'.format(modification_id,
    #                                 modification.status))
    #
    # # before_rollback_node_instnaces = [instance.fields_dict for instance in context.node_instances]
    # for instance in context.node_instances:
    #     context.storage.node_instance.delete(instance.id)
    #
    # for instance in modification.before_modification:
    #     context.storage.node_instance.store(models.NodeInstance(**instance))
    # nodes_num_instances = dict((node.id, node) for node in context.nodes)
    #
    # modified_nodes = modification.modified_nodes
    # for node_id, modified_node in modified_nodes.items():
    #     if node_id in context.deployment.scaling_groups:
    #         props = context.deployment.scaling_groups[node_id]['properties']
    #         props['planned_instances'] = props['current_instances']
    #     else:
    #         rolled_back_node_dict = context.storage.node.get(node_id).fields_dict
    #         rolled_back_node_dict['planned_number_of_instances'] = nodes_num_instances[node_id].number_of_instances
    #         context.storage.node.store(models.Node(**rolled_back_node_dict))
    #
    # context.storage.deployment.store(context.deployment)
    #
    # return context.storage.deployment_modification.get(modification_id)
