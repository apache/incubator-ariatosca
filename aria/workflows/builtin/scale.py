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

from aria import workflow
from aria.workflows.core.engine import Engine
from .install import install
from .uninstall import uninstall

from .deployment_modification import modify_deployment, finish_deployment_modification, \
    rollback_deployment_modification


def scale(context, node_id, delta, scale_compute):
    return scale_entity(
        context=context,
        scalable_entity_name=node_id,
        delta=delta,
        scale_compute=scale_compute)


# TODO: 1. the screening of which nodes were added doesn't work

@workflow(simple_workflow=False)
def scale_entity(context, graph, scalable_entity_name, delta, scale_compute):
    engine = Engine(context.concurrency_count)
    if isinstance(delta, basestring):
        try:
            delta = int(delta)
        except ValueError:
            raise ValueError('The delta parameter must be a number. Got: {0}'.format(delta))

    if delta == 0:
        context.logger.info('delta parameter is 0, so no scaling will take place.')
        return

    scaling_group = context.deployment.scaling_groups.get(scalable_entity_name)
    if scaling_group:
        curr_num_instances = scaling_group['properties']['current_instances']
        planned_num_instances = curr_num_instances + delta
        scale_id = scalable_entity_name
    else:
        node = context.storage.node.get(scalable_entity_name)
        if not node:
            raise ValueError("No scalable entity named {0} was found".format(
                scalable_entity_name))
        host_node = context.storage.node.get(node.host_id)
        scaled_node = host_node if (scale_compute and host_node) else node
        curr_num_instances = scaled_node.number_of_instances
        planned_num_instances = curr_num_instances + delta
        scale_id = scaled_node.id

    if planned_num_instances < 0:
        raise ValueError('Provided delta: {0} is illegal. current number of '
                         'instances of entity {1} is {2}'
                         .format(delta,
                                 scalable_entity_name,
                                 curr_num_instances))

    modification = modify_deployment(
        context,
        {
            scale_id: {
                'instances': planned_num_instances

                # These following parameters are not exposed at the moment,
                # but should be used to control which node instances get scaled in
                # (when scaling in).
                # They are mentioned here, because currently, the modification API
                # is not very documented.
                # Special care should be taken because if `scale_compute == True`
                # (which is the default), then these ids should be the compute node
                # instance ids which are not necessarily instances of the node
                # specified by `scalable_entity_name`.

                # Node instances denoted by these instance ids should be *kept* if
                # possible.
                # 'removed_ids_exclude_hint': [],

                # Node instances denoted by these instance ids should be *removed*
                # if possible.
                # 'removed_ids_include_hint': []
            }
        }
    )
    try:
        context.logger.info('Deployment modification started. '
                            '[modification_id={0}]'.format(modification.id))
        if delta > 0:
            added, related = [], []
            for node_instance in modification.added_and_related:
                if hasattr(node_instance, 'modification') and node_instance.modification == 'added':
                    added.append(node_instance)
                else:
                    related.append(node_instance)
            try:
                graph.add_task(_scale_install(
                    graph=graph,
                    context=context,
                    scaling_up_node_instances=added,
                    unaffected_node_instances=related))
            except:
                context.logger.error('Scale out failed, scaling back in.')
                for task in graph.tasks:
                    graph.remove_task(task)
                graph.add_task(_scale_uninstall(
                    graph=graph,
                    context=context,
                    scaling_down_node_instances=added,
                    unaffected_node_instances=related))
                raise
        else:
            removed, related = [], []
            for node_instance in modification.removed_and_related:
                if hasattr(node_instance, 'modifictation') and node_instance.pop('modification') == 'removed':
                    removed.append(node_instance)
                else:
                    related.append(node_instance)
            graph.add_task(_scale_uninstall(
                context=context,
                scaling_down_node_instances=removed,
                related_nodes=related))
    except:
        context.logger.warn('Rolling back deployment modification. '
                        '[modification_id={0}]'.format(modification.id))
        try:
            rollback_deployment_modification(context, modification.id)
        except:
            context.logger.warn('Deployment modification rollback failed. The '
                            'deployment model is most likely in some corrupted'
                            ' state.'
                            '[modification_id={0}]'.format(modification.id))
            raise
        raise
    else:
        engine.create_workflow(context, graph)
        engine.execute()
        try:
            finish_deployment_modification(context, modification.id)
        except:
            context.logger.warn('Deployment modification finish failed. The '
                            'deployment model is most likely in some corrupted'
                            ' state.'
                            '[modification_id={0}]'.format(modification.id))
            raise


