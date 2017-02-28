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

import re
from types import FunctionType
from datetime import datetime

from aria.parser.modeling import Type, RelationshipType, PolicyType
from aria.modeling.models import (ServiceTemplate, NodeTemplate,
                                  RequirementTemplate, RelationshipTemplate, CapabilityTemplate,
                                  GroupTemplate, PolicyTemplate, SubstitutionTemplate,
                                  SubstitutionTemplateMapping, InterfaceTemplate, OperationTemplate,
                                  ArtifactTemplate, Metadata, Parameter, Plugin)
from aria.utils.console import puts, Colored
from aria.utils.formatting import safe_repr

#from aria.modeling.model import (Type, RelationshipType, PolicyType, ServiceTemplate, NodeTemplate,
#                                 RequirementTemplate, RelationshipTemplate, CapabilityTemplate,
#                                 GroupTemplate, PolicyTemplate, SubstitutionTemplate,
#                                 MappingTemplate, InterfaceTemplate, OperationTemplate,
#                                 ArtifactTemplate, Metadata, Parameter)

from ..data_types import coerce_value

#from platform import node


def create_service_model(context): # pylint: disable=too-many-locals,too-many-branches
    now = datetime.now()
    model = ServiceTemplate(created_at=now,
                            updated_at=now)

    model.description = context.presentation.get('service_template', 'description', 'value')

    # Metadata
    metadata = context.presentation.get('service_template', 'metadata')
    if metadata is not None:
        model.meta_data['template_name'] = Metadata(value=metadata.template_name)
        model.meta_data['template_author'] = Metadata(value=metadata.template_author)
        model.meta_data['template_version'] = Metadata(value=metadata.template_version)
        custom = metadata.custom
        if custom:
            for name, v in custom.iteritems():
                model.meta_data[name] = Metadata(value=v)

    # Types
    create_types(context,
                 context.modeling.node_types,
                 context.presentation.get('service_template', 'node_types'))
    create_types(context,
                 context.modeling.group_types,
                 context.presentation.get('service_template', 'group_types'))
    create_types(context,
                 context.modeling.capability_types,
                 context.presentation.get('service_template', 'capability_types'))
    create_types(context,
                 context.modeling.relationship_types,
                 context.presentation.get('service_template', 'relationship_types'),
                 create_relationship_type)
    create_types(context,
                 context.modeling.policy_types,
                 context.presentation.get('service_template', 'policy_types'),
                 create_policy_type)
    create_types(context,
                 context.modeling.artifact_types,
                 context.presentation.get('service_template', 'artifact_types'))
    create_types(context,
                 context.modeling.interface_types,
                 context.presentation.get('service_template', 'interface_types'))

    # Topology template
    topology_template = context.presentation.get('service_template', 'topology_template')
    if topology_template is not None:
        create_properties_from_values(model.inputs, topology_template._get_input_values(context))
        create_properties_from_values(model.outputs, topology_template._get_output_values(context))

    # Policies
    # (We need to do this before node and group templates, because we need plugins populated)
    policies = context.presentation.get('service_template', 'topology_template', 'policies')
    if policies:
        for policy in policies.itervalues():
            model.policy_templates.append(create_policy_template(context, policy))
            
            if context.modeling.policy_types.get_role(policy.type) == 'plugin':
                model.plugins[policy._name] = create_plugin(context, policy)

    # Node templates
    node_templates = context.presentation.get('service_template', 'topology_template',
                                              'node_templates')
    if node_templates:
        for node_template in node_templates.itervalues():
            model.node_templates.append(create_node_template(context, model, node_template))

    # Groups
    groups = context.presentation.get('service_template', 'topology_template', 'groups')
    if groups:
        for group in groups.itervalues():
            model.group_templates.append(create_group_template(context, model, group))

    # Substitution
    substitution_mappings = context.presentation.get('service_template', 'topology_template',
                                                     'substitution_mappings')
    if substitution_mappings is not None:
        substitution_template = SubstitutionTemplate(node_type_name=substitution_mappings.node_type)
        capabilities = substitution_mappings.capabilities
        if capabilities:
            for mapped_capability_name, capability in capabilities.iteritems():
                substitution_template.mappings[mapped_capability_name] = \
                    SubstitutionTemplateMapping(mapped_name='capability.' + mapped_capability_name,
                                                node_template_name=capability.node_template,
                                                name='capability.' + capability.capability)
        requirements = substitution_mappings.requirements
        if requirements:
            for mapped_requirement_name, requirement in requirements.iteritems():
                substitution_template.mappings[mapped_requirement_name] = \
                    SubstitutionTemplateMapping(mapped_name='requirement.' + mapped_requirement_name,
                                                node_template_name=requirement.node_template,
                                                name='requirement.' + requirement.requirement)
        model.substitution_template = substitution_template

    return model


