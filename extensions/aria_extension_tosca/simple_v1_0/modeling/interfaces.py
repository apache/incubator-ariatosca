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
from aria.parser.presentation import get_locator
from aria.parser.validation import Issue

from .properties import (coerce_property_value, convert_property_definitions_to_values)

#
# InterfaceType
#

def get_inherited_operations(context, presentation):
    """
    Returns our operation definitions added on top of those of our parent, if we have one
    (recursively).

    Allows overriding all aspects of parent operations except input data types.
    """

    # Get operations from parent
    parent = presentation._get_parent(context)
    operations = get_inherited_operations(context, parent) if parent is not None else OrderedDict()

    # Add/merge our operations
    our_operations = presentation.operations # OperationDefinition
    merge_operation_definitions(context, operations, our_operations, presentation._name,
                                presentation, 'type')

    for operation in operations.itervalues():
        operation._reset_method_cache()

    return operations

#
# InterfaceDefinition
#

def get_and_override_input_definitions_from_type(context, presentation):
    """
    Returns our input definitions added on top of those of the interface type, if specified.

    Allows overriding all aspects of parent interface type inputs except data types.
    """

    inputs = OrderedDict()

    # Get inputs from type
    the_type = presentation._get_type(context) # IntefaceType
    type_inputs = the_type._get_inputs(context) if the_type is not None else None
    if type_inputs:
        for input_name, type_input in type_inputs.iteritems():
            inputs[input_name] = type_input._clone(presentation)

    # Add/merge our inputs
    our_inputs = presentation.inputs # PropertyDefinition
    if our_inputs:
        merge_input_definitions(context, inputs, our_inputs, presentation._name, None, presentation,
                                'definition')

    return inputs

def get_and_override_operation_definitions_from_type(context, presentation):
    """
    Returns our operation definitions added on top of those of the interface type, if specified.

    Allows overriding all aspects of parent interface type inputs except data types.
    """

    operations = OrderedDict()

    # Get operations from type
    the_type = presentation._get_type(context) # InterfaceType
    type_operations = the_type._get_operations(context) if the_type is not None else None
    if type_operations:
        for operations_name, type_operation in type_operations.iteritems():
            operations[operations_name] = type_operation._clone(presentation)

    # Add/merge our operations
    our_operations = presentation.operations # OperationDefinition
    merge_operation_definitions(context, operations, our_operations, presentation._name,
                                presentation, 'definition')

    return operations

#
# NodeType, RelationshipType, GroupType
#

def get_inherited_interface_definitions(context, presentation, type_name, for_presentation=None):
    """
    Returns our interface definitions added on top of those of our parent, if we have one
    (recursively).

    Allows overriding all aspects of parent interfaces except interface and operation input data
    types.
    """

    # Get interfaces from parent
    parent = presentation._get_parent(context)
    interfaces = get_inherited_interface_definitions(context, parent, type_name, presentation) \
        if parent is not None else OrderedDict()

    # Add/merge interfaces from their types
    merge_interface_definitions_from_their_types(context, interfaces, presentation)

    # Add/merge our interfaces
    our_interfaces = presentation.interfaces
    merge_interface_definitions(context, interfaces, our_interfaces, presentation,
                                for_presentation=for_presentation)

    return interfaces

#
# NodeTemplate, RelationshipTemplate, GroupTemplate
#

def get_template_interfaces(context, presentation, type_name):
    """
    Returns the assigned interface_template values while making sure they are defined in the type.
    This includes the interfaces themselves, their operations, and inputs for interfaces and
    operations.

    Interface and operation inputs' default values, if available, will be used if we did not assign
    them.

    Makes sure that required inputs indeed end up with a value.

    This code is especially complex due to the many levels of nesting involved.
    """

    template_interfaces = OrderedDict()

    the_type = presentation._get_type(context) # NodeType, RelationshipType, GroupType
    # InterfaceDefinition (or InterfaceAssignment in the case of RelationshipTemplate):
    interface_definitions = the_type._get_interfaces(context) if the_type is not None else None

    # Copy over interfaces from the type (will initialize inputs with default values)
    if interface_definitions is not None:
        for interface_name, interface_definition in interface_definitions.iteritems():
            # Note that in the case of a RelationshipTemplate, we will already have the values as
            # InterfaceAssignment. It will not be converted, just cloned.
            template_interfaces[interface_name] = \
                convert_interface_definition_from_type_to_template(context, interface_definition,
                                                                   presentation)

    # Fill in our interfaces
    our_interface_assignments = presentation.interfaces
    if our_interface_assignments:
        # InterfaceAssignment:
        for interface_name, our_interface_assignment in our_interface_assignments.iteritems():
            if interface_name in template_interfaces:
                interface_assignment = template_interfaces[interface_name] # InterfaceAssignment
                # InterfaceDefinition (or InterfaceAssignment in the case of RelationshipTemplate):
                interface_definition = interface_definitions[interface_name]
                merge_interface(context, presentation, interface_assignment,
                                our_interface_assignment, interface_definition, interface_name)
            else:
                context.validation.report(
                    'interface definition "%s" not declared at %s "%s" in "%s"'
                    % (interface_name, type_name, presentation.type, presentation._fullname),
                    locator=our_interface_assignment._locator, level=Issue.BETWEEN_TYPES)

    # Check that there are no required inputs that we haven't assigned
    for interface_name, interface_template in template_interfaces.iteritems():
        if interface_name in interface_definitions:
            # InterfaceDefinition (or InterfaceAssignment in the case of RelationshipTemplate):
            interface_definition = interface_definitions[interface_name]
            our_interface_assignment = our_interface_assignments.get(interface_name) \
                if our_interface_assignments is not None else None
            validate_required_inputs(context, presentation, interface_template,
                                     interface_definition, our_interface_assignment, interface_name)

    return template_interfaces

