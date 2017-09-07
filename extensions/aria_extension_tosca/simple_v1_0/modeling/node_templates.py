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


def validate_type_in_regards_to_substitution_mapping(context, node_template):
    """
    Reports iff the node is in a substituting template, and is derived from the substituting type

    :param context: :class:`aria.parser.consumption.context.ConsumptionContext`
    :param node_template: :class:`aria_extension_tosca.v1_0.templates.NodeTemplate`
    """
    substitution_mappings = node_template._container.substitution_mappings
    if not substitution_mappings:
        return
    substitution_type = substitution_mappings._get_type(context)
    node_type = node_template._get_type(context)
    if substitution_type._is_descendant(context, node_type):
        context.validation.report(
            'type {0} of node template {1} is a descendant of substitution type {2}. in a service '
            'template that contains a substitution_mapping section, you cannot define a node '
            'template that descends from the substitution mapping type.'.format(
                node_type._name, node_template._name, substitution_type._name))
