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

from aria.utils.formatting import safe_repr
from aria.parser import implements_specification
from aria.parser.presentation import (report_issue_for_unknown_type, derived_from_validator)
from aria.parser.validation import Issue

from ..modeling.data_types import (get_primitive_data_type, get_data_type_name, coerce_value,
                                   get_container_data_type)
from .types import (get_type_by_name, convert_name_to_full_type_name)



#
# NodeTemplate, RelationshipTemplate
#

@implements_specification('3.7.3.3', 'tosca-simple-1.0')
def copy_validator(template_type_name, templates_dict_name):
    """
    Makes sure that the field refers to an existing template defined in the root presenter.

    Use with the :func:`field_validator` decorator for the ``copy`` field in
    :class:`NodeTemplate` and :class:`RelationshipTemplate`.
    """

    def validator_fn(field, presentation, context):
        field.default_validate(presentation, context)

        # Make sure type exists
        value = getattr(presentation, field.name)
        if value is not None:
            copy = context.presentation.get_from_dict('service_template', 'topology_template',
                                                      templates_dict_name, value)
            if copy is None:
                report_issue_for_unknown_type(context, presentation, template_type_name, field.name)
            else:
                if copy.copy is not None:
                    context.validation.report(
                        u'"copy" field refers to a {0} that itself is a copy in "{1}": {2}'
                        .format(template_type_name, presentation._fullname, safe_repr(value)),
                        locator=presentation._locator, level=Issue.BETWEEN_TYPES)

    return validator_fn


#
# PropertyDefinition, AttributeDefinition, ParameterDefinition, EntrySchema
#

def data_type_validator(type_name='data type'):
    """
    Makes sure that the field refers to a valid data type, whether complex or primitive.

    Used with the :func:`field_validator` decorator for the ``type`` fields in
    :class:`PropertyDefinition`, :class:`AttributeDefinition`, :class:`ParameterDefinition`,
    and :class:`EntrySchema`.

    Extra behavior beyond validation: generated function returns true if field is a complex data
    type.
    """

    def validator(field, presentation, context):
        field.default_validate(presentation, context)

        value = getattr(presentation, field.name)
        if value is not None:
            # Test for circular definitions
            container_data_type = get_container_data_type(presentation)
            if (container_data_type is not None) and (container_data_type._name == value):
                context.validation.report(
                    u'type of property "{0}" creates a circular value hierarchy: {1}'
                    .format(presentation._fullname, safe_repr(value)),
                    locator=presentation._get_child_locator('type'), level=Issue.BETWEEN_TYPES)

            # Can be a complex data type
            if get_type_by_name(context, value, 'data_types') is not None:
                return True

            # Can be a primitive data type
            if get_primitive_data_type(value) is None:
                report_issue_for_unknown_type(context, presentation, type_name, field.name)

        return False

    return validator


#
# PropertyDefinition, AttributeDefinition
#

def entry_schema_validator(field, presentation, context):
    """
    According to whether the data type supports ``entry_schema`` (e.g., it is or inherits from
    list or map), make sure that we either have or don't have a valid data type value.

    Used with the :func:`field_validator` decorator for the ``entry_schema`` field in
    :class:`PropertyDefinition` and :class:`AttributeDefinition`.
    """

    field.default_validate(presentation, context)

    def type_uses_entry_schema(the_type):
        use_entry_schema = the_type._get_extension('use_entry_schema', False) \
            if hasattr(the_type, '_get_extension') else False
        if use_entry_schema:
            return True
        parent = the_type._get_parent(context) if hasattr(the_type, '_get_parent') else None
        if parent is None:
            return False
        return type_uses_entry_schema(parent)

    value = getattr(presentation, field.name)
    the_type = presentation._get_type(context)
    if the_type is None:
        return
    use_entry_schema = type_uses_entry_schema(the_type)

    if use_entry_schema:
        if value is None:
            context.validation.report(
                u'"entry_schema" does not have a value as required by data type "{0}" in "{1}"'
                .format(get_data_type_name(the_type), presentation._container._fullname),
                locator=presentation._locator, level=Issue.BETWEEN_TYPES)
    else:
        if value is not None:
            context.validation.report(
                u'"entry_schema" has a value but it is not used by data type "{0}" in "{1}"'
                .format(get_data_type_name(the_type), presentation._container._fullname),
                locator=presentation._locator, level=Issue.BETWEEN_TYPES)