#
# Utils
#

def convert_interface_definition_from_type_to_template(context, presentation, container):
    from ..assignments import InterfaceAssignment

    if isinstance(presentation, InterfaceAssignment):
        # Nothing to convert, so just clone
        return presentation._clone(container)

    raw = convert_interface_definition_from_type_to_raw_template(context, presentation)
    return InterfaceAssignment(name=presentation._name, raw=raw, container=container)

def convert_interface_definition_from_type_to_raw_template(context, presentation): # pylint: disable=invalid-name
    raw = OrderedDict()

    # Copy default values for inputs
    inputs = presentation._get_inputs(context)
    if inputs is not None:
        raw['inputs'] = convert_property_definitions_to_values(context, inputs)

    # Copy operations
    operations = presentation._get_operations(context)
    if operations:
        for operation_name, operation in operations.iteritems():
            raw[operation_name] = OrderedDict()
            description = operation.description
            if description is not None:
                raw[operation_name]['description'] = deepcopy_with_locators(description._raw)
            implementation = operation.implementation
            if implementation is not None:
                raw[operation_name]['implementation'] = deepcopy_with_locators(implementation._raw)
            inputs = operation.inputs
            if inputs is not None:
                raw[operation_name]['inputs'] = convert_property_definitions_to_values(context,
                                                                                       inputs)

    return raw

def convert_requirement_interface_definitions_from_type_to_raw_template(context, raw_requirement, # pylint: disable=invalid-name
                                                                        interface_definitions):
    if not interface_definitions:
        return
    if 'interfaces' not in raw_requirement:
        raw_requirement['interfaces'] = OrderedDict()
    for interface_name, interface_definition in interface_definitions.iteritems():
        raw_interface = convert_interface_definition_from_type_to_raw_template(context,
                                                                               interface_definition)
        if interface_name in raw_requirement['interfaces']:
            merge(raw_requirement['interfaces'][interface_name], raw_interface)
        else:
            raw_requirement['interfaces'][interface_name] = raw_interface

def merge_interface(context, presentation, interface_assignment, our_interface_assignment,
                    interface_definition, interface_name):
    # Assign/merge interface inputs
    assign_raw_inputs(context, interface_assignment._raw, our_interface_assignment.inputs,
                      interface_definition._get_inputs(context), interface_name, None, presentation)

    # Assign operation implementations and inputs
    our_operation_templates = our_interface_assignment.operations # OperationAssignment
    # OperationDefinition or OperationAssignment:
    operation_definitions = interface_definition._get_operations(context) \
        if hasattr(interface_definition, '_get_operations') else interface_definition.operations
    if our_operation_templates:
        # OperationAssignment:
        for operation_name, our_operation_template in our_operation_templates.iteritems():
            operation_definition = operation_definitions.get(operation_name) # OperationDefinition

            our_input_assignments = our_operation_template.inputs
            our_implementation = our_operation_template.implementation

            if operation_definition is None:
                context.validation.report(
                    'interface definition "%s" refers to an unknown operation "%s" in "%s"'
                    % (interface_name, operation_name, presentation._fullname),
                    locator=our_operation_template._locator, level=Issue.BETWEEN_TYPES)

            if (our_input_assignments is not None) or (our_implementation is not None):
                # Make sure we have the dict
                if (operation_name not in interface_assignment._raw) \
                    or (interface_assignment._raw[operation_name] is None):
                    interface_assignment._raw[operation_name] = OrderedDict()

            if our_implementation is not None:
                interface_assignment._raw[operation_name]['implementation'] = \
                    deepcopy_with_locators(our_implementation._raw)

            # Assign/merge operation inputs
            input_definitions = operation_definition.inputs \
                if operation_definition is not None else None
            assign_raw_inputs(context, interface_assignment._raw[operation_name],
                              our_input_assignments, input_definitions, interface_name,
                              operation_name, presentation)