@workflow(simple_workflow=False)
def _scale_uninstall(context, graph, scaling_down_node_instances, unaffected_node_instances):
    node_instance_sub_workflows = {}

    # Create install sub workflow for each unaffected
    for node_instance in unaffected_node_instances:
        node_instance_sub_workflow = uninstall_stub_subworkflow(
            sub_workflow_name='uninstall_stub_{0}'.format(node_instance.id),
            graph=graph,
            context=context)
        node_instance_sub_workflows[node_instance.id] = node_instance_sub_workflow
        graph.add_task(node_instance_sub_workflow)

    # Create install sub workflow for each failing node
    uninstall(
        context=context,
        graph=graph,
        node_instances=scaling_down_node_instances,
        node_instance_sub_workflows=node_instance_sub_workflows)

    # Add operations for intact nodes depending on a node instance
    # belonging to node_instances
    intact_node_relationship_operation = 'aria.interfaces.relationship_lifecycle.unlink'
    for node_instance in unaffected_node_instances:
        node_instance_sub_workflow = node_instance_sub_workflows[node_instance.id]

        for relationship_instance in reversed(node_instance.relationship_instances):
            target_node_instance = context.storage.node_instance.get(
                relationship_instance.target_id)
            after_tasks = []
            if target_node_instance in scaling_down_node_instances:
                after_tasks.extend(
                    [node_instance_sub_workflows[relationship.target_id]
                     for relationship in node_instance.relationship_instances])

            elif target_node_instance in unaffected_node_instances:
                intact_tasks = relationship_tasks_subworkflow(
                    graph=graph,
                    context=context,
                    sub_workflow_name='{0}.{1}'.format(
                        intact_node_relationship_operation,
                        node_instance.id),
                    operation_name=intact_node_relationship_operation,
                    node_instance=node_instance,
                    relationship_instance=relationship_instance)
                after_tasks.extend(intact_tasks)

            graph.dependency(source_task=node_instance_sub_workflow, after=after_tasks)


@workflow(simple_workflow=False)
def _scale_install(context, graph, scaling_up_node_instances, unaffected_node_instances):
    node_instance_sub_workflows = {}

    # Create install sub workflow for each unaffected
    for node_instance in unaffected_node_instances:
        node_instance_sub_workflow = install_stub_subworkflow(
            sub_workflow_name='install_stub_{0}'.format(node_instance.id),
            context=context,
            graph=graph)
        node_instance_sub_workflows[node_instance.id] = node_instance_sub_workflow
        graph.add_task(node_instance_sub_workflow)

    # create install sub workflow for every node instance
    install(
        context=context,
        graph=graph,
        node_instances=scaling_up_node_instances,
        node_instance_sub_workflows=node_instance_sub_workflows)

    # Add operations for intact nodes depending on a node instance
    # belonging to node_instances
    intact_node_relationship_operation = 'aria.interfaces.relationship_lifecycle.establish'
    for node_instance in unaffected_node_instances:
        node_instance_sub_workflow = node_instance_sub_workflows[node_instance.id]

        for relationship_instance in node_instance.relationship_instances:
            after_tasks = [
                node_instance_sub_workflows[relationship_instance.target_id]
                for relationship_instance in node_instance.relationship_instances]

            if context.storage.node_instance.get(relationship_instance.target_id) in unaffected_node_instances:
                intact_tasks = relationship_tasks_subworkflow(
                    graph=graph,
                    context=context,
                    sub_workflow_name='{0}.{1}'.format(
                        intact_node_relationship_operation,
                        node_instance.id),
                    operation_name=intact_node_relationship_operation,
                    node_instance=node_instance,
                    relationship_instance=relationship_instance)
                after_tasks.extend(intact_tasks)

            graph.dependency(source_task=node_instance_sub_workflow, after=after_tasks)


@workflow(simple_workflow=False)
def install_stub_subworkflow(**kwargs):
    pass


@workflow(simple_workflow=False)
def uninstall_stub_subworkflow(**kwargs):
    pass


@workflow(simple_workflow=False)
def install_node_instance_sub_workflow(graph, context, node_instance):
    graph.chain(tasks=[
        context.operation(
            name='aria.interfaces.lifecycle.create.{0}'.format(node_instance.id),
            operation_details=node_instance.node.operations[
                'aria.interfaces.lifecycle.create'],
            node_instance=node_instance),
        preconfigure_relationship_sub_workflow(
            sub_workflow_name='preconfigure_{0}'.format(node_instance.id),
            context=context,
            graph=graph,
            node_instance=node_instance),
        context.operation(
            name='aria.interfaces.lifecycle.configure.{0}'.format(node_instance.id),
            operation_details=node_instance.node.operations[
                'aria.interfaces.lifecycle.configure'],
            node_instance=node_instance),
        postconfigure_relationship_sub_workflow(
            sub_workflow_name='postconfigure_{0}'.format(node_instance.id),
            context=context,
            graph=graph,
            node_instance=node_instance),
        context.operation(
            name='aria.interfaces.lifecycle.start.{0}'.format(node_instance.id),
            operation_details=node_instance.node.operations[
                'aria.interfaces.lifecycle.start'],
            node_instance=node_instance),
        establish_relationship_sub_workflow(
            sub_workflow_name='establish_{0}'.format(node_instance.id),
            context=context,
            graph=graph,
            node_instance=node_instance),
    ])