def create_plugin(context, policy):
    properties = policy.properties

    def get(name):
        prop = properties.get(name)
        return prop.value if prop is not None else None

    now = datetime.now()

    model = Plugin(name=policy._name,
                   archive_name=get('archive_name') or '',
                   distribution=get('distribution'),
                   distribution_release=get('distribution_release'),
                   distribution_version=get('distribution_version'),
                   package_name=get('package_name') or '',
                   package_source=get('package_source'),
                   package_version=get('package_version'),
                   supported_platform=get('supported_platform'),
                   supported_py_versions=get('supported_py_versions'),
                   uploaded_at=now,
                   wheels=get('wheels') or [])

    return model

def create_node_template(context, service_template, node_template):
    node_type = node_template._get_type(context)
    model = NodeTemplate(name=node_template._name, type_name=node_type._name)
    
    model.default_instances = 1
    model.min_instances = 0

    if node_template.description:
        model.description = node_template.description.value

    create_properties_from_values(model.properties, node_template._get_property_values(context))
    create_interface_templates(context, service_template, model.interface_templates,
                               node_template._get_interfaces(context))

    artifacts = node_template._get_artifacts(context)
    if artifacts:
        for artifact_name, artifact in artifacts.iteritems():
            model.artifact_templates[artifact_name] = create_artifact_template(context, artifact)

    requirements = node_template._get_requirements(context)
    if requirements:
        for _, requirement in requirements:
            model.requirement_templates.append(create_requirement_template(context,
                                                                           service_template,
                                                                           requirement))

    capabilities = node_template._get_capabilities(context)
    if capabilities:
        for capability_name, capability in capabilities.iteritems():
            model.capability_templates[capability_name] = create_capability_template(context,
                                                                                     capability)

    if model.target_node_template_constraints:
        model.target_node_template_constraints = []
        create_node_filter_constraint_lambdas(context, node_template.node_filter,
                                              model.target_node_template_constraints)

    return model


def create_interface_template(context, service_template, interface):
    interface_type = interface._get_type(context)
    model = InterfaceTemplate(name=interface._name, type_name=interface_type._name)

    if interface_type.description:
        model.description = interface_type.description.value

    inputs = interface.inputs
    if inputs:
        for input_name, the_input in inputs.iteritems():
            model.inputs[input_name] = Parameter(name=input_name,
                                                 type_name=the_input.value.type,
                                                 str_value=str(the_input.value.value),
                                                 description=the_input.value.description)

    operations = interface.operations
    if operations:
        for operation_name, operation in operations.iteritems():
            model.operation_templates[operation_name] = create_operation_template(context,
                                                                                  service_template,
                                                                                  operation)

    return model if model.operation_templates else None