def merge_raw_input_definition(context, the_raw_input, our_input, interface_name, operation_name,
                               presentation, type_name):
    # Check if we changed the type
    # TODO: allow a sub-type?
    input_type1 = the_raw_input.get('type')
    input_type2 = our_input.type
    if input_type1 != input_type2:
        if operation_name is not None:
            context.validation.report(
                'interface %s "%s" changes operation input "%s.%s" type from "%s" to "%s" in "%s"'
                % (type_name, interface_name, operation_name, our_input._name, input_type1,
                   input_type2, presentation._fullname),
                locator=input_type2._locator, level=Issue.BETWEEN_TYPES)
        else:
            context.validation.report(
                'interface %s "%s" changes input "%s" type from "%s" to "%s" in "%s"'
                % (type_name, interface_name, our_input._name, input_type1, input_type2,
                   presentation._fullname),
                locator=input_type2._locator, level=Issue.BETWEEN_TYPES)

    # Merge
    merge(the_raw_input, our_input._raw)

def merge_input_definitions(context, inputs, our_inputs, interface_name, operation_name,
                            presentation, type_name):
    for input_name, our_input in our_inputs.iteritems():
        if input_name in inputs:
            merge_raw_input_definition(context, inputs[input_name]._raw, our_input, interface_name,
                                       operation_name, presentation, type_name)
        else:
            inputs[input_name] = our_input._clone(presentation)

def merge_raw_input_definitions(context, raw_inputs, our_inputs, interface_name, operation_name,
                                presentation, type_name):
    for input_name, our_input in our_inputs.iteritems():
        if input_name in raw_inputs:
            merge_raw_input_definition(context, raw_inputs[input_name], our_input, interface_name,
                                       operation_name, presentation, type_name)
        else:
            raw_inputs[input_name] = deepcopy_with_locators(our_input._raw)

def merge_raw_operation_definition(context, raw_operation, our_operation, interface_name,
                                   presentation, type_name):
    if not isinstance(our_operation._raw, dict):
        # Convert short form to long form
        raw_operation['implementation'] = deepcopy_with_locators(our_operation._raw)
        return

    # Add/merge inputs
    our_operation_inputs = our_operation.inputs
    if our_operation_inputs:
        # Make sure we have the dict
        if ('inputs' not in raw_operation) or (raw_operation.get('inputs') is None):
            raw_operation['inputs'] = OrderedDict()

        merge_raw_input_definitions(context, raw_operation['inputs'], our_operation_inputs,
                                    interface_name, our_operation._name, presentation, type_name)

    # Override the description
    if our_operation._raw.get('description') is not None:
        raw_operation['description'] = deepcopy_with_locators(our_operation._raw['description'])

    # Add/merge implementation
    if our_operation._raw.get('implementation') is not None:
        if raw_operation.get('implementation') is not None:
            merge(raw_operation['implementation'],
                  deepcopy_with_locators(our_operation._raw['implementation']))
        else:
            raw_operation['implementation'] = \
                deepcopy_with_locators(our_operation._raw['implementation'])

def merge_operation_definitions(context, operations, our_operations, interface_name, presentation,
                                type_name):
    if not our_operations:
        return
    for operation_name, our_operation in our_operations.iteritems():
        if operation_name in operations:
            merge_raw_operation_definition(context, operations[operation_name]._raw, our_operation,
                                           interface_name, presentation, type_name)
        else:
            operations[operation_name] = our_operation._clone(presentation)

def merge_raw_operation_definitions(context, raw_operations, our_operations, interface_name,
                                    presentation, type_name):
    for operation_name, our_operation in our_operations.iteritems():
        if operation_name in raw_operations:
            raw_operation = raw_operations[operation_name]
            if isinstance(raw_operation, basestring):
                # Convert short form to long form
                raw_operations[operation_name] = OrderedDict((('implementation', raw_operation),))
                raw_operation = raw_operations[operation_name]
            merge_raw_operation_definition(context, raw_operation, our_operation, interface_name,
                                           presentation, type_name)
        else:
            raw_operations[operation_name] = deepcopy_with_locators(our_operation._raw)

