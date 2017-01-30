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
from threading import RLock

from .storage import model
from .orchestrator import operation
from .utils.formatting import safe_repr
from .utils.console import puts, Colored


def initialize_storage(context, model_storage, deployment_id):
    blueprint = _create_blueprint(context)
    model_storage.blueprint.put(blueprint)

    deployment = _create_deployment(context, blueprint, deployment_id)
    model_storage.deployment.put(deployment)

    # Create nodes and node instances
    for node_template in context.modeling.model.node_templates.values():
        model_storage.node_template.put(node_template)

        for a_node in context.modeling.instance.find_nodes(node_template.name):
            node = _create_node_instance(deployment, node_template, a_node)
            model_storage.node.put(node)

    # Create relationships
    for node_template in context.modeling.model.node_templates.values():
        for index, requirement_template in enumerate(node_template.requirement_templates):
            # We are currently limited only to requirements for specific node templates!
            if requirement_template.target_node_template_name:
                model_storage.requirement_template.put(requirement_template)

                for node in context.modeling.instance.find_nodes(node_template.name):
                    for relationship_model in node.relationships:
                        if relationship_model.source_requirement_index == index:
                            source_instance = \
                                model_storage.node.get_by_name(node.id)
                            target_instance = \
                                model_storage.node.get_by_name(
                                    relationship_model.target_node_id)
                            relationship = \
                                _create_relationship_instance(source_instance, target_instance)
                            model_storage.relationship.put(relationship)


def _create_blueprint(context):
    now = datetime.utcnow()
    main_file_name = unicode(context.presentation.location)
    try:
        name = context.modeling.model.metadata.values.get('template_name')
    except AttributeError:
        name = None

    return model.ServiceTemplate(
        plan={},
        name=name or main_file_name,
        description=context.modeling.model.description or '',
        created_at=now,
        updated_at=now,
        main_file_name=main_file_name
    )


def _create_deployment(context, service_template, service_instance_id):
    now = datetime.utcnow()
    return model.ServiceInstance(
        name='{0}_{1}'.format(service_template.name, service_instance_id),
        service_template=service_template,
        description=context.modeling.instance.description or '',
        created_at=now,
        updated_at=now,
        workflows={},
        permalink='',
        policy_triggers={},
        scaling_groups={}
    )


def _create_node_instance(service_instance, node, node_model):
    return model.Node(
        service_instance=service_instance,
        name=node_model.id,
        runtime_properties={},
        node_template=node,
        state='',
        scaling_groups=[]
    )


def _create_relationship_instance(source_instance, target_instance):
    return model.Relationship(
        source_node=source_instance,
        target_node=target_instance
    )


_TERMINAL_LOCK = RLock()


@operation
def _dry_node(ctx, _plugin, _implementation, **kwargs):
    with _TERMINAL_LOCK:
        print '> node instance: %s' % Colored.red(ctx.node.name)
        _dump_implementation(_plugin, _implementation)


@operation
def _dry_relationship(ctx, _plugin, _implementation, **kwargs):
    with _TERMINAL_LOCK:
        puts('> relationship instance: %s -> %s' % (
            Colored.red(ctx.relationship.source_node_instance.name),
            Colored.red(ctx.relationship.target_node_instance.name)))
        _dump_implementation(_plugin, _implementation)


def _dump_implementation(plugin, implementation):
    if plugin:
        print '  plugin: %s' % Colored.magenta(plugin)
    if implementation:
        print '  implementation: %s' % Colored.yellow(safe_repr(implementation))