def data_value_validator(field, presentation, context):
    """
    Makes sure that the field contains a valid value according to data type and constraints.

    Used with the :func:`field_validator` decorator for the ``default`` field in
    :class:`PropertyDefinition` and :class:`AttributeDefinition`.
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        the_type = presentation._get_type(context)
        entry_schema = presentation.entry_schema
        # AttributeDefinition does not have this:
        constraints = presentation._get_constraints(context) \
            if hasattr(presentation, '_get_constraints') else None
        coerce_value(context, presentation, the_type, entry_schema, constraints, value, field.name)


#
# DataType
#

_data_type_validator = data_type_validator()
_data_type_derived_from_validator = derived_from_validator(convert_name_to_full_type_name,
                                                           'data_types')


def data_type_derived_from_validator(field, presentation, context):
    """
    Makes sure that the field refers to a valid parent data type (complex or primitive).

    Used with the :func:`field_validator` decorator for the ``derived_from`` field in
    :class:`DataType`.
    """

    if _data_type_validator(field, presentation, context):
        # Validate derivation only if a complex data type (primitive types have no derivation
        # hierarchy)
        _data_type_derived_from_validator(field, presentation, context)


def data_type_constraints_validator(field, presentation, context):
    """
    Makes sure that we do not have constraints if we are a complex type (with no primitive
    ancestor).
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        if presentation._get_primitive_ancestor(context) is None:
            context.validation.report(
                u'data type "{0}" defines constraints but does not have a primitive ancestor'
                .format(presentation._fullname),
                locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_TYPES)


def data_type_properties_validator(field, presentation, context):
    """
    Makes sure that we do not have properties if we have a primitive ancestor.

    Used with the :func:`field_validator` decorator for the ``properties`` field in
    :class:`DataType`.
    """

    field.default_validate(presentation, context)

    values = getattr(presentation, field.name)
    if values is not None:
        if presentation._get_primitive_ancestor(context) is not None:
            context.validation.report(
                u'data type "{0}" defines properties even though it has a primitive ancestor'
                .format(presentation._fullname),
                locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_TYPES)


#
# ConstraintClause
#

def constraint_clause_field_validator(field, presentation, context):
    """
    Makes sure that field contains a valid value for the container type.

    Used with the :func:`field_validator` decorator for various field in :class:`ConstraintClause`.
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        the_type = presentation._get_type(context)
        constraints = the_type._get_constraints(context) \
            if hasattr(the_type, '_get_constraints') else None
        coerce_value(context, presentation, the_type, None, constraints, value, field.name)


def constraint_clause_in_range_validator(field, presentation, context):
    """
    Makes sure that the value is a list with exactly two elements, that both lower bound contains a
    valid value for the container type, and that the upper bound is either "UNBOUNDED" or a valid
    value for the container type.

    Used with the :func:`field_validator` decorator for the ``in_range`` field in
    :class:`ConstraintClause`.
    """

    field.default_validate(presentation, context)

    values = getattr(presentation, field.name)
    if isinstance(values, list):
        # Make sure list has exactly two elements
        if len(values) == 2:
            lower, upper = values
            the_type = presentation._get_type(context)

            # Lower bound must be coercible
            lower = coerce_value(context, presentation, the_type, None, None, lower, field.name)

            if upper != 'UNBOUNDED':
                # Upper bound be coercible
                upper = coerce_value(context, presentation, the_type, None, None, upper, field.name)

                # Second "in_range" value must be greater or equal than first
                if (lower is not None) and (upper is not None) and (lower >= upper):
                    context.validation.report(
                        u'upper bound of "in_range" constraint is not greater than the lower bound'
                        u' in "{0}": {1} <= {2}'
                        .format(presentation._container._fullname, safe_repr(lower),
                                safe_repr(upper)),
                        locator=presentation._locator, level=Issue.FIELD)
        else:
            context.validation.report(
                u'constraint "{0}" is not a list of exactly 2 elements in "{1}": {2}'
                .format(field.name, presentation._fullname, safe_repr(values)),
                locator=presentation._get_child_locator(field.name), level=Issue.FIELD)


def constraint_clause_valid_values_validator(field, presentation, context):
    """
    Makes sure that the value is a list of valid values for the container type.

    Used with the :func:`field_validator` decorator for the ``valid_values`` field in
    :class:`ConstraintClause`.
    """

    field.default_validate(presentation, context)

    values = getattr(presentation, field.name)
    if isinstance(values, list):
        the_type = presentation._get_type(context)
        for value in values:
            coerce_value(context, presentation, the_type, None, None, value, field.name)


def constraint_clause_pattern_validator(field, presentation, context):
    """
    Makes sure that the value is a valid regular expression.

    Used with the :func:`field_validator` decorator for the ``pattern`` field in
    :class:`ConstraintClause`.
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        try:
            # From TOSCA 1.0 3.5.2.1:
            #
            # "Note: Future drafts of this specification will detail the use of regular expressions
            # and reference an appropriate standardized grammar."
            #
            # So we will just use Python's.
            re.compile(value)
        except re.error as e:
            context.validation.report(
                u'constraint "{0}" is not a valid regular expression in "{1}": {2}'
                .format(field.name, presentation._fullname, safe_repr(value)),
                locator=presentation._get_child_locator(field.name), level=Issue.FIELD, exception=e)


