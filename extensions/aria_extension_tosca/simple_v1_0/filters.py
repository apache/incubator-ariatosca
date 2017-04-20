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

from aria.utils.caching import cachedmethod
from aria.parser import implements_specification
from aria.parser.presentation import (has_fields, object_sequenced_list_field, field_validator)

from .misc import ConstraintClause
from .presentation.extensible import ExtensiblePresentation
from .presentation.field_validators import (node_filter_properties_validator,
                                            node_filter_capabilities_validator)

@has_fields
class CapabilityFilter(ExtensiblePresentation):
    @object_sequenced_list_field(ConstraintClause)
    def properties(self):
        pass

    @cachedmethod
    def _get_node_type(self, context):
        return self._container._get_node_type(context)

    @cachedmethod
    def _get_type_for_name(self, context, name):
        node_type = self._get_node_type(context)
        if node_type is not None:
            capabilities = node_type._get_capabilities(context)
            capability = capabilities.get(self._name)
            properties = capability.properties if capability is not None else None
            prop = properties.get(name) if properties is not None else None
            return prop._get_type(context) if prop is not None else None

        return None

@has_fields
@implements_specification('3.5.4', 'tosca-simple-1.0')
class NodeFilter(ExtensiblePresentation):
    """
    A node filter definition defines criteria for selection of a TOSCA Node Template based upon the
    template's property values, capabilities and capability properties.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_NODE_FILTER_DEFN>`__
    """

    @field_validator(node_filter_properties_validator)
    @object_sequenced_list_field(ConstraintClause)
    @implements_specification('3.5.3', 'tosca-simple-1.0')
    def properties(self):
        """
        An optional sequenced list of property filters that would be used to select (filter)
        matching TOSCA entities (e.g., Node Template, Node Type, Capability Types, etc.) based upon
        their property definitions' values.

        See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
        /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
        #DEFN_ELEMENT_PROPERTY_FILTER_DEFN>`__

        :rtype: list of (str, :class:`ConstraintClause`)
        """

    @field_validator(node_filter_capabilities_validator)
    @object_sequenced_list_field(CapabilityFilter)
    def capabilities(self):
        """
        An optional sequenced list of property filters that would be used to select (filter)
        matching TOSCA entities (e.g., Node Template, Node Type, Capability Types, etc.) based upon
        their capabilities' property definitions' values.

        :rtype: list of (str, :class:`CapabilityDefinition`)
        """

    @cachedmethod
    def _get_node_type(self, context):
        if hasattr(self._container, '_get_node'):
            node_type, node_type_variant = self._container._get_node(context)
            return node_type if node_type_variant == 'node_type' else None
        return None

    @cachedmethod
    def _get_type_for_name(self, context, name):
        node_type = self._get_node_type(context)
        if node_type is not None:
            properties = node_type._get_properties(context)
            prop = properties.get(name)
            return prop._get_type(context) if prop is not None else None

        return None
