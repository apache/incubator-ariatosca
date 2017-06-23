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

from aria.utils.collections import FrozenDict
from aria.utils.caching import cachedmethod
from aria.parser import implements_specification
from aria.parser.presentation import (AsIsPresentation, has_fields, allow_unknown_fields,
                                      short_form_field, primitive_field, object_field,
                                      object_dict_field, object_dict_unknown_fields,
                                      field_validator, type_validator)

from .filters import NodeFilter
from .misc import Description, OperationImplementation
from .modeling.parameters import get_assigned_and_defined_parameter_values
from .presentation.extensible import ExtensiblePresentation
from .presentation.field_validators import (node_template_or_type_validator,
                                            relationship_template_or_type_validator,
                                            capability_definition_or_type_validator,
                                            node_filter_validator)
from .presentation.types import (convert_shorthand_to_full_type_name,
                                 get_type_by_full_or_shorthand_name)

@implements_specification('3.5.9', 'tosca-simple-1.0')
class PropertyAssignment(AsIsPresentation):
    """
    This section defines the grammar for assigning values to named properties within TOSCA Node and
    Relationship templates that are defined in their corresponding named types.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_PROPERTY_VALUE_ASSIGNMENT>`__
    """

@short_form_field('implementation')
@has_fields
@implements_specification('3.5.13-2', 'tosca-simple-1.0')
class OperationAssignment(ExtensiblePresentation):
    """
    An operation definition defines a named function or procedure that can be bound to an
    implementation artifact (e.g., a script).

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_OPERATION_DEF>`__
    """

    @object_field(Description)
    def description(self):
        """
        The optional description string for the associated named operation.

        :type: :class:`Description`
        """

    @object_field(OperationImplementation)
    def implementation(self):
        """
        The optional implementation artifact name (e.g., a script file name within a TOSCA CSAR
        file).

        :type: :class:`OperationImplementation`
        """

    @object_dict_field(PropertyAssignment)
    def inputs(self):
        """
        The optional list of input property assignments (i.e., parameters assignments) for operation
        definitions that are within TOSCA Node or Relationship Template definitions. This includes
        when operation definitions are included as part of a Requirement assignment in a Node
        Template.

        :type: {:obj:`basestring`: :class:`PropertyAssignment`}
        """

    @cachedmethod
    def _get_extensions(self, context):
        def update_inherited_extensions(extensions, interface_type):
            parent = interface_type._get_parent(context)
            if parent is not None:
                update_inherited_extensions(extensions, parent)
            operation_definition = interface_type.operations.get(self._name)
            if operation_definition is not None:
                if operation_definition._extensions:
                    extensions.update(operation_definition._extensions)

        extensions = {}
        update_inherited_extensions(extensions, self._container._get_type(context))
        if self._container._extensions:
            extensions.update(self._container._extensions)
        if self._extensions:
            extensions.update(self._extensions)
        return extensions

@allow_unknown_fields
@has_fields
@implements_specification('3.5.14-2', 'tosca-simple-1.0')
class InterfaceAssignment(ExtensiblePresentation):
    """
    An interface definition defines a named interface that can be associated with a Node or
    Relationship Type.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_INTERFACE_DEF>`__
    """

    @object_dict_field(PropertyAssignment)
    def inputs(self):
        """
        The optional list of input property assignments (i.e., parameters assignments) for interface
        definitions that are within TOSCA Node or Relationship Template definitions. This includes
        when interface definitions are referenced as part of a Requirement assignment in a Node
        Template.

        :type: {:obj:`basestring`: :class:`PropertyAssignment`}
        """

    @object_dict_unknown_fields(OperationAssignment)
    def operations(self):
        """
        :type: {:obj:`basestring`: :class:`OperationAssignment`}
        """

    @cachedmethod
    def _get_type(self, context):
        the_type = self._container._get_type(context)

        if isinstance(the_type, tuple):
            # In RelationshipAssignment
            the_type = the_type[0] # This could be a RelationshipTemplate

        interface_definitions = the_type._get_interfaces(context) \
            if the_type is not None else None
        interface_definition = interface_definitions.get(self._name) \
            if interface_definitions is not None else None
        return interface_definition._get_type(context) \
            if interface_definition is not None else None

    def _validate(self, context):
        super(InterfaceAssignment, self)._validate(context)
        if self.operations:
            for operation in self.operations.itervalues(): # pylint: disable=no-member
                operation._validate(context)