#
# RequirementAssignment
#

def node_template_or_type_validator(field, presentation, context):
    """
    Makes sure that the field refers to either a node template or a node type.

    Used with the :func:`field_validator` decorator for the ``node`` field in
    :class:`RequirementAssignment`.
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        node, node_variant = presentation._get_node(context)
        if node_variant == 'node_template':
            node_template_validator(field, presentation, context, value, node)
        elif node_variant == 'node_type':
            node_type_validator(field, presentation, context, value, node)
        else:
            context.validation.report(
                '"%s" refers to a node type or node template that does not match the capability '
                'requirement in "%s"'
                % (presentation._name, presentation._container._fullname),
                locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_FIELDS)

def node_template_validator(field, presentation, context, node_value, node_obj):
    """
    Makes sure that the field refers to a node template.
    """
    the_node_templates = context.presentation.get('service_template', 'topology_template',\
                                                          'node_templates') or {}
    the_parent_capability_type_name = _get_requirement_in_type(context, presentation).\
                                      capability
    the_parent_node_type_name = _get_requirement_in_type(context, presentation).node
    the_nodetype_obj = node_obj._get_type(context)

    if node_value not in the_node_templates:
        context.validation.report(
            '"%s" refers to an unknown node template in "%s"'
            % (presentation._name, presentation._container._fullname),
            locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_FIELDS)
        return

    if the_parent_node_type_name:
        if not _is_parent(context, the_nodetype_obj, the_parent_node_type_name, 'node_types'):
            context.validation.report(
                '"%s" refers to an unknown/inappropriate node type in "%s"'
                % (presentation._name, presentation._container._fullname),
                locator=presentation._get_child_locator(field.name),\
                        level=Issue.BETWEEN_FIELDS)
            return

    if the_nodetype_obj._get_capabilities(context):
        the_capabilities = the_nodetype_obj._get_capabilities(context)
        for the_capability in the_capabilities.iteritems():
            if _is_parent(context, the_capability[1]._get_type(context),\
                          the_parent_capability_type_name, 'capability_types'):
                return
        context.validation.report(
            '"%s" refers to a node template that does not match the capability requirement in "%s"'
            % (presentation._name, presentation._container._fullname),
            locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_FIELDS)
        return

def node_type_validator(field, presentation, context, node_value, node_obj):
    """
    Makes sure that the field refers to a node type.
    """
    the_child_nodetypes = []
    the_parent_capability_type_name = _get_requirement_in_type(context, presentation).\
                                      capability
    the_parent_node_type_name = _get_requirement_in_type(context, presentation).node

    node_type = get_type_by_name(context, node_value, 'node_types')
    if node_type is None:
        context.validation.report(
            '"%s" refers to an unknown node type in "%s"'
            % (presentation._name, presentation._container._fullname),
            locator=presentation._get_child_locator(field.name),\
            level=Issue.BETWEEN_FIELDS)
        return

    if the_parent_node_type_name:
        if not _is_parent(context, node_obj, the_parent_node_type_name, 'node_types'):
            context.validation.report(
                '"%s" refers to an unknown/inappropriate node type in "%s"'
                % (presentation._name, presentation._container._fullname),
                locator=presentation._get_child_locator(field.name),\
                level=Issue.BETWEEN_FIELDS)
            return

    for the_node_type in context.presentation.presenter.service_template.node_types.\
                         iteritems():
        if the_node_type[1]._get_capabilities(context):
            the_capabilities = the_node_type[1]._get_capabilities(context)
            for the_capability in the_capabilities.iteritems():
                if _is_parent(context, the_capability[1]._get_type(context),\
                              the_parent_capability_type_name, 'capability_types'):
                    the_child_nodetypes.append(the_node_type)

    for the_child_node_type in the_child_nodetypes:
        if _is_parent(context, the_child_node_type[1], node_obj._name, 'node_types'):
            return

    context.validation.report(
        '"%s" refers to a node type that does not match the capability requirement in "%s"'
        % (presentation._name, presentation._container._fullname),
        locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_FIELDS)
    return

def capability_definition_or_type_validator(field, presentation, context):
    """
    Makes sure refers to either a capability assignment name in the node template referred to by the
    ``node`` field or a general capability type.

    Used with the :func:`field_validator` decorator for the ``capability`` field in
    :class:`RequirementAssignment`.
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        node, node_variant = presentation._get_node(context)
        capability_variant = presentation._get_capability(context)[1]

        if capability_variant == 'capability_assignment':
            capability_definition_validator(field, presentation, context, value, node, node_variant)
        elif capability_variant == 'capability_type':
            capability_type_validator(field, presentation, context, value, node, node_variant)
        else:
            context.validation.report(
                'requirement "%s" refers to an unknown capability definition name or '\
                'type in "%s": %s'
                % (presentation._name, presentation._container._fullname, safe_repr(value)),
                locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_TYPES)