# From either an InterfaceType or an InterfaceDefinition:
def merge_interface_definition(context, interface, our_source, presentation, type_name):
    if hasattr(our_source, 'type'):
        # Check if we changed the interface type
        input_type1 = interface.type
        input_type2 = our_source.type
        if (input_type1 is not None) and (input_type2 is not None) and (input_type1 != input_type2):
            context.validation.report(
                'interface definition "%s" changes type from "%s" to "%s" in "%s"'
                % (interface._name, input_type1, input_type2, presentation._fullname),
                locator=input_type2._locator, level=Issue.BETWEEN_TYPES)

    # Add/merge inputs
    our_interface_inputs = our_source._get_inputs(context) \
        if hasattr(our_source, '_get_inputs') else our_source.inputs
    if our_interface_inputs:
        # Make sure we have the dict
        if ('inputs' not in interface._raw) or (interface._raw.get('inputs') is None):
            interface._raw['inputs'] = OrderedDict()

        merge_raw_input_definitions(context, interface._raw['inputs'], our_interface_inputs,
                                    our_source._name, None, presentation, type_name)

    # Add/merge operations
    our_operations = our_source._get_operations(context) \
        if hasattr(our_source, '_get_operations') else our_source.operations
    if our_operations is not None:
        merge_raw_operation_definitions(context, interface._raw, our_operations, our_source._name,
                                        presentation, type_name)

def merge_interface_definitions(context, interfaces, our_interfaces, presentation,
                                for_presentation=None):
    if not our_interfaces:
        return
    for name, our_interface in our_interfaces.iteritems():
        if name in interfaces:
            merge_interface_definition(context, interfaces[name], our_interface, presentation,
                                       'definition')
        else:
            interfaces[name] = our_interface._clone(for_presentation)

def merge_interface_definitions_from_their_types(context, interfaces, presentation):
    for interface in interfaces.itervalues():
        the_type = interface._get_type(context) # InterfaceType
        if the_type is not None:
            merge_interface_definition(context, interface, the_type, presentation, 'type')

def assign_raw_inputs(context, values, assignments, definitions, interface_name, operation_name,
                      presentation):
    if not assignments:
        return

    # Make sure we have the dict
    if ('inputs' not in values) or (values['inputs'] is None):
        values['inputs'] = OrderedDict()

    # Assign inputs
    for input_name, assignment in assignments.iteritems():
        if (definitions is not None) and (input_name not in definitions):
            if operation_name is not None:
                context.validation.report(
                    'interface definition "%s" assigns a value to an unknown operation input'
                    ' "%s.%s" in "%s"'
                    % (interface_name, operation_name, input_name, presentation._fullname),
                    locator=assignment._locator, level=Issue.BETWEEN_TYPES)
            else:
                context.validation.report(
                    'interface definition "%s" assigns a value to an unknown input "%s" in "%s"'
                    % (interface_name, input_name, presentation._fullname),
                    locator=assignment._locator, level=Issue.BETWEEN_TYPES)

        definition = definitions.get(input_name) if definitions is not None else None

        # Note: default value has already been assigned

        # Coerce value
        values['inputs'][input_name] = coerce_property_value(context, assignment, definition,
                                                             assignment.value)

def validate_required_inputs(context, presentation, assignment, definition, original_assignment,
                             interface_name, operation_name=None):
    input_definitions = definition.inputs
    if input_definitions:
        for input_name, input_definition in input_definitions.iteritems():
            if input_definition.required:
                prop = assignment.inputs.get(input_name) \
                    if ((assignment is not None) and (assignment.inputs is not None)) else None
                value = prop.value if prop is not None else None
                value = value.value if value is not None else None
                if value is None:
                    if operation_name is not None:
                        context.validation.report(
                            'interface definition "%s" does not assign a value to a required'
                            ' operation input "%s.%s" in "%s"'
                            % (interface_name, operation_name, input_name, presentation._fullname),
                            locator=get_locator(original_assignment, presentation._locator),
                            level=Issue.BETWEEN_TYPES)
                    else:
                        context.validation.report(
                            'interface definition "%s" does not assign a value to a required input'
                            ' "%s" in "%s"'
                            % (interface_name, input_name, presentation._fullname),
                            locator=get_locator(original_assignment, presentation._locator),
                            level=Issue.BETWEEN_TYPES)

    if operation_name is not None:
        return

    assignment_operations = assignment.operations
    operation_definitions = definition._get_operations(context)
    if operation_definitions:
        for operation_name, operation_definition in operation_definitions.iteritems():
            assignment_operation = assignment_operations.get(operation_name) \
                if assignment_operations is not None else None
            original_operation = \
                original_assignment.operations.get(operation_name, original_assignment) \
                if (original_assignment is not None) \
                and (original_assignment.operations is not None) \
                else original_assignment
            validate_required_inputs(context, presentation, assignment_operation,
                                     operation_definition, original_operation, interface_name,
                                     operation_name)