@workflow(simple_workflow=False)
def uninstall_node_instance_sub_workflow(graph, context, node_instance):
    graph.chain(tasks=[
        # instance.set_state('stopping'),
        # instance.send_event('Stopping node'),
        context.operation(
            name='aria.interfaces.monitoring.stop.{0}'.format(node_instance.id),
            operation_details=node_instance.node.operations['aria.interfaces.monitoring.stop'],
            node_instance=node_instance
        ),
        context.operation(
            name='aria.interfaces.lifecycle.stop.{0}'.format(node_instance.id),
            operation_details=node_instance.node.operations['aria.interfaces.lifecycle.stop'],
            node_instance=node_instance
        ),
        # instance.set_state('stopped'),
        unlink_relationship_sub_workflow(
            sub_workflow_name='unlink{0}'.format(node_instance.id),
            context=context,
            graph=graph,
            node_instance=node_instance),
        # instance.set_state('deleting'),
        # instance.send_event('Deleting node'),
        context.operation(
            name='aria.interfaces.lifecycle.delete.{0}'.format(node_instance.id),
            operation_details=node_instance.node.operations['aria.interfaces.lifecycle.delete'],
            node_instance=node_instance
        )
        # instance.set_state('deleted')

    ])


@workflow(simple_workflow=False)
def preconfigure_relationship_sub_workflow(context, graph, node_instance):
    operation_name = 'aria.interfaces.relationship_lifecycle.preconfigure'
    relationship_tasks = []
    for relationship_instance in node_instance.relationship_instances:
        relationship_tasks.append(
            relationship_tasks_subworkflow(
                graph=graph,
                context=context,
                sub_workflow_name='{0}.{1}'.format(operation_name, node_instance.id),
                operation_name=operation_name,
                node_instance=node_instance,
                relationship_instance=relationship_instance)
        )
    graph.chain(tasks=relationship_tasks)


@workflow(simple_workflow=False)
def postconfigure_relationship_sub_workflow(context, graph, node_instance):
    operation_name = 'aria.interfaces.relationship_lifecycle.postconfigure'
    relationship_tasks = []
    for relationship_instance in node_instance.relationship_instances:
        relationship_tasks.append(
            relationship_tasks_subworkflow(
                graph=graph,
                context=context,
                sub_workflow_name='{0}.{1}'.format(operation_name, node_instance.id),
                operation_name=operation_name,
                node_instance=node_instance,
                relationship_instance=relationship_instance)
        )
    graph.chain(tasks=relationship_tasks)


@workflow(simple_workflow=False)
def establish_relationship_sub_workflow(context, graph, node_instance):
    operation_name = 'aria.interfaces.relationship_lifecycle.establish'
    relationship_tasks = []
    for relationship_instance in node_instance.relationship_instances:
        relationship_tasks.append(
            relationship_tasks_subworkflow(
                graph=graph,
                context=context,
                sub_workflow_name='{0}.{1}'.format(operation_name, node_instance.id),
                operation_name=operation_name,
                node_instance=node_instance,
                relationship_instance=relationship_instance)
        )
    graph.chain(tasks=relationship_tasks)


@workflow(simple_workflow=False)
def unlink_relationship_sub_workflow(context, graph, node_instance):
    operation_name = 'aria.interfaces.relationship_lifecycle.unlink'
    relationship_tasks = []
    for relationship_instance in node_instance.relationship_instances:
        relationship_tasks.append(
            relationship_tasks_subworkflow(
                graph=graph,
                context=context,
                sub_workflow_name='{0}.{1}'.format(operation_name, node_instance.id),
                operation_name=operation_name,
                node_instance=node_instance,
                relationship_instance=relationship_instance)
        )
    graph.chain(tasks=relationship_tasks)


@workflow(simple_workflow=False)
def relationship_tasks_subworkflow(graph, context, operation_name, node_instance, relationship_instance):
    source_operation = relationship_instance.relationship.source_operations[operation_name]
    target_instance = context.storage.node_instance.get(relationship_instance.target_id)
    target_operation = relationship_instance.relationship.target_operations[operation_name]
    graph.fan_out([
        context.operation(
            name='source_{0}'.format(operation_name),
            node_instance=node_instance,
            operation_details=source_operation),
        context.operation(
            name='target_{0}'.format(operation_name),
            node_instance=target_instance,
            operation_details=target_operation),
    ])