def create_operation_template(context, service_template, operation): # pylint: disable=unused-argument
    model = OperationTemplate(name=operation._name)

    if operation.description:
        model.description = operation.description.value

    implementation = operation.implementation
    if (implementation is not None) and operation.implementation.primary:
        model.plugin, model.implementation = \
            _parse_implementation(context, service_template, operation.implementation.primary)

        dependencies = implementation.dependencies
        if dependencies is not None:
            model.dependencies = dependencies

    inputs = operation.inputs
    if inputs:
        for input_name, the_input in inputs.iteritems():
            model.inputs[input_name] = Parameter(name=input_name,
                                                 type_name=the_input.value.type,
                                                 str_value=str(the_input.value.value),
                                                 description=the_input.value.description)

    # Dry
    implementation = model.implementation
    model.implementation = '{0}.{1}'.format(__name__, '_dry_node')
    model.inputs['_implementation'] = Parameter(name='_implementation',
                                                type_name='str',
                                                str_value=implementation)
    model.inputs['_plugin'] = Parameter(name='_plugin',
                                        type_name='str',
                                        str_value=model.plugin.name
                                            if model.plugin is not None
                                            else None)

    return model

from aria.orchestrator.decorators import operation
from threading import RLock

_TERMINAL_LOCK = RLock()

@operation
def _dry_node(ctx, _plugin, _implementation, **kwargs):
    with _TERMINAL_LOCK:
        puts('> node instance: %s' % Colored.red(ctx.node.name))
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
        puts('  plugin: %s' % Colored.magenta(plugin))
    if implementation:
        puts('  implementation: %s' % Colored.yellow(safe_repr(implementation)))


def _parse_implementation(context, service_template, implementation):
    if not implementation:
        return None, ''

    index = implementation.find('>')
    if index == -1:
        return None, implementation
    plugin_name = implementation[:index].strip()
    
    if plugin_name == 'execution':
        plugin = None
    else:
        plugin = service_template.plugins.get(plugin_name)
        if plugin is None:
            raise ValueError('unknown plugin: "{0}"'.format(plugin_name))

    implementation = implementation[index+1:].strip()
    return plugin, implementation


def create_artifact_template(context, artifact):
    model = ArtifactTemplate(name=artifact._name, type_name=artifact.type,
                             source_path=artifact.file)

    if artifact.description:
        model.description = artifact.description.value

    model.target_path = artifact.deploy_path

    repository = artifact._get_repository(context)
    if repository is not None:
        model.repository_url = repository.url
        credential = repository._get_credential(context)
        if credential:
            model.repository_credential = {}
            for k, v in credential.iteritems():
                model.repository_credential[k] = v

    create_properties_from_values(model.properties, artifact._get_property_values(context))

    return model


def create_requirement_template(context, service_template, requirement):
    model = {'name': requirement._name}

    node, node_variant = requirement._get_node(context)
    if node is not None:
        if node_variant == 'node_type':
            model['target_node_type_name'] = node._name
        else:
            model['target_node_template_name'] = node._name

    capability, capability_variant = requirement._get_capability(context)
    if capability is not None:
        if capability_variant == 'capability_type':
            model['target_capability_type_name'] = capability._name
        else:
            model['target_capability_name'] = capability._name

    model = RequirementTemplate(**model)

    if model.target_node_template_constraints:
        model.target_node_template_constraints = []
        create_node_filter_constraint_lambdas(context, requirement.node_filter,
                                              model.target_node_template_constraints)

    relationship = requirement.relationship
    if relationship is not None:
        model.relationship_template = create_relationship_template(context, service_template,
                                                                   relationship)

    return model


def create_relationship_type(context, relationship_type): # pylint: disable=unused-argument
    return RelationshipType(relationship_type._name)


def create_policy_type(context, policy_type): # pylint: disable=unused-argument
    return PolicyType(policy_type._name)


def create_relationship_template(context, service_template, relationship):
    relationship_type, relationship_type_variant = relationship._get_type(context)
    if relationship_type_variant == 'relationship_type':
        model = RelationshipTemplate(type_name=relationship_type._name)
    else:
        relationship_template = relationship_type
        relationship_type = relationship_template._get_type(context)
        model = RelationshipTemplate(type_name=relationship_type._name,
                                     template_name=relationship_template._name)
        if relationship_template.description:
            model.description = relationship_template.description.value

    create_properties_from_assignments(model.properties, relationship.properties)
    create_interface_templates(context, service_template, model.interface_templates,
                               relationship.interfaces)

    return model


