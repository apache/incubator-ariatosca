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

from aria.utils.collections import deepcopy_with_locators, OrderedDict
from aria.parser.validation import Issue

from .parameters import (convert_parameter_definitions_to_values, merge_raw_parameter_definitions,
                         get_assigned_and_defined_parameter_values)


#
# CapabilityType
#

def get_inherited_valid_source_types(context, presentation):
    """
    If we haven't set the ``valid_source_types`` fields, uses that value from our parent, if we have
    one (recursively).
    """

    valid_source_types = presentation.valid_source_types

    if valid_source_types is None:
        parent = presentation._get_parent(context)
        valid_source_types = get_inherited_valid_source_types(context, parent) \
            if parent is not None else None

    return valid_source_types


#
# NodeType
#

def get_inherited_capability_definitions(context, presentation, for_presentation=None):
    """
    Returns our capability capability definitions added on top of those of our parent, if we have
    one (recursively).

    Allows overriding all aspects of parent capability properties except data type.
    """

    if for_presentation is None:
        for_presentation = presentation

    # Get capability definitions from parent
    parent = presentation._get_parent(context)
    capability_definitions = get_inherited_capability_definitions(
        context, parent, for_presentation) if parent is not None else OrderedDict()

    # Add/merge our capability definitions
    our_capability_definitions = presentation.capabilities
    if our_capability_definitions:
        for capability_name, our_capability_definition in our_capability_definitions.iteritems():
            if capability_name in capability_definitions:
                capability_definition = capability_definitions[capability_name]

                # Check if we changed the type
                type1 = capability_definition._get_type(context)
                type2 = our_capability_definition._get_type(context)

                if not type1._is_descendant(context, type2):
                    context.validation.report(
                        'capability definition type "{0}" is not a descendant of overridden '
                        'capability definition type "{1}"' \
                        .format(type1._name, type2._name),
                        locator=our_capability_definition._locator, level=Issue.BETWEEN_TYPES)

                merge_capability_definition(context, presentation, capability_definition,
                                            our_capability_definition)
            else:
                capability_definition = our_capability_definition._clone(for_presentation)
                if isinstance(capability_definition._raw, basestring):
                    # Make sure we have a dict
                    the_type = capability_definition._raw
                    capability_definition._raw = OrderedDict()
                    capability_definition._raw['type'] = the_type
                capability_definitions[capability_name] = capability_definition

            merge_capability_definition_from_type(context, presentation, capability_definition)

    for capability_definition in capability_definitions.itervalues():
        capability_definition._reset_method_cache()

    return capability_definitions


#
# NodeTemplate
#

def get_template_capabilities(context, presentation):
    """
    Returns the node type's capabilities with our assignments to properties and attributes merged
    in.

    Capability properties' default values, if available, will be used if we did not assign them.

    Makes sure that required properties indeed end up with a value.
    """

    capability_assignments = OrderedDict()

    the_type = presentation._get_type(context) # NodeType
    capability_definitions = the_type._get_capabilities(context) if the_type is not None else None

    # Copy over capability definitions from the type (will initialize properties with default
    # values)
    if capability_definitions:
        for capability_name, capability_definition in capability_definitions.iteritems():
            capability_assignments[capability_name] = \
                convert_capability_from_definition_to_assignment(context, capability_definition,
                                                                 presentation)

    # Fill in our capability assignments
    our_capability_assignments = presentation.capabilities
    if our_capability_assignments:
        for capability_name, our_capability_assignment in our_capability_assignments.iteritems():
            if capability_name in capability_assignments:
                capability_assignment = capability_assignments[capability_name]

                # Assign properties
                values = get_assigned_and_defined_parameter_values(context,
                                                                   our_capability_assignment,
                                                                   'property')

                if values:
                    capability_assignment._raw['properties'] = values
                    capability_assignment._reset_method_cache()
            else:
                context.validation.report(
                    'capability "{0}" not declared at node type "{1}" in "{2}"'
                    .format(capability_name, presentation.type, presentation._fullname),
                    locator=our_capability_assignment._locator, level=Issue.BETWEEN_TYPES)

    return capability_assignments


#
# Utils
#

def convert_capability_from_definition_to_assignment(context, presentation, container):
    from ..assignments import CapabilityAssignment

    raw = OrderedDict()

    properties = presentation.properties
    if properties is not None:
        raw['properties'] = convert_parameter_definitions_to_values(context, properties)

    # TODO attributes

    return CapabilityAssignment(name=presentation._name, raw=raw, container=container)


def merge_capability_definition(context, presentation, capability_definition,
                                from_capability_definition):
    raw_properties = OrderedDict()

    capability_definition._raw['type'] = from_capability_definition.type

    # Merge properties from type
    from_property_defintions = from_capability_definition.properties
    merge_raw_parameter_definitions(context, presentation, raw_properties, from_property_defintions,
                                    'properties')

    # Merge our properties
    merge_raw_parameter_definitions(context, presentation, raw_properties,
                                    capability_definition.properties, 'properties')

    if raw_properties:
        capability_definition._raw['properties'] = raw_properties
        capability_definition._reset_method_cache()

    # Merge occurrences
    occurrences = from_capability_definition._raw.get('occurrences')
    if (occurrences is not None) and (capability_definition._raw.get('occurrences') is None):
        capability_definition._raw['occurrences'] = \
            deepcopy_with_locators(occurrences)


def merge_capability_definition_from_type(context, presentation, capability_definition):
    """
    Merge ``properties`` and ``valid_source_types`` from the node type's capability definition
    over those taken from the parent node type.
    """
    raw_properties = OrderedDict()

    # Merge properties from parent
    the_type = capability_definition._get_type(context)
    type_property_defintions = the_type._get_properties(context)
    merge_raw_parameter_definitions(context, presentation, raw_properties, type_property_defintions,
                                    'properties')

    # Merge our properties (might override definitions in parent)
    merge_raw_parameter_definitions(context, presentation, raw_properties,
                                    capability_definition.properties, 'properties')

    if raw_properties:
        capability_definition._raw['properties'] = raw_properties

    # Override valid_source_types
    if capability_definition._raw.get('valid_source_types') is None:
        valid_source_types = the_type._get_valid_source_types(context)
        if valid_source_types is not None:
            capability_definition._raw['valid_source_types'] = \
                deepcopy_with_locators(valid_source_types)
