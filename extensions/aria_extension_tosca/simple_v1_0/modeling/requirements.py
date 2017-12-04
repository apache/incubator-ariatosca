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

from aria.parser.validation import Issue
from aria.utils.collections import (deepcopy_with_locators, OrderedDict)

from .parameters import (convert_parameter_definitions_to_values, validate_required_values,
                         coerce_parameter_value)
from .interfaces import (convert_requirement_interface_definitions_from_type_to_raw_template,
                         merge_interface_definitions, merge_interface, validate_required_inputs)


#
# NodeType
#

def get_inherited_requirement_definitions(context, presentation):
    """
    Returns our requirement definitions added on top of those of our parent, if we have one
    (recursively).

    Allows overriding requirement definitions if they have the same name.
    """

    parent = presentation._get_parent(context)
    requirement_definitions = get_inherited_requirement_definitions(context, parent) \
        if parent is not None else []

    our_requirement_definitions = presentation.requirements
    if our_requirement_definitions:
        for requirement_name, our_requirement_definition in our_requirement_definitions:
            # Remove existing requirement definitions of this name if they exist
            for name, requirement_definition in requirement_definitions:
                if name == requirement_name:
                    requirement_definitions.remove((name, requirement_definition))

            requirement_definitions.append((requirement_name, our_requirement_definition))

    return requirement_definitions


#
# NodeTemplate
#

def get_template_requirements(context, presentation):
    """
    Returns our requirements added on top of those of the node type if they exist there.

    If the requirement has a relationship, the relationship properties and interfaces are assigned.

    Returns the assigned property, interface input, and interface operation input values while
    making sure they are defined in our type. Default values, if available, will be used if we did
    not assign them. Also makes sure that required properties and inputs indeed end up with a value.
    """

    requirement_assignments = []

    the_type = presentation._get_type(context) # NodeType
    requirement_definitions = the_type._get_requirements(context) if the_type is not None else None

    # Add our requirement assignments
    our_requirement_assignments = presentation.requirements
    if our_requirement_assignments:
        add_requirement_assignments(context, presentation, requirement_assignments,
                                    requirement_definitions, our_requirement_assignments)

    # Validate occurrences
    if requirement_definitions:
        for requirement_name, requirement_definition in requirement_definitions:
            # Allowed occurrences
            allowed_occurrences = requirement_definition.occurrences

            # Count actual occurrences
            actual_occurrences = 0
            for name, _ in requirement_assignments:
                if name == requirement_name:
                    actual_occurrences += 1

            if allowed_occurrences is None:
                # If not specified, we interpret this to mean that exactly 1 occurrence is required
                if actual_occurrences == 0:
                    # If it's not there, we will automatically add it (this behavior is not in the
                    # TOSCA spec, but seems implied)
                    requirement_assignment, \
                    relationship_property_definitions, \
                    relationship_interface_definitions = \
                        convert_requirement_from_definition_to_assignment(context,
                                                                          requirement_definition,
                                                                          None, presentation)
                    validate_requirement_assignment(context, presentation, requirement_assignment,
                                                    relationship_property_definitions,
                                                    relationship_interface_definitions,
                                                    requirement_definition)
                    requirement_assignments.append((requirement_name, requirement_assignment))
                elif actual_occurrences > 1:
                    context.validation.report(
                        u'requirement "{0}" is allowed only one occurrence in "{1}": {2:d}'
                        .format(requirement_name, presentation._fullname, actual_occurrences),
                        locator=presentation._locator, level=Issue.BETWEEN_TYPES)
            else:
                if not allowed_occurrences.is_in(actual_occurrences):
                    if allowed_occurrences.value[1] == 'UNBOUNDED':
                        context.validation.report(
                            u'requirement "{0}" does not have at least {1:d} occurrences in "{3}":'
                            u' has {4:d}'
                            .format(requirement_name, allowed_occurrences.value[0],
                                    presentation._fullname, actual_occurrences),
                            locator=presentation._locator, level=Issue.BETWEEN_TYPES)
                    else:
                        context.validation.report(
                            u'requirement "{0}" is allowed between {1:d} and {2:d} occurrences in'
                            u' "{3}": has {4:d}'
                            .format(requirement_name, allowed_occurrences.value[0],
                                    allowed_occurrences.value[1], presentation._fullname,
                                    actual_occurrences),
                            locator=presentation._locator, level=Issue.BETWEEN_TYPES)

    return requirement_assignments


#
# Utils
#