@short_form_field('type')
@has_fields
class RelationshipAssignment(ExtensiblePresentation):
    """
    Relationship assignment.
    """

    @field_validator(relationship_template_or_type_validator)
    @primitive_field(str)
    def type(self):
        """
        The optional reserved keyname used to provide the name of the Relationship Type for the
        requirement assignment's relationship keyname.

        :type: :obj:`basestring`
        """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        ARIA NOTE: This field is not mentioned in the spec, but is implied.

        :type: {:obj:`basestring`: :class:`PropertyAssignment`}
        """

    @object_dict_field(InterfaceAssignment)
    def interfaces(self):
        """
        The optional reserved keyname used to reference declared (named) interface definitions of
        the corresponding Relationship Type in order to provide Property assignments for these
        interfaces or operations of these interfaces.

        :type: {:obj:`basestring`: :class:`InterfaceAssignment`}
        """

    @cachedmethod
    def _get_type(self, context):
        type_name = self.type
        if type_name is not None:
            the_type = context.presentation.get_from_dict('service_template', 'topology_template',
                                                          'relationship_templates', type_name)
            if the_type is not None:
                return the_type, 'relationship_template'
            the_type = get_type_by_full_or_shorthand_name(context, type_name, 'relationship_types')
            if the_type is not None:
                return the_type, 'relationship_type'
        return None, None

@short_form_field('node')
@has_fields
@implements_specification('3.7.2', 'tosca-simple-1.0')
class RequirementAssignment(ExtensiblePresentation):
    """
    A Requirement assignment allows template authors to provide either concrete names of TOSCA
    templates or provide abstract selection criteria for providers to use to find matching TOSCA
    templates that are used to fulfill a named requirement's declared TOSCA Node Type.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_REQUIREMENT_ASSIGNMENT>`__
    """

    # The example in 3.7.2.2.2 shows unknown fields in addition to these, but is this a mistake?

    @field_validator(capability_definition_or_type_validator)
    @primitive_field(str)
    def capability(self):
        """
        The optional reserved keyname used to provide the name of either a:

        * Capability definition within a target node template that can fulfill the requirement.
        * Capability Type that the provider will use to select a type-compatible target node
          template to fulfill the requirement at runtime.

        :type: :obj:`basestring`
        """

    @field_validator(node_template_or_type_validator)
    @primitive_field(str)
    def node(self):
        """
        The optional reserved keyname used to identify the target node of a relationship.
        Specifically, it is used to provide either a:

        * Node Template name that can fulfill the target node requirement.
        * Node Type name that the provider will use to select a type-compatible node template to
          fulfill the requirement at runtime.

        :type: :obj:`basestring`
        """

    @object_field(RelationshipAssignment)
    def relationship(self):
        """
        The optional reserved keyname used to provide the name of either a:

        * Relationship Template to use to relate the source node to the (capability in the) target
          node when fulfilling the requirement.
        * Relationship Type that the provider will use to select a type-compatible relationship
          template to relate the source node to the target node at runtime.

        :type: :class:`RelationshipAssignment`
        """

    @field_validator(node_filter_validator)
    @object_field(NodeFilter)
    def node_filter(self):
        """
        The optional filter definition that TOSCA orchestrators or providers would use to select a
        type-compatible target node that can fulfill the associated abstract requirement at runtime.

        :type: :class:`NodeFilter`
        """

    @cachedmethod
    def _get_node(self, context):
        node = self.node

        if node is not None:
            node_template = context.presentation.get_from_dict('service_template',
                                                               'topology_template',
                                                               'node_templates', node)
            if node_template is not None:
                return node_template, 'node_template'
            node_type = get_type_by_full_or_shorthand_name(context, node, 'node_types')
            if node_type is not None:
                return node_type, 'node_type'

        return None, None

    @cachedmethod
    def _get_capability(self, context):
        capability = self.capability

        if capability is not None:
            node, node_variant = self._get_node(context)
            if node_variant == 'node_template':
                capabilities = node._get_capabilities(context)
                if capability in capabilities:
                    return capabilities[capability], 'capability_assignment'
            capability_type = get_type_by_full_or_shorthand_name(context, capability,
                                                                 'capability_types')
            if capability_type is not None:
                return capability_type, 'capability_type'

        return None, None

@implements_specification('3.5.11', 'tosca-simple-1.0')
class AttributeAssignment(AsIsPresentation):
    """
    This section defines the grammar for assigning values to named attributes within TOSCA Node and
    Relationship templates which are defined in their corresponding named types.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_ATTRIBUTE_VALUE_ASSIGNMENT>`__
    """

@has_fields
@implements_specification('3.7.1', 'tosca-simple-1.0')
class CapabilityAssignment(ExtensiblePresentation):
    """
    A capability assignment allows node template authors to assign values to properties and
    attributes for a named capability definition that is part of a Node Template's type definition.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_CAPABILITY_ASSIGNMENT>`__
    """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        An optional list of property definitions for the Capability definition.

        :type: {:obj:`basestring`: :class:`PropertyAssignment`}
        """

    @object_dict_field(AttributeAssignment)
    def attributes(self):
        """
        An optional list of attribute definitions for the Capability definition.

        :type: {:obj:`basestring`: :class:`AttributeAssignment`}
        """

    @cachedmethod
    def _get_definition(self, context):
        node_type = self._container._get_type(context)
        capability_definitions = node_type._get_capabilities(context) \
            if node_type is not None else None
        return capability_definitions.get(self._name) \
            if capability_definitions is not None else None

    @cachedmethod
    def _get_type(self, context):
        capability_definition = self._get_definition(context)
        return capability_definition._get_type(context) \
            if capability_definition is not None else None