def capability_definition_validator(field, presentation, context, capability_value, node_obj,
                                    node_variant):
    """
    Makes sure if the capability name in the node template refers to a general capability definition
    """
    the_parent_capability_type_name = _get_requirement_in_type(context, presentation).\
                                              capability
    the_parent_node_type_name = _get_requirement_in_type(context, presentation).node

    if node_obj:
        _is_capability_in_node(context, node_variant, node_obj, presentation, field,
                               capability_value)

    if the_parent_node_type_name:
        the_nodetype_obj = get_type_by_name(context, the_parent_node_type_name,\
                                            'node_types')
        _is_capability_in_node(context, 'node_type', the_nodetype_obj, presentation,\
                               field, capability_value)

    for the_node_type in context.presentation.presenter.service_template.node_types.\
                         iteritems():
        if the_node_type[1]._get_capabilities(context):
            the_capabilities = the_node_type[1]._get_capabilities(context)
            for the_capability in the_capabilities.iteritems():
                if the_capability[1]._name == capability_value:
                    the_capability_type_name = the_capability[1].type

    the_capability_type_obj = get_type_by_name(context, the_capability_type_name,\
                                               'capability_types')
    if _is_parent(context, the_capability_type_obj, the_parent_capability_type_name,
                  'capability_types'):
        return

def capability_type_validator(field, presentation, context, capability_value, node_obj,
                              node_variant):
    """
    Makes sure if the capability type in the node template refers to a general capability type
    """
    the_parent_capability_type_name = _get_requirement_in_type(context, presentation).\
                                      capability
    the_parent_node_type_name = _get_requirement_in_type(context, presentation).node
    the_capability_type_obj = get_type_by_name(context, capability_value, 'capability_types')

    if node_obj:
        _is_capability_in_node(context, node_variant, node_obj, presentation, field,
                               capability_value)

    if the_parent_node_type_name:
        the_nodetype_obj = get_type_by_name(context, the_parent_node_type_name,\
                                            'node_types')
        _is_capability_in_node(context, 'node_type', the_nodetype_obj, presentation,\
                               field, capability_value)

    if the_capability_type_obj is not None and \
       _is_parent(context, the_capability_type_obj, the_parent_capability_type_name,
                  'capability_types'):

        return

