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
Creates ARIA service template models based on the TOSCA presentation.

Relies on many helper methods in the presentation classes.
"""

#pylint: disable=unsubscriptable-object

import os
import re
from types import FunctionType
from datetime import datetime

from ruamel import yaml

from aria.parser.validation import Issue
from aria.utils.formatting import string_list_as_string
from aria.utils.collections import (StrictDict, OrderedDict)
from aria.orchestrator import WORKFLOW_DECORATOR_RESERVED_ARGUMENTS
from aria.modeling.models import (Type, ServiceTemplate, NodeTemplate,
                                  RequirementTemplate, RelationshipTemplate, CapabilityTemplate,
                                  GroupTemplate, PolicyTemplate, SubstitutionTemplate,
                                  SubstitutionTemplateMapping, InterfaceTemplate, OperationTemplate,
                                  ArtifactTemplate, Metadata, Input, Output, Property,
                                  Attribute, Configuration, PluginSpecification)

from .parameters import coerce_parameter_value
from .constraints import (Equal, GreaterThan, GreaterOrEqual, LessThan, LessOrEqual, InRange,
                          ValidValues, Length, MinLength, MaxLength, Pattern)
from ..data_types import coerce_value


# These match the first un-escaped ">"
# See: http://stackoverflow.com/a/11819111/849021
IMPLEMENTATION_PREFIX_REGEX = re.compile(r'(?<!\\)(?:\\\\)*>')


def create_service_template_model(context): # pylint: disable=too-many-locals,too-many-branches
    model = ServiceTemplate(created_at=datetime.now(),
                            main_file_name=os.path.basename(str(context.presentation.location)))

    model.description = context.presentation.get('service_template', 'description', 'value')

    # Metadata
    metadata = context.presentation.get('service_template', 'metadata')
    if metadata is not None:
        create_metadata_models(context, model, metadata)

    # Types
    model.node_types = Type(variant='node')
    create_types(context,
                 model.node_types,
                 context.presentation.get('service_template', 'node_types'))
    model.group_types = Type(variant='group')
    create_types(context,
                 model.group_types,
                 context.presentation.get('service_template', 'group_types'))
    model.policy_types = Type(variant='policy')
    create_types(context,
                 model.policy_types,
                 context.presentation.get('service_template', 'policy_types'))
    model.relationship_types = Type(variant='relationship')
    create_types(context,
                 model.relationship_types,
                 context.presentation.get('service_template', 'relationship_types'))
    model.capability_types = Type(variant='capability')
    create_types(context,
                 model.capability_types,
                 context.presentation.get('service_template', 'capability_types'))
    model.interface_types = Type(variant='interface')
    create_types(context,
                 model.interface_types,
                 context.presentation.get('service_template', 'interface_types'))
    model.artifact_types = Type(variant='artifact')
    create_types(context,
                 model.artifact_types,
                 context.presentation.get('service_template', 'artifact_types'))

    # Topology template
    topology_template = context.presentation.get('service_template', 'topology_template')
    if topology_template is not None:
        create_parameter_models_from_values(model.inputs,
                                            topology_template._get_input_values(context),
                                            model_cls=Input)
        create_parameter_models_from_values(model.outputs,
                                            topology_template._get_output_values(context),
                                            model_cls=Output)

    # Plugin specifications
    policies = context.presentation.get('service_template', 'topology_template', 'policies')
    if policies:
        for policy in policies.itervalues():
            role = model.policy_types.get_descendant(policy.type).role
            if role == 'plugin':
                plugin_specification = create_plugin_specification_model(context, policy)
                model.plugin_specifications[plugin_specification.name] = plugin_specification
            elif role == 'workflow':
                operation_template = create_workflow_operation_template_model(context,
                                                                              model, policy)
                model.workflow_templates[operation_template.name] = operation_template

    # Node templates
    node_templates = context.presentation.get('service_template', 'topology_template',
                                              'node_templates')
    if node_templates:
        for node_template in node_templates.itervalues():
            node_template_model = create_node_template_model(context, model, node_template)
            model.node_templates[node_template_model.name] = node_template_model
        for node_template in node_templates.itervalues():
            fix_node_template_model(context, model, node_template)

    # Group templates
    groups = context.presentation.get('service_template', 'topology_template', 'groups')
    if groups:
        for group in groups.itervalues():
            group_template_model = create_group_template_model(context, model, group)
            model.group_templates[group_template_model.name] = group_template_model

    # Policy templates
    policies = context.presentation.get('service_template', 'topology_template', 'policies')
    if policies:
        for policy in policies.itervalues():
            policy_template_model = create_policy_template_model(context, model, policy)
            model.policy_templates[policy_template_model.name] = policy_template_model

    # Substitution template
    substitution_mappings = context.presentation.get('service_template', 'topology_template',
                                                     'substitution_mappings')
    if substitution_mappings:
        model.substitution_template = create_substitution_template_model(context, model,
                                                                         substitution_mappings)

    return model


def create_metadata_models(context, service_template, metadata):
    service_template.meta_data['template_name'] = Metadata(name='template_name',
                                                           value=metadata.template_name)
    service_template.meta_data['template_author'] = Metadata(name='template_author',
                                                             value=metadata.template_author)
    service_template.meta_data['template_version'] = Metadata(name='template_version',
                                                              value=metadata.template_version)
    custom = metadata.custom
    if custom:
        for name, value in custom.iteritems():
            service_template.meta_data[name] = Metadata(name=name,
                                                        value=value)


def create_node_template_model(context, service_template, node_template):
    node_type = node_template._get_type(context)
    node_type = service_template.node_types.get_descendant(node_type._name)
    model = NodeTemplate(name=node_template._name,
                         type=node_type)

    model.default_instances = 1
    model.min_instances = 0

    if node_template.description:
        model.description = node_template.description.value

    create_parameter_models_from_values(model.properties,
                                        node_template._get_property_values(context),
                                        model_cls=Property)
    create_parameter_models_from_values(model.attributes,
                                        node_template._get_attribute_default_values(context),
                                        model_cls=Attribute)
    create_interface_template_models(context, service_template, model.interface_templates,
                                     node_template._get_interfaces(context))

    artifacts = node_template._get_artifacts(context)
    if artifacts:
        for artifact_name, artifact in artifacts.iteritems():
            model.artifact_templates[artifact_name] = \
                create_artifact_template_model(context, service_template, artifact)

    capabilities = node_template._get_capabilities(context)
    if capabilities:
        for capability_name, capability in capabilities.iteritems():
            model.capability_templates[capability_name] = \
                create_capability_template_model(context, service_template, capability)

    if node_template.node_filter:
        model.target_node_template_constraints = []
        create_node_filter_constraints(context, node_template.node_filter,
                                       model.target_node_template_constraints)

    return model


def fix_node_template_model(context, service_template, node_template):
    # Requirements have to be created after all node templates have been created, because
    # requirements might reference another node template
    model = service_template.node_templates[node_template._name]
    requirements = node_template._get_requirements(context)
    if requirements:
        for _, requirement in requirements:
            model.requirement_templates.append(create_requirement_template_model(context,
                                                                                 service_template,
                                                                                 requirement))


def create_group_template_model(context, service_template, group):
    group_type = group._get_type(context)
    group_type = service_template.group_types.get_descendant(group_type._name)
    model = GroupTemplate(name=group._name,
                          type=group_type)

    if group.description:
        model.description = group.description.value

    create_parameter_models_from_values(model.properties, group._get_property_values(context),
                                        model_cls=Property)
    create_interface_template_models(context, service_template, model.interface_templates,
                                     group._get_interfaces(context))

    members = group.members
    if members:
        for member in members:
            node_template = service_template.node_templates[member]
            assert node_template
            model.node_templates.append(node_template)

    return model


def create_policy_template_model(context, service_template, policy):
    policy_type = policy._get_type(context)
    policy_type = service_template.policy_types.get_descendant(policy_type._name)
    model = PolicyTemplate(name=policy._name,
                           type=policy_type)

    if policy.description:
        model.description = policy.description.value

    create_parameter_models_from_values(model.properties, policy._get_property_values(context),
                                        model_cls=Property)

    node_templates, groups = policy._get_targets(context)
    if node_templates:
        for target in node_templates:
            node_template = service_template.node_templates[target._name]
            assert node_template
            model.node_templates.append(node_template)
    if groups:
        for target in groups:
            group_template = service_template.group_templates[target._name]
            assert group_template
            model.group_templates.append(group_template)

    return model


def create_requirement_template_model(context, service_template, requirement):
    model = {'name': requirement._name}

    node, node_variant = requirement._get_node(context)
    if node is not None:
        if node_variant == 'node_type':
            node_type = service_template.node_types.get_descendant(node._name)
            model['target_node_type'] = node_type
        else:
            node_template = service_template.node_templates[node._name]
            model['target_node_template'] = node_template

    capability, capability_variant = requirement._get_capability(context)
    if capability is not None:
        if capability_variant == 'capability_type':
            capability_type = \
                service_template.capability_types.get_descendant(capability._name)
            model['target_capability_type'] = capability_type
        else:
            model['target_capability_name'] = capability._name

    model = RequirementTemplate(**model)

    if requirement.node_filter:
        model.target_node_template_constraints = []
        create_node_filter_constraints(context, requirement.node_filter,
                                       model.target_node_template_constraints)

    relationship = requirement.relationship
    if relationship is not None:
        model.relationship_template = \
            create_relationship_template_model(context, service_template, relationship)
        model.relationship_template.name = requirement._name

    return model


def create_relationship_template_model(context, service_template, relationship):
    relationship_type, relationship_type_variant = relationship._get_type(context)
    if relationship_type_variant == 'relationship_type':
        relationship_type = service_template.relationship_types.get_descendant(
            relationship_type._name)
        model = RelationshipTemplate(type=relationship_type)
    else:
        relationship_template = relationship_type
        relationship_type = relationship_template._get_type(context)
        relationship_type = service_template.relationship_types.get_descendant(
            relationship_type._name)
        model = RelationshipTemplate(type=relationship_type)
        if relationship_template.description:
            model.description = relationship_template.description.value

    create_parameter_models_from_assignments(model.properties,
                                             relationship.properties,
                                             model_cls=Property)
    create_interface_template_models(context, service_template, model.interface_templates,
                                     relationship.interfaces)

    return model


def create_capability_template_model(context, service_template, capability):
    capability_type = capability._get_type(context)
    capability_type = service_template.capability_types.get_descendant(capability_type._name)
    model = CapabilityTemplate(name=capability._name,
                               type=capability_type)

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
        for valid_source_type in valid_source_types:
            # TODO: handle shortcut type names
            node_type = service_template.node_types.get_descendant(valid_source_type)
            model.valid_source_node_types.append(node_type)

    create_parameter_models_from_assignments(model.properties,
                                             capability.properties,
                                             model_cls=Property)

    return model


def create_interface_template_model(context, service_template, interface):
    interface_type = interface._get_type(context)
    interface_type = service_template.interface_types.get_descendant(interface_type._name)
    model = InterfaceTemplate(name=interface._name,
                              type=interface_type)

    if interface_type.description:
        model.description = interface_type.description

    inputs = interface.inputs
    if inputs:
        for input_name, the_input in inputs.iteritems():
            model.inputs[input_name] = Input(name=input_name, # pylint: disable=unexpected-keyword-arg
                                             type_name=the_input.value.type,
                                             value=the_input.value.value,
                                             description=the_input.value.description)

    operations = interface.operations
    if operations:
        for operation_name, operation in operations.iteritems():
            model.operation_templates[operation_name] = \
                create_operation_template_model(context, service_template, operation)

    return model if model.operation_templates else None


def create_operation_template_model(context, service_template, operation):
    model = OperationTemplate(name=operation._name)

    if operation.description:
        model.description = operation.description.value

    implementation = operation.implementation
    if implementation is not None:
        primary = implementation.primary
        extract_implementation_primary(context, service_template, operation, model, primary)
        relationship_edge = operation._get_extensions(context).get('relationship_edge')
        if relationship_edge is not None:
            if relationship_edge == 'source':
                model.relationship_edge = False
            elif relationship_edge == 'target':
                model.relationship_edge = True

        dependencies = implementation.dependencies
        configuration = OrderedDict()
        if dependencies:
            for dependency in dependencies:
                key, value = split_prefix(dependency)
                if key is not None:
                    # Special ARIA prefix: signifies configuration parameters

                    # Parse as YAML
                    try:
                        value = yaml.load(value)
                    except yaml.parser.MarkedYAMLError as e:
                        context.validation.report(
                            'YAML parser {0} in operation configuration: {1}'
                            .format(e.problem, value),
                            locator=implementation._locator,
                            level=Issue.FIELD)
                        continue

                    # Coerce to intrinsic functions, if there are any
                    value = coerce_parameter_value(context, implementation, None, value).value

                    # Support dot-notation nesting
                    set_nested(configuration, key.split('.'), value)
                else:
                    if model.dependencies is None:
                        model.dependencies = []
                    model.dependencies.append(dependency)

        # Convert configuration to Configuration models
        for key, value in configuration.iteritems():
            model.configurations[key] = Configuration.wrap(key, value,
                                                           description='Operation configuration.')

    inputs = operation.inputs
    if inputs:
        for input_name, the_input in inputs.iteritems():
            model.inputs[input_name] = Input(name=input_name, # pylint: disable=unexpected-keyword-arg
                                             type_name=the_input.value.type,
                                             value=the_input.value.value,
                                             description=the_input.value.description)

    return model


def create_artifact_template_model(context, service_template, artifact):
    artifact_type = artifact._get_type(context)
    artifact_type = service_template.artifact_types.get_descendant(artifact_type._name)
    model = ArtifactTemplate(name=artifact._name,
                             type=artifact_type,
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

    create_parameter_models_from_values(model.properties, artifact._get_property_values(context),
                                        model_cls=Property)

    return model


def create_substitution_template_model(context, service_template, substitution_mappings):
    node_type = service_template.node_types.get_descendant(substitution_mappings.node_type)
    model = SubstitutionTemplate(node_type=node_type)

    capabilities = substitution_mappings.capabilities
    if capabilities:
        for mapped_capability_name, capability in capabilities.iteritems():
            name = 'capability.' + mapped_capability_name
            node_template_model = service_template.node_templates[capability.node_template]
            capability_template_model = \
                node_template_model.capability_templates[capability.capability]
            model.mappings[name] = \
                SubstitutionTemplateMapping(name=name,
                                            node_template=node_template_model,
                                            capability_template=capability_template_model)

    requirements = substitution_mappings.requirements
    if requirements:
        for mapped_requirement_name, requirement in requirements.iteritems():
            name = 'requirement.' + mapped_requirement_name
            node_template_model = service_template.node_templates[requirement.node_template]
            requirement_template_model = None
            for a_model in node_template_model.requirement_templates:
                if a_model.name == requirement.requirement:
                    requirement_template_model = a_model
                    break
            model.mappings[name] = \
                SubstitutionTemplateMapping(name=name,
                                            node_template=node_template_model,
                                            requirement_template=requirement_template_model)

    return model


def create_plugin_specification_model(context, policy):
    properties = policy.properties

    def get(name, default=None):
        prop = properties.get(name)
        return prop.value if prop is not None else default

    model = PluginSpecification(name=policy._name,
                                version=get('version'),
                                enabled=get('enabled', True))

    return model


def create_workflow_operation_template_model(context, service_template, policy):
    model = OperationTemplate(name=policy._name,
                              service_template=service_template)

    if policy.description:
        model.description = policy.description.value

    properties = policy._get_property_values(context)
    for prop_name, prop in properties.iteritems():
        if prop_name == 'implementation':
            model.function = prop.value
        else:
            model.inputs[prop_name] = Input(name=prop_name, # pylint: disable=unexpected-keyword-arg
                                            type_name=prop.type,
                                            value=prop.value,
                                            description=prop.description)

    used_reserved_names = WORKFLOW_DECORATOR_RESERVED_ARGUMENTS.intersection(model.inputs.keys())
    if used_reserved_names:
        context.validation.report('using reserved arguments in workflow policy "{0}": {1}'
                                  .format(
                                      policy._name,
                                      string_list_as_string(used_reserved_names)),
                                  locator=policy._locator,
                                  level=Issue.EXTERNAL)

    return model


#
# Utils
#

def create_types(context, root, types):
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
                model = Type(name=the_type._name,
                             role=the_type._get_extension('role'))
                if the_type.description:
                    model.description = the_type.description.value
                if parent_type is None:
                    model.parent = root
                    model.variant = root.variant
                    root.children.append(model)
                else:
                    container = root.get_descendant(parent_type._name)
                    if container is not None:
                        model.parent = container
                        model.variant = container.variant
                        container.children.append(model)


def create_parameter_models_from_values(properties, source_properties, model_cls):

    if source_properties:
        for property_name, prop in source_properties.iteritems():
            properties[property_name] = model_cls(name=property_name,  # pylint: disable=unexpected-keyword-arg
                                                  type_name=prop.type,
                                                  value=prop.value,
                                                  description=prop.description)


def create_parameter_models_from_assignments(properties, source_properties, model_cls):
    if source_properties:
        for property_name, prop in source_properties.iteritems():
            properties[property_name] = model_cls(name=property_name, # pylint: disable=unexpected-keyword-arg
                                                  type_name=prop.value.type,
                                                  value=prop.value.value,
                                                  description=prop.value.description)


def create_interface_template_models(context, service_template, interfaces, source_interfaces):
    if source_interfaces:
        for interface_name, interface in source_interfaces.iteritems():
            interface = create_interface_template_model(context, service_template, interface)
            if interface is not None:
                interfaces[interface_name] = interface


def create_node_filter_constraints(context, node_filter, target_node_template_constraints):
    properties = node_filter.properties
    if properties is not None:
        for property_name, constraint_clause in properties:
            constraint = create_constraint(context, node_filter, constraint_clause, property_name,
                                           None)
            target_node_template_constraints.append(constraint)

    capabilities = node_filter.capabilities
    if capabilities is not None:
        for capability_name, capability in capabilities:
            properties = capability.properties
            if properties is not None:
                for property_name, constraint_clause in properties:
                    constraint = create_constraint(context, node_filter, constraint_clause,
                                                   property_name, capability_name)
                    target_node_template_constraints.append(constraint)


def create_constraint(context, node_filter, constraint_clause, property_name, capability_name): # pylint: disable=too-many-return-statements
    constraint_key = constraint_clause._raw.keys()[0]

    the_type = constraint_clause._get_type(context)

    def coerce_constraint(constraint):
        if the_type is not None:
            return coerce_value(context, node_filter, the_type, None, None, constraint,
                                constraint_key)
        else:
            return constraint

    def coerce_constraints(constraints):
        if the_type is not None:
            return tuple(coerce_constraint(constraint) for constraint in constraints)
        else:
            return constraints

    if constraint_key == 'equal':
        return Equal(property_name, capability_name,
                     coerce_constraint(constraint_clause.equal))
    elif constraint_key == 'greater_than':
        return GreaterThan(property_name, capability_name,
                           coerce_constraint(constraint_clause.greater_than))
    elif constraint_key == 'greater_or_equal':
        return GreaterOrEqual(property_name, capability_name,
                              coerce_constraint(constraint_clause.greater_or_equal))
    elif constraint_key == 'less_than':
        return LessThan(property_name, capability_name,
                        coerce_constraint(constraint_clause.less_than))
    elif constraint_key == 'less_or_equal':
        return LessOrEqual(property_name, capability_name,
                           coerce_constraint(constraint_clause.less_or_equal))
    elif constraint_key == 'in_range':
        return InRange(property_name, capability_name,
                       coerce_constraints(constraint_clause.in_range))
    elif constraint_key == 'valid_values':
        return ValidValues(property_name, capability_name,
                           coerce_constraints(constraint_clause.valid_values))
    elif constraint_key == 'length':
        return Length(property_name, capability_name,
                      coerce_constraint(constraint_clause.length))
    elif constraint_key == 'min_length':
        return MinLength(property_name, capability_name,
                         coerce_constraint(constraint_clause.min_length))
    elif constraint_key == 'max_length':
        return MaxLength(property_name, capability_name,
                         coerce_constraint(constraint_clause.max_length))
    elif constraint_key == 'pattern':
        return Pattern(property_name, capability_name,
                       coerce_constraint(constraint_clause.pattern))
    else:
        raise ValueError('malformed node_filter: {0}'.format(constraint_key))


def split_prefix(string):
    """
    Splits the prefix on the first non-escaped ">".
    """

    split = IMPLEMENTATION_PREFIX_REGEX.split(string, 1)
    if len(split) < 2:
        return None, None
    return split[0].strip(), split[1].strip()


def set_nested(the_dict, keys, value):
    """
    If the ``keys`` list has just one item, puts the value in the the dict. If there are more items,
    puts the value in a sub-dict, creating sub-dicts as necessary for each key.

    For example, if ``the_dict`` is an empty dict, keys is ``['first', 'second', 'third']`` and
    value is ``'value'``, then the_dict will be: ``{'first':{'second':{'third':'value'}}}``.

    :param the_dict: Dict to change
    :type the_dict: {}
    :param keys: Keys
    :type keys: [basestring]
    :param value: Value
    """
    key = keys.pop(0)
    if len(keys) == 0:
        the_dict[key] = value
    else:
        if key not in the_dict:
            the_dict[key] = StrictDict(key_class=basestring)
        set_nested(the_dict[key], keys, value)


def extract_implementation_primary(context, service_template, presentation, model, primary):
    prefix, postfix = split_prefix(primary)
    if prefix:
        # Special ARIA prefix
        model.plugin_specification = service_template.plugin_specifications.get(prefix)
        model.function = postfix
        if model.plugin_specification is None:
            context.validation.report(
                'no policy for plugin "{0}" specified in operation implementation: {1}'
                .format(prefix, primary),
                locator=presentation._get_child_locator('properties', 'implementation'),
                level=Issue.BETWEEN_TYPES)
    else:
        # Standard TOSCA artifact with default plugin
        model.implementation = primary