def convert_requirement_from_definition_to_assignment(context, requirement_definition,              # pylint: disable=too-many-branches
                                                      our_requirement_assignment, container):
    from ..assignments import RequirementAssignment

    raw = OrderedDict()

    # Capability type name:
    raw['capability'] = deepcopy_with_locators(requirement_definition.capability)

    node_type = requirement_definition._get_node_type(context)
    if node_type is not None:
        raw['node'] = deepcopy_with_locators(node_type._name)

    relationship_type = None
    relationship_template = None
    relationship_property_definitions = None
    relationship_interface_definitions = None

    # First try to find the relationship if we declared it
    # RelationshipAssignment:
    our_relationship = our_requirement_assignment.relationship \
        if our_requirement_assignment is not None else None
    if our_relationship is not None:
        relationship_type, relationship_type_variant = our_relationship._get_type(context)
        if relationship_type_variant == 'relationship_template':
            relationship_template = relationship_type
            relationship_type = relationship_template._get_type(context)

    definition_relationship_type = None
    relationship_definition = requirement_definition.relationship # RelationshipDefinition
    if relationship_definition is not None:
        definition_relationship_type = relationship_definition._get_type(context)

    # If not exists, try at the node type
    if relationship_type is None:
        relationship_type = definition_relationship_type
    else:
        # Make sure the type is derived
        if not definition_relationship_type._is_descendant(context, relationship_type):
            context.validation.report(
                u'assigned relationship type "{0}" is not a descendant of declared relationship '
                u' type "{1}"'
                .format(relationship_type._name, definition_relationship_type._name),
                locator=container._locator, level=Issue.BETWEEN_TYPES)

    if relationship_type is not None:
        raw['relationship'] = OrderedDict()

        type_name = our_relationship.type if our_relationship is not None else None
        if type_name is None:
            type_name = relationship_type._name

        raw['relationship']['type'] = deepcopy_with_locators(type_name)

        # These are our property definitions
        relationship_property_definitions = relationship_type._get_properties(context)

        if relationship_template is not None:
            # Property values from template
            raw['relationship']['properties'] = relationship_template._get_property_values(context)
        else:
            if relationship_property_definitions:
                # Convert property definitions to values
                raw['relationship']['properties'] = \
                    convert_parameter_definitions_to_values(context,
                                                            relationship_property_definitions)

        # These are our interface definitions
        # InterfaceDefinition:
        relationship_interface_definitions = OrderedDict(relationship_type._get_interfaces(context))

        # Convert interface definitions to templates
        convert_requirement_interface_definitions_from_type_to_raw_template(
            context,
            raw['relationship'],
            relationship_interface_definitions)

        if relationship_definition:
            # Merge extra interface definitions
            # InterfaceDefinition:
            definition_interface_definitions = relationship_definition.interfaces
            merge_interface_definitions(context, relationship_interface_definitions,
                                        definition_interface_definitions, requirement_definition,
                                        container)

        if relationship_template is not None:
            # Interfaces from template
            interfaces = relationship_template._get_interfaces(context)
            if interfaces:
                raw['relationship']['interfaces'] = OrderedDict()
                for interface_name, interface in interfaces.iteritems():
                    raw['relationship']['interfaces'][interface_name] = interface._raw

    return \
        RequirementAssignment(name=requirement_definition._name, raw=raw, container=container), \
        relationship_property_definitions, \
        relationship_interface_definitions


def add_requirement_assignments(context, presentation, requirement_assignments,
                                requirement_definitions, our_requirement_assignments):
    for requirement_name, our_requirement_assignment in our_requirement_assignments:
        requirement_definition = get_first_requirement(requirement_definitions, requirement_name)
        if requirement_definition is not None:
            requirement_assignment, \
            relationship_property_definitions, \
            relationship_interface_definitions = \
                convert_requirement_from_definition_to_assignment(context, requirement_definition,
                                                                  our_requirement_assignment,
                                                                  presentation)
            merge_requirement_assignment(context,
                                         relationship_property_definitions,
                                         relationship_interface_definitions,
                                         requirement_assignment, our_requirement_assignment)
            validate_requirement_assignment(context,
                                            our_requirement_assignment.relationship \
                                            or our_requirement_assignment,
                                            requirement_assignment,
                                            relationship_property_definitions,
                                            relationship_interface_definitions,
                                            requirement_definition)
            requirement_assignments.append((requirement_name, requirement_assignment))
        else:
            context.validation.report(u'requirement "{0}" not declared at node type "{1}" in "{2}"'
                                      .format(requirement_name, presentation.type,
                                              presentation._fullname),
                                      locator=our_requirement_assignment._locator,
                                      level=Issue.BETWEEN_TYPES)


def merge_requirement_assignment(context, relationship_property_definitions,
                                 relationship_interface_definitions, requirement, our_requirement):
    our_capability = our_requirement.capability
    if our_capability is not None:
        requirement._raw['capability'] = deepcopy_with_locators(our_capability)

    our_node = our_requirement.node
    if our_node is not None:
        requirement._raw['node'] = deepcopy_with_locators(our_node)

    our_node_filter = our_requirement.node_filter
    if our_node_filter is not None:
        requirement._raw['node_filter'] = deepcopy_with_locators(our_node_filter._raw)

    our_relationship = our_requirement.relationship # RelationshipAssignment
    if our_relationship is not None:
        # Make sure we have a dict
        if 'relationship' not in requirement._raw:
            requirement._raw['relationship'] = OrderedDict()

        merge_requirement_assignment_relationship(context, our_relationship,
                                                  relationship_property_definitions,
                                                  relationship_interface_definitions,
                                                  requirement, our_relationship)