def create_capability_template(context, capability):
    capability_type = capability._get_type(context)
    model = CapabilityTemplate(name=capability._name, type_name=capability_type._name)

    capability_definition = capability._get_definition(context)
    if capability_definition.description:
        model.description = capability_definition.description.value
    occurrences = capability_definition.occurrences
    if occurrences is not None:
        model.min_occurrences = occurrences.value[0]
        if occurrences.value[1] != 'UNBOUNDED':
            model.max_occurrences = occurrences.value[1]

    valid_source_types = capability_definition.valid_source_types
    if valid_source_types:
        model.valid_source_node_type_names = valid_source_types

    create_properties_from_assignments(model.properties, capability.properties)

    return model


def create_group_template(context, service_template, group):
    group_type = group._get_type(context)
    model = GroupTemplate(name=group._name, type_name=group_type._name)

    if group.description:
        model.description = group.description.value

    create_properties_from_values(model.properties, group._get_property_values(context))
    create_interface_templates(context, service_template, model.interface_templates,
                               group._get_interfaces(context))

    members = group.members
    if members:
        model.member_node_template_names = []
        for member in members:
            model.member_node_template_names.append(member)

    return model


def create_policy_template(context, policy):
    policy_type = policy._get_type(context)
    model = PolicyTemplate(name=policy._name, type_name=policy_type._name)

    if policy.description:
        model.description = policy.description.value

    create_properties_from_values(model.properties, policy._get_property_values(context))

    node_templates, groups = policy._get_targets(context)
    if node_templates:
        model.target_node_template_names = []
        for node_template in node_templates:
            model.target_node_template_names.append(node_template._name)
    if groups:
        model.target_group_template_names = []
        for group in groups:
            model.target_group_template_names.append(group._name)

    return model


#
# Utils
#

def create_types(context, root, types, normalize=None):
    if types is None:
        return

    def added_all():
        for name in types:
            if root.get_descendant(name) is None:
                return False
        return True

    while not added_all():
        for name, the_type in types.iteritems():
            if root.get_descendant(name) is None:
                parent_type = the_type._get_parent(context)
                if normalize:
                    model = normalize(context, the_type)
                else:
                    model = Type(the_type._name)
                if the_type.description:
                    model.description = the_type.description.value
                model.role = the_type._get_extension('role')
                if parent_type is None:
                    root.children.append(model)
                else:
                    container = root.get_descendant(parent_type._name)
                    if container is not None:
                        container.children.append(model)


def create_properties_from_values(properties, source_properties):
    if source_properties:
        for property_name, prop in source_properties.iteritems():
            properties[property_name] = Parameter(name=property_name,
                                                  type_name=prop.type,
                                                  str_value=str(prop.value),
                                                  description=prop.description)


def create_properties_from_assignments(properties, source_properties):
    if source_properties:
        for property_name, prop in source_properties.iteritems():
            properties[property_name] = Parameter(name=property_name,
                                                  type_name=prop.value.type,
                                                  str_value=str(prop.value.value),
                                                  description=prop.value.description)


def create_interface_templates(context, service_template, interfaces, source_interfaces):
    if source_interfaces:
        for interface_name, interface in source_interfaces.iteritems():
            interface = create_interface_template(context, service_template, interface)
            if interface is not None:
                interfaces[interface_name] = interface


def create_node_filter_constraint_lambdas(context, node_filter, target_node_template_constraints):
    if node_filter is None:
        return

    properties = node_filter.properties
    if properties is not None:
        for property_name, constraint_clause in properties:
            func = create_constraint_clause_lambda(context, node_filter, constraint_clause,
                                                   property_name, None)
            if func is not None:
                target_node_template_constraints.append(func)

    capabilities = node_filter.capabilities
    if capabilities is not None:
        for capability_name, capability in capabilities:
            properties = capability.properties
            if properties is not None:
                for property_name, constraint_clause in properties:
                    func = create_constraint_clause_lambda(context, node_filter, constraint_clause,
                                                           property_name, capability_name)
                    if func is not None:
                        target_node_template_constraints.append(func)