def _get_requirement_in_type(context, presentation):
    the_nodetype_obj = presentation._container._get_type(context)
    the_requirements_obj = the_nodetype_obj._get_requirements(context)
    the_requirement_obj = None
    for the_requirement in the_requirements_obj:
        if the_requirement[0] == presentation._name:
            the_requirement_obj = the_requirement[1]
    return the_requirement_obj

def _is_capability_in_node(context, node_variant, node, presentation, field, value):
    if node_variant == 'node_template':
        the_nodetype_obj = node._get_type(context)
        if the_nodetype_obj._get_capabilities(context):
            the_capabilities = the_nodetype_obj._get_capabilities(context)
            for the_capability in the_capabilities.iteritems():
                if the_capability[1]._name == value or \
                   _is_parent(context, the_capability[1]._get_type(context), value,
                              'capability_types'):
                    return

            context.validation.report(
                '"%s" refers to a node template that does not match the capability requirement '\
                'in "%s"'
                % (presentation._name, presentation._container._fullname),
                locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_FIELDS)
            return


    if node_variant == 'node_type':
        the_child_nodetypes = []
        if get_type_by_name(context, node._name, 'node_types') is None:
            context.validation.report(
                '"%s" refers to an unknown/inappropriate node type in "%s"'
                % (presentation._name, presentation._container._fullname),
                locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_FIELDS)
            return

        for the_node_type in context.presentation.presenter.service_template.node_types.iteritems():
            if the_node_type[1]._get_capabilities(context):
                the_capabilities = the_node_type[1]._get_capabilities(context)
                for the_capability in the_capabilities.iteritems():
                    if the_capability[1].type == value or the_capability[1]._name == value:
                        the_child_nodetypes.append(the_node_type)

        for the_node_type in the_child_nodetypes:
            if _is_parent(context, the_node_type[1], node._name, 'node_types'):
                return

def _is_parent(context, type_obj, parent_type_name, parent_type):
    parent_type_name = convert_name_to_full_type_name(context, parent_type_name,
                                                      context.presentation.get('service_template',
                                                                               parent_type))
    if type_obj._name == parent_type_name:
        return True
    the_parent = type_obj._get_parent(context)
    if the_parent is not None:
        if the_parent._name == parent_type_name:
            return True
        found = _is_parent(context, the_parent, parent_type_name, parent_type)
        return found
    else:
        return False

def node_filter_validator(field, presentation, context):
    """
    Makes sure that the field has a value only if "node" refers to a node type.

    Used with the :func:`field_validator` decorator for the ``node_filter`` field in
    :class:`RequirementAssignment`.
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        _, node_type_variant = presentation._get_node(context)
        if node_type_variant != 'node_type':
            context.validation.report(
                u'requirement "{0}" has a node filter even though "node" does not refer to a node'
                u' type in "{1}"'
                .format(presentation._fullname, presentation._container._fullname),
                locator=presentation._locator, level=Issue.BETWEEN_FIELDS)


#
# RelationshipAssignment
#

def relationship_template_or_type_validator(field, presentation, context):
    """
    Makes sure that the field refers to either a relationship template or a relationship type.

    Used with the :func:`field_validator` decorator for the ``type`` field in
    :class:`RelationshipAssignment`.
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        relationship_templates = \
            context.presentation.get('service_template', 'topology_template',
                                     'relationship_templates') \
            or {}
        if (value not in relationship_templates) and \
            (get_type_by_name(context, value, 'relationship_types') is None):
            report_issue_for_unknown_type(context, presentation,
                                          'relationship template or relationship type', field.name)


#
# PolicyType
#