def merge_requirement_assignment_relationship(context, presentation, property_definitions,
                                              interface_definitions, requirement, our_relationship):
    our_relationship_properties = our_relationship._raw.get('properties') \
        if isinstance(our_relationship._raw, dict) else None
    if our_relationship_properties:
        # Make sure we have a dict
        if 'properties' not in requirement._raw['relationship']:
            requirement._raw['relationship']['properties'] = OrderedDict()

        # Merge our properties
        for property_name, prop in our_relationship_properties.iteritems():
            if property_name in property_definitions:
                definition = property_definitions[property_name]
                requirement._raw['relationship']['properties'][property_name] = \
                    coerce_parameter_value(context, presentation, definition, prop)
            else:
                context.validation.report(
                    u'relationship property "{0}" not declared at definition of requirement "{1}"'
                    u' in "{2}"'
                    .format(property_name, requirement._fullname,
                            presentation._container._container._fullname),
                    locator=our_relationship._get_child_locator('properties', property_name),
                    level=Issue.BETWEEN_TYPES)

    our_interfaces = our_relationship.interfaces
    if our_interfaces:
        # Make sure we have a dict
        if 'interfaces' not in requirement._raw['relationship']:
            requirement._raw['relationship']['interfaces'] = OrderedDict()

        # Merge interfaces
        for interface_name, our_interface in our_interfaces.iteritems():
            if interface_name not in requirement._raw['relationship']['interfaces']:
                requirement._raw['relationship']['interfaces'][interface_name] = OrderedDict()

            if (interface_definitions is not None) and (interface_name in interface_definitions):
                interface_definition = interface_definitions[interface_name]
                interface_assignment = requirement.relationship.interfaces[interface_name]
                merge_interface(context, presentation, interface_assignment, our_interface,
                                interface_definition, interface_name)
            else:
                context.validation.report(
                    u'relationship interface "{0}" not declared at definition of requirement "{1}"'
                    u' in "{2}"'
                    .format(interface_name, requirement._fullname,
                            presentation._container._container._fullname),
                    locator=our_relationship._locator, level=Issue.BETWEEN_TYPES)


def validate_requirement_assignment(context, presentation, requirement_assignment,
                                    relationship_property_definitions,
                                    relationship_interface_definitions, requirement_definition):
    # Validate node
    definition_node_type = requirement_definition._get_node_type(context)
    assignment_node_type, node_variant = requirement_assignment._get_node(context)
    if node_variant == 'node_template':
        assignment_node_type = assignment_node_type._get_type(context)
    if (assignment_node_type is not None) and (definition_node_type is not None) and \
        (assignment_node_type is not definition_node_type) and \
        (not definition_node_type._is_descendant(context, assignment_node_type)):
        context.validation.report(
            u'requirement assignment node "{0}" is not derived from node type "{1}" of requirement '
            u'definition in {2}'
            .format(requirement_assignment.node, requirement_definition.node,
                    presentation._container._fullname),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)

    # Validate capability
    definition_capability_type = requirement_definition._get_capability_type(context)
    assignment_capability_type, capability_variant = requirement_assignment._get_capability(context)
    if capability_variant == 'capability_assignment':
        assignment_capability_type = assignment_capability_type._get_type(context)
    if (assignment_capability_type is not None) and (definition_capability_type is not None) and \
        (assignment_capability_type is not definition_capability_type) and \
        (not definition_capability_type._is_descendant(context, assignment_capability_type)):
        context.validation.report(
            u'requirement assignment capability "{0}" is not derived from capability type "{1}" of '
            u'requirement definition in {2}'
            .format(requirement_assignment.capability, requirement_definition.capability,
                    presentation._container._fullname),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)

    relationship = requirement_assignment.relationship

    values = OrderedDict((name, prop.value)
                         for name, prop in relationship.properties.iteritems()) \
                         if (relationship and relationship.properties) else {}
    validate_required_values(context, presentation, values, relationship_property_definitions)

    if relationship_interface_definitions:
        for interface_name, relationship_interface_definition \
            in relationship_interface_definitions.iteritems():
            interface_assignment = relationship.interfaces.get(interface_name) \
                if (relationship and relationship.interfaces) else None
            validate_required_inputs(context, presentation, interface_assignment,
                                     relationship_interface_definition, None, interface_name)


def get_first_requirement(requirement_definitions, name):
    if requirement_definitions is not None:
        for requirement_name, requirement_definition in requirement_definitions:
            if requirement_name == name:
                return requirement_definition
    return None