def create_constraint_clause_lambda(context, node_filter, constraint_clause, property_name, # pylint: disable=too-many-return-statements
                                    capability_name):
    constraint_key = constraint_clause._raw.keys()[0]
    the_type = constraint_clause._get_type(context)

    def coerce_constraint(constraint, container):
        constraint = coerce_value(context, node_filter, the_type, None, None, constraint,
                                  constraint_key) if the_type is not None else constraint
        if hasattr(constraint, '_evaluate'):
            constraint = constraint._evaluate(context, container)
        return constraint

    def get_value(node_type):
        if capability_name is not None:
            capability = node_type.capability_templates.get(capability_name)
            prop = capability.properties.get(property_name) if capability is not None else None
            return prop.value if prop is not None else None
        value = node_type.properties.get(property_name)
        return value.value if value is not None else None

    if constraint_key == 'equal':
        def equal(node_type, container):
            constraint = coerce_constraint(constraint_clause.equal, container)
            value = get_value(node_type)
            return value == constraint

        return equal

    elif constraint_key == 'greater_than':
        def greater_than(node_type, container):
            constraint = coerce_constraint(constraint_clause.greater_than, container)
            value = get_value(node_type)
            return value > constraint

        return greater_than

    elif constraint_key == 'greater_or_equal':
        def greater_or_equal(node_type, container):
            constraint = coerce_constraint(constraint_clause.greater_or_equal, container)
            value = get_value(node_type)
            return value >= constraint

        return greater_or_equal

    elif constraint_key == 'less_than':
        def less_than(node_type, container):
            constraint = coerce_constraint(constraint_clause.less_than, container)
            value = get_value(node_type)
            return value < constraint

        return less_than

    elif constraint_key == 'less_or_equal':
        def less_or_equal(node_type, container):
            constraint = coerce_constraint(constraint_clause.less_or_equal, container)
            value = get_value(node_type)
            return value <= constraint

        return less_or_equal

    elif constraint_key == 'in_range':
        def in_range(node_type, container):
            lower, upper = constraint_clause.in_range
            lower, upper = coerce_constraint(lower, container), coerce_constraint(upper, container)
            value = get_value(node_type)
            if value < lower:
                return False
            if (upper != 'UNBOUNDED') and (value > upper):
                return False
            return True

        return in_range

    elif constraint_key == 'valid_values':
        def valid_values(node_type, container):
            constraint = tuple(coerce_constraint(v, container)
                               for v in constraint_clause.valid_values)
            value = get_value(node_type)
            return value in constraint

        return valid_values

    elif constraint_key == 'length':
        def length(node_type, container): # pylint: disable=unused-argument
            constraint = constraint_clause.length
            value = get_value(node_type)
            return len(value) == constraint

        return length

    elif constraint_key == 'min_length':
        def min_length(node_type, container): # pylint: disable=unused-argument
            constraint = constraint_clause.min_length
            value = get_value(node_type)
            return len(value) >= constraint

        return min_length

    elif constraint_key == 'max_length':
        def max_length(node_type, container): # pylint: disable=unused-argument
            constraint = constraint_clause.max_length
            value = get_value(node_type)
            return len(value) >= constraint

        return max_length

    elif constraint_key == 'pattern':
        def pattern(node_type, container): # pylint: disable=unused-argument
            constraint = constraint_clause.pattern
            # Note: the TOSCA 1.0 spec does not specify the regular expression grammar, so we will
            # just use Python's
            value = node_type.properties.get(property_name)
            return re.match(constraint, str(value)) is not None

        return pattern

    return None