def list_node_type_or_group_type_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to either node types or a group types.

    Used with the :func:`field_validator` decorator for the ``targets`` field in
    :class:`PolicyType`.
    """

    field.default_validate(presentation, context)

    values = getattr(presentation, field.name)
    if values is not None:
        for value in values:
            if (get_type_by_name(context, value, 'node_types') is None) and \
                    (get_type_by_name(context, value, 'group_types') is None):
                report_issue_for_unknown_type(context, presentation, 'node type or group type',
                                              field.name, value)


#
# GroupTemplate
#

def group_members_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to node templates  and that they match the node types
    declared in the group type.

    Used with the :func:`field_validator` decorator for the ``targets`` field in
    :class:`GroupTemplate`.
    """

    field.default_validate(presentation, context)

    values = getattr(presentation, field.name)
    if values is not None:
        node_templates = \
            context.presentation.get('service_template', 'topology_template', 'node_templates') \
                or {}
        for value in values:
            if value not in node_templates:
                report_issue_for_unknown_type(context, presentation, 'node template', field.name,
                                              value)

            group_type = presentation._get_type(context)
            if group_type is None:
                break

            node_types = group_type._get_members(context)

            is_valid = False

            if value in node_templates:
                our_node_type = node_templates[value]._get_type(context)
                for node_type in node_types:
                    if node_type._is_descendant(context, our_node_type):
                        is_valid = True
                        break

            if not is_valid:
                context.validation.report(
                    u'group definition target does not match a node type'
                    u' declared in the group type in "{0}": {1}'
                    .format(presentation._name, safe_repr(value)),
                    locator=presentation._locator, level=Issue.BETWEEN_TYPES)


#
# PolicyTemplate
#

def policy_targets_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to either node templates or groups, and that
    they match the node types and group types declared in the policy type.

    Used with the :func:`field_validator` decorator for the ``targets`` field in
    :class:`PolicyTemplate`.
    """

    field.default_validate(presentation, context)

    values = getattr(presentation, field.name)
    if values is not None:
        node_templates = \
            context.presentation.get('service_template', 'topology_template', 'node_templates') \
                or {}
        groups = context.presentation.get('service_template', 'topology_template', 'groups') \
            or {}
        for value in values:
            if (value not in node_templates) and (value not in groups):
                report_issue_for_unknown_type(context, presentation, 'node template or group',
                                              field.name, value)

            policy_type = presentation._get_type(context)
            if policy_type is None:
                break

            node_types, group_types = policy_type._get_targets(context)

            is_valid = False

            if value in node_templates:
                our_node_type = node_templates[value]._get_type(context)
                for node_type in node_types:
                    if node_type._is_descendant(context, our_node_type):
                        is_valid = True
                        break

            elif value in groups:
                our_group_type = groups[value]._get_type(context)
                for group_type in group_types:
                    if group_type._is_descendant(context, our_group_type):
                        is_valid = True
                        break

            if not is_valid:
                context.validation.report(
                    u'policy definition target does not match either a node type or a group type'
                    u' declared in the policy type in "{0}": {1}'
                    .format(presentation._name, safe_repr(value)),
                    locator=presentation._locator, level=Issue.BETWEEN_TYPES)


#
# NodeFilter
#

def node_filter_properties_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to defined properties in the target node type.

    Used with the :func:`field_validator` decorator for the ``properties`` field in
    :class:`NodeFilter`.
    """

    field.default_validate(presentation, context)

    values = getattr(presentation, field.name)
    if values is not None:
        node_type = presentation._get_node_type(context)
        if node_type is not None:
            properties = node_type._get_properties(context)
            for name, _ in values:
                if name not in properties:
                    context.validation.report(
                        u'node filter refers to an unknown property definition in "{0}": {1}'
                        .format(node_type._name, name),
                        locator=presentation._locator, level=Issue.BETWEEN_TYPES)


def node_filter_capabilities_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to defined capabilities and properties in the target
    node type.

    Used with the :func:`field_validator` decorator for the ``capabilities`` field in
    :class:`NodeFilter`.
    """

    field.default_validate(presentation, context)

    values = getattr(presentation, field.name)
    if values is not None:                                                                          # pylint: disable=too-many-nested-blocks
        node_type = presentation._get_node_type(context)
        if node_type is not None:
            capabilities = node_type._get_capabilities(context)
            for name, value in values:
                capability = capabilities.get(name)
                if capability is not None:
                    properties = value.properties
                    capability_properties = capability.properties
                    if (properties is not None) and (capability_properties is not None):
                        for property_name, _ in properties:
                            if property_name not in capability_properties:
                                context.validation.report(
                                    u'node filter refers to an unknown capability definition'
                                    u' property in "{0}": {1}'
                                    .format(node_type._name, property_name),
                                    locator=presentation._locator, level=Issue.BETWEEN_TYPES)
                else:
                    context.validation.report(
                        u'node filter refers to an unknown capability definition in "{0}": {1}'
                        .format(node_type._name, name),
                        locator=presentation._locator, level=Issue.BETWEEN_TYPES)
