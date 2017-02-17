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

"""
This solution is temporary, as we plan to combine aria.parser.modeling and aria.storage.modeling
into one package (aria.modeling?).
"""

from datetime import datetime
from threading import RLock

from ...modeling import model
from ...orchestrator.decorators import operation
from ...utils.console import puts, Colored
from ...utils.formatting import safe_repr


def initialize_storage(context, model_storage, service_instance_id):
    s_service_template = create_service_template(context)
    model_storage.service_template.put(s_service_template)

    s_service_instance = create_service_instance(context, s_service_template, service_instance_id)
    model_storage.service_instance.put(s_service_instance)

    # Create node templates and nodes
    for node_template in context.modeling.model.node_templates.itervalues():
        s_node_template = create_node_template(s_service_template, node_template)
        model_storage.node_template.put(s_node_template)

        for node in context.modeling.instance.find_nodes(node_template.name):
            s_node = create_node(s_service_instance, s_node_template, node)
            model_storage.node.put(s_node)
            create_interfaces(context, model_storage, node.interfaces,
                              s_node, 'node', None, '_dry_node')

    # Create relationships between nodes
    for source_node in context.modeling.instance.nodes.itervalues():
        for relationship in source_node.relationships:
            s_source_node = model_storage.node.get_by_name(source_node.id)
            s_target_node = model_storage.node.get_by_name(relationship.target_node_id)
            s_relationship = create_relationship(s_source_node, s_target_node)
            model_storage.relationship.put(s_relationship)
            # TOSCA always uses the "source" edge
            create_interfaces(context, model_storage, relationship.source_interfaces,
                              s_relationship, 'relationship', 'source', '_dry_relationship')


def create_service_template(context):
    now = datetime.utcnow()
    main_file_name = unicode(context.presentation.location)
    try:
        name = context.modeling.model.metadata.values.get('template_name')
    except AttributeError:
        name = None
    return model.ServiceTemplate(
        name=name or main_file_name,
        description=context.modeling.model.description or '',
        created_at=now,
        updated_at=now,
        main_file_name=main_file_name,
        plan={}
    )


def create_service_instance(context, service_template, service_instance_id):
    now = datetime.utcnow()
    return model.ServiceInstance(
        name='{0}_{1}'.format(service_template.name, service_instance_id),
        service_template=service_template,
        description=context.modeling.instance.description or '',
        created_at=now,
        updated_at=now)


def create_node_template(service_template, node_template):
    return model.NodeTemplate(
        name=node_template.name,
        type_name=node_template.type_name,
        default_instances=node_template.default_instances,
        min_instances=node_template.min_instances,
        max_instances=node_template.max_instances or 100,
        service_template=service_template)


def create_node(service_instance, node_template, node):
    return model.Node(
        name=node.id,
        state='',
        node_template=node_template,
        service_instance=service_instance)


def create_relationship(source_node, target_node):
    return model.Relationship(
        source_node=source_node,
        target_node=target_node)


def create_interfaces(context, model_storage, interfaces, node_or_relationship, type_name, edge,
                      fn_name):
    for interface_name, interface in interfaces.iteritems():
        s_interface = model.Interface(name=interface_name,
                                      type_name=interface.type_name,
                                      edge=edge)
        setattr(s_interface, type_name, node_or_relationship)
        model_storage.interface.put(s_interface)
        for operation_name, oper in interface.operations.iteritems():
            operation_name = '{0}.{1}'.format(interface_name, operation_name)
            s_operation = model.Operation(name=operation_name,
                                          implementation='{0}.{1}'.format(__name__, fn_name),
                                          interface=s_interface)
            plugin, implementation = _parse_implementation(context, oper.implementation)
            # TODO: operation's user inputs
            s_operation.inputs.append(model.Parameter(name='_plugin', # pylint: disable=no-member
                                                      str_value=str(plugin),
                                                      type='str'))
            s_operation.inputs.append(model.Parameter(name='_implementation', # pylint: disable=no-member
                                                      str_value=str(implementation),
                                                      type='str'))
            model_storage.operation.put(s_operation)


def _parse_implementation(context, implementation):
    if not implementation:
        return '', ''

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
        print '> node instance: %s' % Colored.red(ctx.node.name)
        _dump_implementation(_plugin, _implementation)


@operation
def _dry_relationship(ctx, _plugin, _implementation, **kwargs):
    with _TERMINAL_LOCK:
        puts('> relationship instance: %s -> %s' % (
            Colored.red(ctx.relationship.source_node.name),
            Colored.red(ctx.relationship.target_node.name)))
        _dump_implementation(_plugin, _implementation)


def _dump_implementation(plugin, implementation):
    if plugin:
        print '  plugin: %s' % Colored.magenta(plugin)
    if implementation:
        print '  implementation: %s' % Colored.yellow(safe_repr(implementation))
