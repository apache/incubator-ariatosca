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

from ...storage import model
from ...orchestrator import operation
from ...utils.console import puts, Colored
from ...utils.formatting import safe_repr


def initialize_storage(context, model_storage, deployment_id):
    blueprint = create_blueprint(context)
    model_storage.blueprint.put(blueprint)

    deployment = create_deployment(context, blueprint, deployment_id)
    model_storage.deployment.put(deployment)

    # Create nodes and node instances
    for node_template in context.modeling.model.node_templates.itervalues():
        node = create_node(context, deployment, node_template)
        model_storage.node.put(node)

        for a_node in context.modeling.instance.find_nodes(node_template.name):
            node_instance = create_node_instance(node, a_node)
            model_storage.node_instance.put(node_instance)

    # Create relationships
    for node_template in context.modeling.model.node_templates.itervalues():
        for index, requirement_template in enumerate(node_template.requirement_templates):
            # We are currently limited only to requirements for specific node templates!
            if requirement_template.target_node_template_name:
                source = model_storage.node.get_by_name(node_template.name)
                target = model_storage.node.get_by_name(
                    requirement_template.target_node_template_name)
                relationship = create_relationship(context, source, target,
                                                   requirement_template.relationship_template)
                model_storage.relationship.put(relationship)

                for node in context.modeling.instance.find_nodes(node_template.name):
                    for relationship_model in node.relationships:
                        if relationship_model.source_requirement_index == index:
                            source_instance = \
                                model_storage.node_instance.get_by_name(node.id)
                            target_instance = \
                                model_storage.node_instance.get_by_name(
                                    relationship_model.target_node_id)
                            relationship_instance = \
                                create_relationship_instance(relationship, source_instance,
                                                             target_instance)
                            model_storage.relationship_instance.put(relationship_instance)


def create_blueprint(context):
    now = datetime.utcnow()
    main_file_name = unicode(context.presentation.location)
    try:
        name = context.modeling.model.metadata.values.get('template_name')
    except AttributeError:
        name = None
    return model.Blueprint(
        plan={},
        name=name or main_file_name,
        description=context.modeling.model.description or '',
        created_at=now,
        updated_at=now,
        main_file_name=main_file_name)


def create_deployment(context, blueprint, deployment_id):
    now = datetime.utcnow()
    return model.Deployment(
        name='%s_%s' % (blueprint.name, deployment_id),
        blueprint_fk=blueprint.id,
        description=context.modeling.instance.description or '',
        created_at=now,
        updated_at=now,
        workflows={},
        inputs={},
        groups={},
        permalink='',
        policy_triggers={},
        policy_types={},
        outputs={},
        scaling_groups={})


def create_node(context, deployment, node_template):
    operations = create_operations(context, node_template.interface_templates, '_dry_node')
    return model.Node(
        name=node_template.name,
        type=node_template.type_name,
        type_hierarchy=[],
        number_of_instances=node_template.default_instances,
        planned_number_of_instances=node_template.default_instances,
        deploy_number_of_instances=node_template.default_instances,
        properties={},
        operations=operations,
        min_number_of_instances=node_template.min_instances,
        max_number_of_instances=node_template.max_instances or 100,
        deployment_fk=deployment.id)


def create_relationship(context, source, target, relationship_template):
    if relationship_template:
        source_operations = create_operations(context,
                                              relationship_template.source_interface_templates,
                                              '_dry_relationship')
        target_operations = create_operations(context,
                                              relationship_template.target_interface_templates,
                                              '_dry_relationship')
    else:
        source_operations = {}
        target_operations = {}
    return model.Relationship(
        source_node_fk=source.id,
        target_node_fk=target.id,
        source_interfaces={},
        source_operations=source_operations,
        target_interfaces={},
        target_operations=target_operations,
        type='rel_type',
        type_hierarchy=[],
        properties={})


def create_node_instance(node, node_model):
    return model.NodeInstance(
        name=node_model.id,
        runtime_properties={},
        version=None,
        node_fk=node.id,
        state='',
        scaling_groups=[])


def create_relationship_instance(relationship, source_instance, target_instance):
    return model.RelationshipInstance(
        relationship_fk=relationship.id,
        source_node_instance_fk=source_instance.id,
        target_node_instance_fk=target_instance.id)


def create_operations(context, interfaces, fn_name):
    operations = {}
    for interface in interfaces.itervalues():
        operations[interface.type_name] = {}
        for oper in interface.operation_templates.itervalues():
            name = '%s.%s' % (interface.type_name, oper.name)
            operations[name] = {
                'operation': '%s.%s' % (__name__, fn_name),
                'inputs': {
                    '_plugin': None,
                    '_implementation': None}}
            if oper.implementation:
                plugin, implementation = _parse_implementation(context, oper.implementation)
                operations[name]['inputs']['_plugin'] = plugin
                operations[name]['inputs']['_implementation'] = implementation

    return operations


def _parse_implementation(context, implementation):
    index = implementation.find('>')
    if index == -1:
        return 'execution', implementation
    plugin = implementation[:index].strip()

    # TODO: validation should happen in parser
    if (plugin != 'execution') and (_get_plugin(context, plugin) is None):
        raise ValueError('unknown plugin: "%s"' % plugin)

    implementation = implementation[index+1:].strip()
    return plugin, implementation


def _get_plugin(context, plugin_name):
    def is_plugin(type_name):
        return context.modeling.policy_types.get_role(type_name) == 'plugin'

    for policy in context.modeling.instance.policies.itervalues():
        if (policy.name == plugin_name) and is_plugin(policy.type_name):
            return policy

    return None


_TERMINAL_LOCK = RLock()


@operation
def _dry_node(ctx, _plugin, _implementation, **kwargs):
    with _TERMINAL_LOCK:
        print '> node instance: %s' % Colored.red(ctx.node_instance.name)
        _dump_implementation(_plugin, _implementation)


@operation
def _dry_relationship(ctx, _plugin, _implementation, **kwargs):
    with _TERMINAL_LOCK:
        puts('> relationship instance: %s -> %s' % (
            Colored.red(ctx.relationship_instance.source_node_instance.name),
            Colored.red(ctx.relationship_instance.target_node_instance.name)))
        _dump_implementation(_plugin, _implementation)


def _dump_implementation(plugin, implementation):
    if plugin:
        print '  plugin: %s' % Colored.magenta(plugin)
    if implementation:
        print '  implementation: %s' % Colored.yellow(safe_repr(implementation))