@has_fields
@implements_specification('3.5.6', 'tosca-simple-1.0')
class ArtifactAssignment(ExtensiblePresentation):
    """
    An artifact definition defines a named, typed file that can be associated with Node Type or Node
    Template and used by orchestration engine to facilitate deployment and implementation of
    interface operations.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ENTITY_ARTIFACT_DEF>`__
    """

    @field_validator(type_validator('artifact type', convert_shorthand_to_full_type_name,
                                    'artifact_types'))
    @primitive_field(str, required=True)
    def type(self):
        """
        The required artifact type for the artifact definition.

        :type: :obj:`basestring`
        """

    @primitive_field(str, required=True)
    def file(self):
        """
        The required URI string (relative or absolute) which can be used to locate the artifact's
        file.

        :type: :obj:`basestring`
        """

    @field_validator(type_validator('repository', 'repositories'))
    @primitive_field(str)
    def repository(self):
        """
        The optional name of the repository definition which contains the location of the external
        repository that contains the artifact. The artifact is expected to be referenceable by its
        file URI within the repository.

        :type: :obj:`basestring`
        """

    @object_field(Description)
    def description(self):
        """
        The optional description for the artifact definition.

        :type: :class:`Description`
        """

    @primitive_field(str)
    def deploy_path(self):
        """
        The file path the associated file would be deployed into within the target node's container.

        :type: :obj:`basestring`
        """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        ARIA NOTE: This field is not mentioned in the spec, but is implied.

        :type: {:obj:`basestring`: :class:`PropertyAssignment`}
        """

    @cachedmethod
    def _get_type(self, context):
        return get_type_by_full_or_shorthand_name(context, self.type, 'artifact_types')

    @cachedmethod
    def _get_repository(self, context):
        return context.presentation.get_from_dict('service_template', 'repositories',
                                                  self.repository)

    @cachedmethod
    def _get_property_values(self, context):
        return FrozenDict(get_assigned_and_defined_parameter_values(context, self, 'property'))

    @cachedmethod
    def _validate(self, context):
        super(ArtifactAssignment, self)._validate(context)
        self._get_property_values(context)
