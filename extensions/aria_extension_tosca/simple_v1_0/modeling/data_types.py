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
from collections import OrderedDict

from aria.parser import dsl_specification
from aria.parser.presentation import (get_locator, validate_primitive)
from aria.parser.utils import (import_fullname, full_type_name, safe_repr)
from aria.parser.validation import Issue

from ..functions import get_function
from ..presentation.types import get_type_by_full_or_shorthand_name

#
# DataType
#

def get_inherited_constraints(context, presentation):
    """
    If we don't have constraints, will return our parent's constraints (if we have one),
    recursively.

    Implication: if we define even one constraint, the parent's constraints will not be inherited.
    """

    constraints = presentation.constraints

    if constraints is None:
        # If we don't have any, use our parent's
        parent = presentation._get_parent(context)
        parent_constraints = get_inherited_constraints(context, parent) \
            if parent is not None else None
        if parent_constraints is not None:
            constraints = parent_constraints

    return constraints

def coerce_data_type_value(context, presentation, data_type, entry_schema, constraints, value, # pylint: disable=unused-argument
                           aspect):
    """
    Handles the :code:`_coerce_data()` hook for complex data types.

    There are two kinds of handling:

    1. If we have a primitive type as our great ancestor, then we do primitive type coersion, and
       just check for constraints.

    2. Otherwise, for normal complex data types we return the assigned property values while making
       sure they are defined in our type. The property definition's default value, if available,
       will be used if we did not assign it. We also make sure that required definitions indeed end
       up with a value.
    """

    primitive_type = data_type._get_primitive_ancestor(context)
    if primitive_type is not None:
        # Must be coercible to primitive ancestor
        value = coerce_to_primitive(context, presentation, primitive_type, constraints, value,
                                    aspect)
    else:
        definitions = data_type._get_properties(context)
        if isinstance(value, dict):
            temp = OrderedDict()

            # Fill in our values, but make sure they are defined
            for name, v in value.iteritems():
                if name in definitions:
                    definition = definitions[name]
                    definition_type = definition._get_type(context)
                    definition_entry_schema = definition.entry_schema
                    definition_constraints = definition._get_constraints(context)
                    temp[name] = coerce_value(context, presentation, definition_type,
                                              definition_entry_schema, definition_constraints, v,
                                              aspect)
                else:
                    context.validation.report(
                        'assignment to undefined property "%s" in type "%s" in "%s"'
                        % (name, data_type._fullname, presentation._fullname),
                        locator=get_locator(v, value, presentation), level=Issue.BETWEEN_TYPES)

            # Fill in defaults from the definitions, and check if required definitions have not been
            # assigned
            for name, definition in definitions.iteritems():
                if (temp.get(name) is None) and hasattr(definition, 'default') \
                    and (definition.default is not None):
                    definition_type = definition._get_type(context)
                    definition_entry_schema = definition.entry_schema
                    definition_constraints = definition._get_constraints(context)
                    temp[name] = coerce_value(context, presentation, definition_type,
                                              definition_entry_schema, definition_constraints,
                                              definition.default, 'default')

                if getattr(definition, 'required', False) and (temp.get(name) is None):
                    context.validation.report(
                        'required property "%s" in type "%s" is not assigned a value in "%s"'
                        % (name, data_type._fullname, presentation._fullname),
                        locator=presentation._get_child_locator('definitions'),
                        level=Issue.BETWEEN_TYPES)

            value = temp
        elif value is not None:
            context.validation.report('value of type "%s" is not a dict in "%s"'
                                      % (data_type._fullname, presentation._fullname),
                                      locator=get_locator(value, presentation),
                                      level=Issue.BETWEEN_TYPES)
            value = None

    return value

def validate_data_type_name(context, presentation):
    """
    Makes sure the complex data type's name is not that of a built-in type.
    """

    name = presentation._name
    if get_primitive_data_type(name) is not None:
        context.validation.report('data type name is that of a built-in type: %s'
                                  % safe_repr(name),
                                  locator=presentation._locator, level=Issue.BETWEEN_TYPES)

#
# PropertyDefinition, AttributeDefinition, EntrySchema, DataType
#

def get_data_type(context, presentation, field_name, allow_none=False):
    """
    Returns the type, whether it's a complex data type (a DataType instance) or a primitive (a
    Python primitive type class).

    If the type is not specified, defaults to :class:`str`, per note in section 3.2.1.1 of the
    `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #_Toc379455072>`__
    """

    type_name = getattr(presentation, field_name)

    if type_name is None:
        if allow_none:
            return None
        else:
            return str

    # Make sure not derived from self
    if type_name == presentation._name:
        return None

    # Avoid circular definitions
    container_data_type = get_container_data_type(presentation)
    if (container_data_type is not None) and (container_data_type._name == type_name):
        return None

    # Try complex data type
    data_type = get_type_by_full_or_shorthand_name(context, type_name, 'data_types')
    if data_type is not None:
        return data_type

    # Try primitive data type
    return get_primitive_data_type(type_name)

#
# PropertyDefinition, EntrySchema
#

