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

from ..presentation.types import convert_shorthand_to_full_type_name


#
# PolicyType
#

def get_inherited_targets(context, presentation):
    """
    Returns our target node types and group types if we have them or those of our parent, if we have
    one (recursively).
    """

    parent = presentation._get_parent(context)

    node_types, group_types = get_inherited_targets(context, parent) \
        if parent is not None else ([], [])

    our_targets = presentation.targets
    if our_targets:
        all_node_types = context.presentation.get('service_template', 'node_types') or {}
        all_group_types = context.presentation.get('service_template', 'group_types') or {}
        node_types = []
        group_types = []

        for our_target in our_targets:
            if our_target in all_node_types:
                our_target = convert_shorthand_to_full_type_name(context, our_target,
                                                                 all_node_types)
                node_types.append(all_node_types[our_target])
            elif our_target in all_group_types:
                our_target = convert_shorthand_to_full_type_name(context, our_target,
                                                                 all_group_types)
                group_types.append(all_group_types[our_target])

    return node_types, group_types


#
# PolicyTemplate
#

def get_policy_targets(context, presentation):
    """
    Returns our target node templates and groups if we have them.
    """

    node_templates = []
    groups = []

    our_targets = presentation.targets
    if our_targets:
        all_node_templates = \
            context.presentation.get('service_template', 'topology_template', 'node_templates') \
            or {}
        all_groups = \
            context.presentation.get('service_template', 'topology_template', 'groups') \
            or {}

        for our_target in our_targets:
            if our_target in all_node_templates:
                node_templates.append(all_node_templates[our_target])
            elif our_target in all_groups:
                groups.append(all_groups[our_target])

    return node_templates, groups
