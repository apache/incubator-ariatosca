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

from ..presentation.types import convert_name_to_full_type_name


#
# GroupType
#

def get_inherited_members(context, presentation):
    """
    Returns our target node types if we have them or those of our parent, if we have one
    (recursively).
    """

    parent = presentation._get_parent(context)

    node_types = get_inherited_members(context, parent) if parent is not None else []

    our_members = presentation.members
    if our_members:
        all_node_types = context.presentation.get('service_template', 'node_types') or {}
        node_types = []

        for our_member in our_members:
            if our_member in all_node_types:
                our_member = convert_name_to_full_type_name(context, our_member, all_node_types)
                node_types.append(all_node_types[our_member])

    return node_types