def get_property_constraints(context, presentation):
    """
    If we don't have constraints, will return our type's constraints (if we have one), recursively.

    Implication: if we define even one constraint, the type's constraints will not be inherited.
    """

    constraints = presentation.constraints

    if constraints is None:
        # If we don't have any, use our type's
        the_type = presentation._get_type(context)
        type_constraints = the_type._get_constraints(context) \
            if hasattr(the_type, '_get_constraints') else None
        if type_constraints is not None:
            constraints = type_constraints

    return constraints

#
# ConstraintClause
#

def apply_constraint_to_value(context, presentation, constraint_clause, value): # pylint: disable=too-many-statements,too-many-return-statements,too-many-branches
    """
    Returns false if the value does not conform to the constraint.
    """

    constraint_key = constraint_clause._raw.keys()[0]
    the_type = constraint_clause._get_type(context)
    # PropertyAssignment does not have this:
    entry_schema = getattr(presentation, 'entry_schema', None)

    def coerce_constraint(constraint):
        return coerce_value(context, presentation, the_type, entry_schema, None, constraint,
                            constraint_key)

    def report(message, constraint):
        context.validation.report('value %s %s per constraint in "%s": %s'
                                  % (message, safe_repr(constraint),
                                     presentation._name or presentation._container._name,
                                     safe_repr(value)),
                                  locator=presentation._locator, level=Issue.BETWEEN_FIELDS)

    if constraint_key == 'equal':
        constraint = coerce_constraint(constraint_clause.equal)
        if value != constraint:
            report('is not equal to', constraint)
            return False

    elif constraint_key == 'greater_than':
        constraint = coerce_constraint(constraint_clause.greater_than)
        if value <= constraint:
            report('is not greater than', constraint)
            return False

    elif constraint_key == 'greater_or_equal':
        constraint = coerce_constraint(constraint_clause.greater_or_equal)
        if value < constraint:
            report('is not greater than or equal to', constraint)
            return False

    elif constraint_key == 'less_than':
        constraint = coerce_constraint(constraint_clause.less_than)
        if value >= constraint:
            report('is not less than', constraint)
            return False

    elif constraint_key == 'less_or_equal':
        constraint = coerce_constraint(constraint_clause.less_or_equal)
        if value > constraint:
            report('is not less than or equal to', constraint)
            return False

    elif constraint_key == 'in_range':
        lower, upper = constraint_clause.in_range
        lower, upper = coerce_constraint(lower), coerce_constraint(upper)
        if value < lower:
            report('is not greater than or equal to lower bound', lower)
            return False
        if (upper != 'UNBOUNDED') and (value > upper):
            report('is not lesser than or equal to upper bound', upper)
            return False

    elif constraint_key == 'valid_values':
        constraint = tuple(coerce_constraint(v) for v in constraint_clause.valid_values)
        if value not in constraint:
            report('is not one of', constraint)
            return False

    elif constraint_key == 'length':
        constraint = constraint_clause.length
        try:
            if len(value) != constraint:
                report('is not of length', constraint)
                return False
        except TypeError:
            pass # should be validated elsewhere

    elif constraint_key == 'min_length':
        constraint = constraint_clause.min_length
        try:
            if len(value) < constraint:
                report('has a length lesser than', constraint)
                return False
        except TypeError:
            pass # should be validated elsewhere

    elif constraint_key == 'max_length':
        constraint = constraint_clause.max_length
        try:
            if len(value) > constraint:
                report('has a length greater than', constraint)
                return False
        except TypeError:
            pass # should be validated elsewhere

    elif constraint_key == 'pattern':
        constraint = constraint_clause.pattern
        try:
            # Note: the TOSCA 1.0 spec does not specify the regular expression grammar, so we will
            # just use Python's
            if re.match(constraint, str(value)) is None:
                report('does not match regular expression', constraint)
                return False
        except re.error:
            pass # should be validated elsewhere

    return True

#
# Repository
#

def get_data_type_value(context, presentation, field_name, type_name):
    the_type = get_type_by_full_or_shorthand_name(context, type_name, 'data_types')
    if the_type is not None:
        value = getattr(presentation, field_name)
        if value is not None:
            return coerce_data_type_value(context, presentation, the_type, None, None, value, None)
    else:
        context.validation.report('field "%s" in "%s" refers to unknown data type "%s"'
                                  % (field_name, presentation._fullname, type_name),
                                  locator=presentation._locator, level=Issue.BETWEEN_TYPES)
    return None

#
# Utils
#

PRIMITIVE_DATA_TYPES = {
    # YAML 1.2:
    'tag:yaml.org,2002:str': str,
    'tag:yaml.org,2002:integer': int,
    'tag:yaml.org,2002:float': float,
    'tag:yaml.org,2002:bool': bool,
    'tag:yaml.org,2002:null': None.__class__,

    # TOSCA aliases:
    'string': str,
    'integer': int,
    'float': float,
    'boolean': bool,
    'null': None.__class__}

