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

from aria.utils.formatting import safe_repr
from aria.parser.validation import Issue


def validate_substitution_mappings_requirement(context, presentation):
    # Validate that the requirement in substitution_mapping is defined in the substitution node type
    substitution_node_type = presentation._container._get_type(context)
    if substitution_node_type is None:
        return
    for req_name, req in substitution_node_type._get_requirements(context):
        if req_name == presentation._name:
            substitution_type_requirement = req
            break
    else:
        context.validation.report(
            u'substitution mapping requirement "{0}" is not declared in node type "{1}"'.format(
                presentation._name, substitution_node_type._name),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)
        return

    if not _validate_mapping_format(presentation):
        _report_invalid_mapping_format(context, presentation, field='requirement')
        return

    # Validate that the mapped requirement is defined in the corresponding node template
    node_template = _get_node_template(context, presentation)
    if node_template is None:
        _report_missing_node_template(context, presentation, field='requirement')
        return
    mapped_requirement_name = presentation._raw[1]
    for req_name, req in node_template._get_requirements(context):
        if req_name == mapped_requirement_name:
            node_template_requirement = req
            break
    else:
        context.validation.report(
            u'substitution mapping requirement "{0}" refers to an unknown requirement of node '
            u'template "{1}": {mapped_requirement_name}'.format(
                presentation._name, node_template._name,
                mapped_requirement_name=safe_repr(mapped_requirement_name)),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)
        return

    # Validate that the requirement's capability type in substitution_mapping is derived from the
    # requirement's capability type in the corresponding node template
    substitution_type_requirement_capability_type = \
        substitution_type_requirement._get_capability_type(context)
    node_template_requirement_capability_type = \
        node_template_requirement._get_capability(context)[0]
    if not substitution_type_requirement_capability_type._is_descendant(
            context, node_template_requirement_capability_type):
        context.validation.report(
            u'substitution mapping requirement "{0}" of capability type "{1}" is not a descendant '
            u'of the mapped node template capability type "{2}"'.format(
                presentation._name,
                substitution_type_requirement_capability_type._name,
                node_template_requirement_capability_type._name),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)


def validate_substitution_mappings_capability(context, presentation):
    # Validate that the capability in substitution_mapping is defined in the substitution node type
    substitution_node_type = presentation._container._get_type(context)
    if substitution_node_type is None:
        return
    substitution_type_capabilities = substitution_node_type._get_capabilities(context)
    substitution_type_capability = substitution_type_capabilities.get(presentation._name)
    if substitution_type_capability is None:
        context.validation.report(
            u'substitution mapping capability "{0}" '
            u'is not declared in node type "{substitution_type}"'.format(
                presentation._name, substitution_type=substitution_node_type._name),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)
        return

    if not _validate_mapping_format(presentation):
        _report_invalid_mapping_format(context, presentation, field='capability')
        return

    # Validate that the capability in substitution_mapping is declared in the corresponding
    # node template
    node_template = _get_node_template(context, presentation)
    if node_template is None:
        _report_missing_node_template(context, presentation, field='capability')
        return
    mapped_capability_name = presentation._raw[1]
    node_template_capability = node_template._get_capabilities(context).get(mapped_capability_name)

    if node_template_capability is None:
        context.validation.report(
            u'substitution mapping capability "{0}" refers to an unknown '
            u'capability of node template "{1}": {mapped_capability_name}'.format(
                presentation._name, node_template._name,
                mapped_capability_name=safe_repr(mapped_capability_name)),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)
        return

    # Validate that the capability type in substitution_mapping is derived from the capability type
    # in the corresponding node template
    substitution_type_capability_type = substitution_type_capability._get_type(context)
    node_template_capability_type = node_template_capability._get_type(context)
    if not substitution_type_capability_type._is_descendant(context, node_template_capability_type):
        context.validation.report(
            u'node template capability type "{0}" is not a descendant of substitution mapping '
            u'capability "{1}" of type "{2}"'.format(
                node_template_capability_type._name,
                presentation._name,
                substitution_type_capability_type._name),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)


#
# Utils
#

def _validate_mapping_format(presentation):
    """
    Validate that the mapping is a list of 2 strings.
    """
    if not isinstance(presentation._raw, list) or \
            len(presentation._raw) != 2 or \
            not isinstance(presentation._raw[0], basestring) or \
            not isinstance(presentation._raw[1], basestring):
        return False
    return True


def _get_node_template(context, presentation):
    node_template_name = presentation._raw[0]
    node_template = context.presentation.get_from_dict('service_template', 'topology_template',
                                                       'node_templates', node_template_name)
    return node_template


def _report_missing_node_template(context, presentation, field):
    context.validation.report(
        u'substitution mappings {field} "{node_template_mapping}" '
        u'refers to an unknown node template: {node_template_name}'.format(
            field=field,
            node_template_mapping=presentation._name,
            node_template_name=safe_repr(presentation._raw[0])),
        locator=presentation._locator, level=Issue.FIELD)


def _report_invalid_mapping_format(context, presentation, field):
    context.validation.report(
        u'substitution mapping {field} "{field_name}" is not a list of 2 strings: {value}'.format(
            field=field,
            field_name=presentation._name,
            value=safe_repr(presentation._raw)),
        locator=presentation._locator, level=Issue.FIELD)
