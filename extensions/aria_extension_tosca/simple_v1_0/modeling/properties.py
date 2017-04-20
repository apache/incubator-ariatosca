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

from aria.utils.collections import merge, deepcopy_with_locators, OrderedDict
from aria.parser.presentation import Value
from aria.parser.validation import Issue

from .data_types import coerce_value

#
# ArtifactType, DataType, CapabilityType, RelationshipType, NodeType, GroupType, PolicyType
#

# Works on properties, parameters, inputs, and attributes
def get_inherited_property_definitions(context, presentation, field_name, for_presentation=None):
    """
    Returns our property definitions added on top of those of our parent, if we have one
    (recursively).

    Allows overriding all aspects of parent properties except data type.
    """

    # Get definitions from parent
    # If we inherit from a primitive, it does not have a parent:
    parent = presentation._get_parent(context) if hasattr(presentation, '_get_parent') else None
    definitions = get_inherited_property_definitions(context, parent, field_name,
                                                     for_presentation=presentation) \
                                                     if parent is not None else OrderedDict()

    # Add/merge our definitions
    # If we inherit from a primitive, it does not have our field
    our_definitions = getattr(presentation, field_name, None)
    if our_definitions:
        our_definitions_clone = OrderedDict()
        for name, our_definition in our_definitions.iteritems():
            our_definitions_clone[name] = our_definition._clone(for_presentation)
        our_definitions = our_definitions_clone
        merge_property_definitions(context, presentation, definitions, our_definitions, field_name)

    for definition in definitions.itervalues():
        definition._reset_method_cache()

    return definitions

#
# NodeTemplate, RelationshipTemplate, GroupTemplate, PolicyTemplate
#

def get_assigned_and_defined_property_values(context, presentation, field_name='property',
                                             field_name_plural='properties'):
    """
    Returns the assigned property values while making sure they are defined in our type.

    The property definition's default value, if available, will be used if we did not assign it.

    Makes sure that required properties indeed end up with a value.
    """

    values = OrderedDict()

    the_type = presentation._get_type(context)
    assignments = getattr(presentation, field_name_plural)
    get_fn_name = '_get_{0}'.format(field_name_plural)
    definitions = getattr(the_type, get_fn_name)(context) if the_type is not None else None

    # Fill in our assignments, but make sure they are defined
    if assignments:
        for name, value in assignments.iteritems():
            if (definitions is not None) and (name in definitions):
                definition = definitions[name]
                values[name] = coerce_property_value(context, value, definition, value.value)
            else:
                context.validation.report('assignment to undefined {0} "{1}" in "{2}"'
                                          .format(field_name, name, presentation._fullname),
                                          locator=value._locator, level=Issue.BETWEEN_TYPES)

    # Fill in defaults from the definitions
    if definitions:
        for name, definition in definitions.iteritems():
            if values.get(name) is None:
                values[name] = coerce_property_value(context, presentation, definition,
                                                     definition.default)

    validate_required_values(context, presentation, values, definitions)

    return values

#
# TopologyTemplate
#

def get_parameter_values(context, presentation, field_name):
    values = OrderedDict()

    parameters = getattr(presentation, field_name)

    # Fill in defaults and values
    if parameters:
        for name, parameter in parameters.iteritems():
            if values.get(name) is None:
                if hasattr(parameter, 'value') and (parameter.value is not None):
                    # For parameters only:
                    values[name] = coerce_property_value(context, presentation, parameter,
                                                         parameter.value)
                else:
                    default = parameter.default if hasattr(parameter, 'default') else None
                    values[name] = coerce_property_value(context, presentation, parameter, default)

    return values

#
# Utils
#

def validate_required_values(context, presentation, values, definitions):
    """
    Check if required properties have not been assigned.
    """

    if not definitions:
        return
    for name, definition in definitions.iteritems():
        if getattr(definition, 'required', False) \
            and ((values is None) or (values.get(name) is None)):
            context.validation.report('required property "%s" is not assigned a value in "%s"'
                                      % (name, presentation._fullname),
                                      locator=presentation._get_child_locator('properties'),
                                      level=Issue.BETWEEN_TYPES)

def merge_raw_property_definition(context, presentation, raw_property_definition,
                                  our_property_definition, field_name, property_name):
    # Check if we changed the type
    # TODO: allow a sub-type?
    type1 = raw_property_definition.get('type')
    type2 = our_property_definition.type
    if type1 != type2:
        context.validation.report(
            'override changes type from "%s" to "%s" for property "%s" in "%s"'
            % (type1, type2, property_name, presentation._fullname),
            locator=presentation._get_child_locator(field_name, property_name),
            level=Issue.BETWEEN_TYPES)

    merge(raw_property_definition, our_property_definition._raw)

def merge_raw_property_definitions(context, presentation, raw_property_definitions,
                                   our_property_definitions, field_name):
    if not our_property_definitions:
        return
    for property_name, our_property_definition in our_property_definitions.iteritems():
        if property_name in raw_property_definitions:
            raw_property_definition = raw_property_definitions[property_name]
            merge_raw_property_definition(context, presentation, raw_property_definition,
                                          our_property_definition, field_name, property_name)
        else:
            raw_property_definitions[property_name] = \
                deepcopy_with_locators(our_property_definition._raw)

def merge_property_definitions(context, presentation, property_definitions,
                               our_property_definitions, field_name):
    if not our_property_definitions:
        return
    for property_name, our_property_definition in our_property_definitions.iteritems():
        if property_name in property_definitions:
            property_definition = property_definitions[property_name]
            merge_raw_property_definition(context, presentation, property_definition._raw,
                                          our_property_definition, field_name, property_name)
        else:
            property_definitions[property_name] = our_property_definition

# Works on properties, inputs, and parameters
def coerce_property_value(context, presentation, definition, value, aspect=None):
    the_type = definition._get_type(context) if definition is not None else None
    entry_schema = definition.entry_schema if definition is not None else None
    constraints = definition._get_constraints(context) \
        if ((definition is not None) and hasattr(definition, '_get_constraints')) else None
    value = coerce_value(context, presentation, the_type, entry_schema, constraints, value, aspect)
    if (the_type is not None) and hasattr(the_type, '_name'):
        type_name = the_type._name
    else:
        type_name = getattr(definition, 'type', None)
    description = getattr(definition, 'description', None)
    description = description.value if description is not None else None
    return Value(type_name, value, description)

def convert_property_definitions_to_values(context, definitions):
    values = OrderedDict()
    for name, definition in definitions.iteritems():
        default = definition.default
        values[name] = coerce_property_value(context, definition, definition, default)
    return values