@dsl_specification('3.2.1', 'tosca-simple-1.0')
def get_primitive_data_type(type_name):
    """
    Many of the types we use in this profile are built-in types from the YAML 1.2 specification
    (i.e., those identified by the "tag:yaml.org,2002" version tag) [YAML-1.2].

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #_Toc373867862>`__
    """

    return PRIMITIVE_DATA_TYPES.get(type_name)

def get_data_type_name(the_type):
    """
    Returns the name of the type, whether it's a DataType, a primitive type, or another class.
    """

    return the_type._name if hasattr(the_type, '_name') else full_type_name(the_type)

def coerce_value(context, presentation, the_type, entry_schema, constraints, value, aspect=None): # pylint: disable=too-many-return-statements
    """
    Returns the value after it's coerced to its type, reporting validation errors if it cannot be
    coerced.

    Supports both complex data types and primitives.

    Data types can use the :code:`coerce_value` extension to hook their own specialized function.
    If the extension is present, we will delegate to that hook.
    """

    is_function, func = get_function(context, presentation, value)
    if is_function:
        return func

    if the_type is None:
        return value

    if the_type == None.__class__:
        if value is not None:
            context.validation.report('field "%s" is of type "null" but has a non-null value: %s'
                                      % (presentation._name, safe_repr(value)),
                                      locator=presentation._locator, level=Issue.BETWEEN_FIELDS)
            return None

    # Delegate to 'coerce_value' extension
    if hasattr(the_type, '_get_extension'):
        coerce_value_fn_name = the_type._get_extension('coerce_value')
        if coerce_value_fn_name is not None:
            if value is None:
                return None
            coerce_value_fn = import_fullname(coerce_value_fn_name)
            return coerce_value_fn(context, presentation, the_type, entry_schema, constraints,
                                   value, aspect)

    if hasattr(the_type, '_coerce_value'):
        # Delegate to '_coerce_value' (likely a DataType instance)
        return the_type._coerce_value(context, presentation, entry_schema, constraints, value,
                                      aspect)

    # Coerce to primitive type
    return coerce_to_primitive(context, presentation, the_type, constraints, value, aspect)

def coerce_to_primitive(context, presentation, primitive_type, constraints, value, aspect=None):
    """
    Returns the value after it's coerced to a primitive type, translating exceptions to validation
    errors if it cannot be coerced.
    """

    if value is None:
        return None

    try:
        # Coerce
        value = validate_primitive(value, primitive_type,
                                   context.validation.allow_primitive_coersion)

        # Check constraints
        apply_constraints_to_value(context, presentation, constraints, value)
    except ValueError as e:
        report_issue_for_bad_format(context, presentation, primitive_type, value, aspect, e)
        value = None
    except TypeError as e:
        report_issue_for_bad_format(context, presentation, primitive_type, value, aspect, e)
        value = None

    return value

def coerce_to_data_type_class(context, presentation, cls, entry_schema, constraints, value,
                              aspect=None):
    """
    Returns the value after it's coerced to a data type class, reporting validation errors if it
    cannot be coerced. Constraints will be applied after coersion.

    Will either call a :code:`_create` static function in the class, or instantiate it using a
    constructor if :code:`_create` is not available.

    This will usually be called by a :code:`coerce_value` extension hook in a :class:`DataType`.
    """

    try:
        if hasattr(cls, '_create'):
            # Instantiate using creator function
            value = cls._create(context, presentation, entry_schema, constraints, value, aspect)
        else:
            # Normal instantiation
            value = cls(entry_schema, constraints, value, aspect)
    except ValueError as e:
        report_issue_for_bad_format(context, presentation, cls, value, aspect, e)
        value = None

    # Check constraints
    value = apply_constraints_to_value(context, presentation, constraints, value)

    return value

def apply_constraints_to_value(context, presentation, constraints, value):
    """
    Applies all constraints to the value. If the value conforms, returns the value. If it does not
    conform, returns None.
    """

    if (value is not None) and (constraints is not None):
        valid = True
        for constraint in constraints:
            if not constraint._apply_to_value(context, presentation, value):
                valid = False
        if not valid:
            value = None
    return value

def get_container_data_type(presentation):
    if presentation is None:
        return None
    if type(presentation).__name__ == 'DataType':
        return presentation
    return get_container_data_type(presentation._container)

def report_issue_for_bad_format(context, presentation, the_type, value, aspect, e):
    if aspect == 'default':
        aspect = '"default" value'
    elif aspect is not None:
        aspect = '"%s" aspect' % aspect

    if aspect is not None:
        context.validation.report('%s for field "%s" is not a valid "%s": %s'
                                  % (aspect, presentation._name or presentation._container._name,
                                     get_data_type_name(the_type), safe_repr(value)),
                                  locator=presentation._locator, level=Issue.BETWEEN_FIELDS,
                                  exception=e)
    else:
        context.validation.report('field "%s" is not a valid "%s": %s'
                                  % (presentation._name or presentation._container._name,
                                     get_data_type_name(the_type), safe_repr(value)),
                                  locator=presentation._locator, level=Issue.BETWEEN_FIELDS,
                                  exception=e)
