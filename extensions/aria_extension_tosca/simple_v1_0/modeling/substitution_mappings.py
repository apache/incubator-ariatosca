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

def validate_subtitution_mappings_requirement(context, presentation):
    if not validate_format(context, presentation, 'requirement'):
        return

    node_template = get_node_template(context, presentation, 'requirement')
    if node_template is None:
        return

    node_type = presentation._container._get_type(context)
    if node_type is None:
        return

    requirements = node_type._get_requirements(context)
    type_requirement = None
    for name, the_requirement in requirements:
        if name == presentation._name:
            type_requirement = the_requirement
            break
    if type_requirement is None:
        context.validation.report(
            'substitution mappings requirement "%s" is not declared in node type "%s"'
            % (presentation._name, node_type._name),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)
        return

    requirement_name = presentation._raw[1]
    requirements = node_template._get_requirements(context)
    requirement = None
    for name, the_requirement in requirements:
        if name == requirement_name:
            requirement = the_requirement
            break

    if requirement is None:
        context.validation.report(
            'substitution mappings requirement "%s" refers to an unknown requirement of node '
            'template "%s": %s'
            % (presentation._name, node_template._name, safe_repr(requirement_name)),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)
        return

def validate_subtitution_mappings_capability(context, presentation):
    if not validate_format(context, presentation, 'capability'):
        return

    node_template = get_node_template(context, presentation, 'capability')
    if node_template is None:
        return

    node_type = presentation._container._get_type(context)
    if node_type is None:
        return

    capabilities = node_type._get_capabilities(context)
    type_capability = capabilities.get(presentation._name)
    if type_capability is None:
        context.validation.report(
            'substitution mappings capability "%s" is not declared in node type "%s"'
            % (presentation._name, node_type._name), locator=presentation._locator,
            level=Issue.BETWEEN_TYPES)
        return

    capability_name = presentation._raw[1]
    capabilities = node_template._get_capabilities(context)
    capability = capabilities.get(capability_name)

    if capability is None:
        context.validation.report(
            'substitution mappings capability "%s" refers to an unknown capability of node template'
            ' "%s": %s'
            % (presentation._name, node_template._name, safe_repr(capability_name)),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)
        return

    type_capability_type = type_capability._get_type(context)
    capability_type = capability._get_type(context)

    if not type_capability_type._is_descendant(context, capability_type):
        context.validation.report(
            'type "%s" of substitution mappings capability "%s" is not a descendant of "%s"'
            % (capability_type._name, presentation._name, type_capability_type._name),
            locator=presentation._locator, level=Issue.BETWEEN_TYPES)

#
# Utils
#

def validate_format(context, presentation, name):
    if (not isinstance(presentation._raw, list)) or (len(presentation._raw) != 2) \
        or (not isinstance(presentation._raw[0], basestring)) \
        or (not isinstance(presentation._raw[1], basestring)):
        context.validation.report(
            'substitution mappings %s "%s" is not a list of 2 strings: %s'
            % (name, presentation._name, safe_repr(presentation._raw)),
            locator=presentation._locator, level=Issue.FIELD)
        return False
    return True

def get_node_template(context, presentation, name):
    node_template_name = presentation._raw[0]
    node_template = context.presentation.get_from_dict('service_template', 'topology_template',
                                                       'node_templates', node_template_name)
    if node_template is None:
        context.validation.report(
            'substitution mappings %s "%s" refers to an unknown node template: %s'
            % (name, presentation._name, safe_repr(node_template_name)),
            locator=presentation._locator, level=Issue.FIELD)
    return node_template
