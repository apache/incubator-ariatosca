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

from aria.utils.collections import FrozenDict, FrozenList
from aria.utils.caching import cachedmethod
from aria.parser import implements_specification
from aria.parser.presentation import (has_fields, allow_unknown_fields, primitive_field,
                                      primitive_list_field, object_field, object_dict_field,
                                      object_list_field, object_sequenced_list_field,
                                      object_dict_unknown_fields, field_getter, field_validator,
                                      list_type_validator, derived_from_validator,
                                      get_parent_presentation)

from .assignments import ArtifactAssignment
from .data_types import Version
from .definitions import (PropertyDefinition, AttributeDefinition, InterfaceDefinition,
                          RequirementDefinition, CapabilityDefinition, OperationDefinition)
from .misc import (Description, ConstraintClause)
from .modeling.artifacts import get_inherited_artifact_definitions
from .modeling.capabilities import (get_inherited_valid_source_types,
                                    get_inherited_capability_definitions)
from .modeling.data_types import (get_data_type, get_inherited_constraints, coerce_data_type_value,
                                  validate_data_type_name)
from .modeling.interfaces import (get_inherited_interface_definitions, get_inherited_operations)
from .modeling.policies import get_inherited_targets
from .modeling.parameters import get_inherited_parameter_definitions
from .modeling.requirements import get_inherited_requirement_definitions
from .presentation.extensible import ExtensiblePresentation
from .presentation.field_getters import data_type_class_getter
from .presentation.field_validators import (data_type_derived_from_validator,
                                            data_type_constraints_validator,
                                            data_type_properties_validator,
                                            list_node_type_or_group_type_validator)
from .presentation.types import convert_shorthand_to_full_type_name

@has_fields
@implements_specification('3.6.3', 'tosca-simple-1.0')
class ArtifactType(ExtensiblePresentation):
    """
    An Artifact Type is a reusable entity that defines the type of one or more files that are used
    to define implementation or deployment artifacts that are referenced by nodes or relationships
    on their operations.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ENTITY_ARTIFACT_TYPE>`__
    """

    @field_validator(derived_from_validator(convert_shorthand_to_full_type_name, 'artifact_types'))
    @primitive_field(str)
    def derived_from(self):
        """
        An optional parent Artifact Type name the Artifact Type derives from.

        :rtype: str
        """

    @field_getter(data_type_class_getter(Version))
    @primitive_field()
    def version(self):
        """
        An optional version for the Artifact Type definition.

        :rtype: :class:`Version`
        """

    @object_field(Description)
    def description(self):
        """
        An optional description for the Artifact Type.

        :rtype: :class:`Description`
        """

    @primitive_field(str)
    def mime_type(self):
        """
        The required mime type property for the Artifact Type.

        :rtype: str
        """

    @primitive_list_field(str)
    def file_ext(self):
        """
        The required file extension property for the Artifact Type.

        :rtype: list of str
        """

    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        An optional list of property definitions for the Artifact Type.

        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_parent_presentation(context, self, convert_shorthand_to_full_type_name,
                                       'artifact_types')

    @cachedmethod
    def _get_properties(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'properties'))

    def _validate(self, context):
        super(ArtifactType, self)._validate(context)
        self._get_properties(context)

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'version',
            'derived_from',
            'mime_type',
            'file_ext',
            'properties'))

@has_fields
@implements_specification('3.6.5', 'tosca-simple-1.0')
class DataType(ExtensiblePresentation):
    """
    A Data Type definition defines the schema for new named datatypes in TOSCA.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ENTITY_DATA_TYPE>`__
    """

    @field_validator(data_type_derived_from_validator)
    @primitive_field(str)
    def derived_from(self):
        """
        The optional key used when a datatype is derived from an existing TOSCA Data Type.

        :rtype: str
        """

    @object_field(Version)
    def version(self):
        """
        An optional version for the Data Type definition.

        :rtype: :class:`Version`
        """

    @object_field(Description)
    def description(self):
        """
        The optional description for the Data Type.

        :rtype: :class:`Description`
        """

    @field_validator(data_type_constraints_validator)
    @object_list_field(ConstraintClause)
    def constraints(self):
        """
        The optional list of sequenced constraint clauses for the Data Type.

        :rtype: list of (str, :class:`ConstraintClause`)
        """

    @field_validator(data_type_properties_validator)
    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        The optional list property definitions that comprise the schema for a complex Data Type in
        TOSCA.

        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_data_type(context, self, 'derived_from', allow_none=True)

    @cachedmethod
    def _get_primitive_ancestor(self, context):
        parent = self._get_parent(context)
        if parent is not None:
            if not isinstance(parent, DataType):
                return parent
            else:
                return parent._get_primitive_ancestor(context) # pylint: disable=no-member
        return None

    @cachedmethod
    def _get_properties(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'properties'))

    @cachedmethod
    def _get_constraints(self, context):
        return get_inherited_constraints(context, self)

    def _validate(self, context):
        super(DataType, self)._validate(context)
        validate_data_type_name(context, self)
        self._get_properties(context)

    def _coerce_value(self, context, presentation, entry_schema, constraints, value, aspect):
        return coerce_data_type_value(context, presentation, self, entry_schema, constraints, value,
                                      aspect)

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'version',
            'derived_from',
            'constraints',
            'properties'))

@has_fields
@implements_specification('3.6.6', 'tosca-simple-1.0')
class CapabilityType(ExtensiblePresentation):
    """
    A Capability Type is a reusable entity that describes a kind of capability that a Node Type can
    declare to expose. Requirements (implicit or explicit) that are declared as part of one node can
    be matched to (i.e., fulfilled by) the Capabilities declared by another node.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ENTITY_CAPABILITY_TYPE>`__
    """

    @field_validator(derived_from_validator(convert_shorthand_to_full_type_name,
                                            'capability_types'))
    @primitive_field(str)
    def derived_from(self):
        """
        An optional parent capability type name this new Capability Type derives from.

        :rtype: str
        """

    @object_field(Version)
    def version(self):
        """
        An optional version for the Capability Type definition.

        :rtype: :class:`Version`
        """

    @object_field(Description)
    def description(self):
        """
        An optional description for the Capability Type.

        :rtype: :class:`Description`
        """

    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        An optional list of property definitions for the Capability Type.

        ARIA NOTE: The spec says 'list', but the examples are all of dicts.

        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @object_dict_field(AttributeDefinition)
    def attributes(self):
        """
        An optional list of attribute definitions for the Capability Type.

        :rtype: dict of str, :class:`AttributeDefinition`
        """

    @field_validator(list_type_validator('node type', convert_shorthand_to_full_type_name,
                                         'node_types'))
    @primitive_list_field(str)
    def valid_source_types(self):
        """
        An optional list of one or more valid names of Node Types that are supported as valid
        sources of any relationship established to the declared Capability Type.

        :rtype: list of str
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_parent_presentation(context, self, convert_shorthand_to_full_type_name,
                                       'capability_types')

    @cachedmethod
    def _is_descendant(self, context, the_type):
        if the_type is None:
            return False
        elif the_type._name == self._name:
            return True
        return self._is_descendant(context, the_type._get_parent(context))

    @cachedmethod
    def _get_properties(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'properties'))

    @cachedmethod
    def _get_valid_source_types(self, context):
        return get_inherited_valid_source_types(context, self)

    def _validate(self, context):
        super(CapabilityType, self)._validate(context)
        self._get_properties(context)

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'version',
            'derived_from',
            'valid_source_types',
            'properties',
            'attributes'))

@allow_unknown_fields
@has_fields
@implements_specification('3.6.4', 'tosca-simple-1.0')
class InterfaceType(ExtensiblePresentation):
    """
    An Interface Type is a reusable entity that describes a set of operations that can be used to
    interact with or manage a node or relationship in a TOSCA topology.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ENTITY_INTERFACE_TYPE>`__
    """

    @field_validator(derived_from_validator(convert_shorthand_to_full_type_name, 'interface_types'))
    @primitive_field(str)
    def derived_from(self):
        """
        An optional parent Interface Type name this new Interface Type derives from.

        :rtype: str
        """

    @object_field(Version)
    def version(self):
        """
        An optional version for the Interface Type definition.

        :rtype: :class:`Version`
        """

    @object_field(Description)
    def description(self):
        """
        An optional description for the Interface Type.

        :rtype: :class:`Description`
        """

    @object_dict_field(PropertyDefinition)
    def inputs(self):
        """
        The optional list of input parameter definitions.

        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @object_dict_unknown_fields(OperationDefinition)
    def operations(self):
        """
        :rtype: dict of str, :class:`OperationDefinition`
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_parent_presentation(context, self, convert_shorthand_to_full_type_name,
                                       'interface_types')

    @cachedmethod
    def _get_inputs(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'inputs'))

    @cachedmethod
    def _get_operations(self, context):
        return FrozenDict(get_inherited_operations(context, self))

    def _validate(self, context):
        super(InterfaceType, self)._validate(context)
        self._get_inputs(context)
        for operation in self.operations.itervalues(): # pylint: disable=no-member
            operation._validate(context)

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'version',
            'derived_from',
            'inputs',
            'operations'))

@has_fields
@implements_specification('3.6.9', 'tosca-simple-1.0')
class RelationshipType(ExtensiblePresentation):
    """
    A Relationship Type is a reusable entity that defines the type of one or more relationships
    between Node Types or Node Templates.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ENTITY_RELATIONSHIP_TYPE>`__
    """

    @field_validator(derived_from_validator(convert_shorthand_to_full_type_name,
                                            'relationship_types'))
    @primitive_field(str)
    def derived_from(self):
        """
        An optional parent Relationship Type name the Relationship Type derives from.

        :rtype: str
        """

    @object_field(Version)
    def version(self):
        """
        An optional version for the Relationship Type definition.

        :rtype: :class:`Version`
        """

    @object_field(Description)
    def description(self):
        """
        An optional description for the Relationship Type.

        :rtype: :class:`Description`
        """

    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        An optional list of property definitions for the Relationship Type.

        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @object_dict_field(AttributeDefinition)
    def attributes(self):
        """
        An optional list of attribute definitions for the Relationship Type.

        :rtype: dict of str, :class:`AttributeDefinition`
        """

    @object_dict_field(InterfaceDefinition)
    def interfaces(self):
        """
        An optional list of interface definitions interfaces supported by the Relationship Type.

        :rtype: dict of str, :class:`InterfaceDefinition`
        """

    @field_validator(list_type_validator('capability type', convert_shorthand_to_full_type_name,
                                         'capability_types'))
    @primitive_list_field(str)
    def valid_target_types(self):
        """
        An optional list of one or more names of Capability Types that are valid targets for this
        relationship.

        :rtype: list of str
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_parent_presentation(context, self, convert_shorthand_to_full_type_name,
                                       'relationship_types')

    @cachedmethod
    def _is_descendant(self, context, the_type):
        if the_type is None:
            return False
        elif the_type._name == self._name:
            return True
        return self._is_descendant(context, the_type._get_parent(context))

    @cachedmethod
    def _get_properties(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'properties'))

    @cachedmethod
    def _get_attributes(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'attributes'))

    @cachedmethod
    def _get_interfaces(self, context):
        return FrozenDict(get_inherited_interface_definitions(context, self, 'relationship type'))

    def _validate(self, context):
        super(RelationshipType, self)._validate(context)
        self._get_properties(context)
        self._get_attributes(context)
        self._get_interfaces(context)

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'version',
            'derived_from',
            'valid_target_types',
            'properties',
            'attributes',
            'interfaces'))

@has_fields
@implements_specification('3.6.8', 'tosca-simple-1.0')
class NodeType(ExtensiblePresentation):
    """
    A Node Type is a reusable entity that defines the type of one or more Node Templates. As such, a
    Node Type defines the structure of observable properties via a Properties Definition, the
    Requirements and Capabilities of the node as well as its supported interfaces.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ENTITY_NODE_TYPE>`__
    """

    @field_validator(derived_from_validator(convert_shorthand_to_full_type_name, 'node_types'))
    @primitive_field(str)
    def derived_from(self):
        """
        An optional parent Node Type name this new Node Type derives from.

        :rtype: str
        """

    @object_field(Version)
    def version(self):
        """
        An optional version for the Node Type definition.

        :rtype: :class:`Version`
        """

    @object_field(Description)
    def description(self):
        """
        An optional description for the Node Type.

        :rtype: :class:`Description`
        """

    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        An optional list of property definitions for the Node Type.

        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @object_dict_field(AttributeDefinition)
    def attributes(self):
        """
        An optional list of attribute definitions for the Node Type.

        :rtype: dict of str, :class:`AttributeDefinition`
        """

    @object_sequenced_list_field(RequirementDefinition)
    def requirements(self):
        """
        An optional sequenced list of requirement definitions for the Node Type.

        ARIA NOTE: The spec seems wrong to make this a sequenced list. It seems that when you have
        more than one requirement of the same name, behavior is undefined. The idea is to use the
        "occurrences" field if you need to limit the number of requirement assignments.

        :rtype: list of (str, :class:`RequirementDefinition`)
        """

    @object_dict_field(CapabilityDefinition)
    def capabilities(self):
        """
        An optional list of capability definitions for the Node Type.

        :rtype: list of :class:`CapabilityDefinition`
        """

    @object_dict_field(InterfaceDefinition)
    def interfaces(self):
        """
        An optional list of interface definitions supported by the Node Type.

        :rtype: dict of str, :class:`InterfaceDefinition`
        """

    @object_dict_field(ArtifactAssignment)
    def artifacts(self):
        """
        An optional list of named artifact definitions for the Node Type.

        :rtype: dict of str, :class:`ArtifactAssignment`
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_parent_presentation(context, self, convert_shorthand_to_full_type_name,
                                       'node_types')

    @cachedmethod
    def _is_descendant(self, context, the_type):
        if the_type is None:
            return False
        elif the_type._name == self._name:
            return True
        return self._is_descendant(context, the_type._get_parent(context))

    @cachedmethod
    def _get_properties(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'properties'))

    @cachedmethod
    def _get_attributes(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'attributes'))

    @cachedmethod
    def _get_requirements(self, context):
        return FrozenList(get_inherited_requirement_definitions(context, self))

    @cachedmethod
    def _get_capabilities(self, context):
        return FrozenDict(get_inherited_capability_definitions(context, self))

    @cachedmethod
    def _get_interfaces(self, context):
        return FrozenDict(get_inherited_interface_definitions(context, self, 'node type'))

    @cachedmethod
    def _get_artifacts(self, context):
        return FrozenDict(get_inherited_artifact_definitions(context, self))

    def _validate(self, context):
        super(NodeType, self)._validate(context)
        self._get_properties(context)
        self._get_attributes(context)
        self._get_requirements(context)
        self._get_capabilities(context)
        self._get_interfaces(context)
        self._get_artifacts(context)

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'version',
            'derived_from',
            'properties',
            'attributes',
            'interfaces',
            'artifacts',
            'requirements',
            'capabilities'))

@has_fields
@implements_specification('3.6.10', 'tosca-simple-1.0')
class GroupType(ExtensiblePresentation):
    """
    A Group Type defines logical grouping types for nodes, typically for different management
    purposes. Groups can effectively be viewed as logical nodes that are not part of the physical
    deployment topology of an application, yet can have capabilities and the ability to attach
    policies and interfaces that can be applied (depending on the group type) to its member nodes.

    Conceptually, group definitions allow the creation of logical "membership" relationships to
    nodes in a service template that are not a part of the application's explicit requirement
    dependencies in the topology template (i.e. those required to actually get the application
    deployed and running). Instead, such logical membership allows for the introduction of things
    such as group management and uniform application of policies (i.e., requirements that are also
    not bound to the application itself) to the group's members.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ENTITY_GROUP_TYPE>`__
    """

    @field_validator(derived_from_validator(convert_shorthand_to_full_type_name, 'group_types'))
    @primitive_field(str)
    def derived_from(self):
        """
        An optional parent Group Type name the Group Type derives from.

        :rtype: str
        """

    @object_field(Version)
    def version(self):
        """
        An optional version for the Group Type definition.

        :rtype: :class:`Version`
        """

    @object_field(Description)
    def description(self):
        """
        The optional description for the Group Type.

        :rtype: :class:`Description`
        """

    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        An optional list of property definitions for the Group Type.

        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @field_validator(list_type_validator('node type', convert_shorthand_to_full_type_name,
                                         'node_types'))
    @primitive_list_field(str)
    def members(self):
        """
        An optional list of one or more names of Node Types that are valid (allowed) as members of
        the Group Type.

        Note: This can be viewed by TOSCA Orchestrators as an implied relationship from the listed
        members nodes to the group, but one that does not have operational lifecycle considerations.
        For example, if we were to name this as an explicit Relationship Type we might call this
        "MemberOf" (group).

        :rtype: list of str
        """

    @object_dict_field(InterfaceDefinition)
    def interfaces(self):
        """
        An optional list of interface definitions supported by the Group Type.

        :rtype: dict of str, :class:`InterfaceDefinition`
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_parent_presentation(context, self, convert_shorthand_to_full_type_name,
                                       'group_types')

    @cachedmethod
    def _is_descendant(self, context, the_type):
        if the_type is None:
            return False
        elif the_type._name == self._name:
            return True
        return self._is_descendant(context, the_type._get_parent(context))

    @cachedmethod
    def _get_properties(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'properties'))

    @cachedmethod
    def _get_interfaces(self, context):
        return FrozenDict(get_inherited_interface_definitions(context, self, 'group type'))

    def _validate(self, context):
        super(GroupType, self)._validate(context)
        self._get_properties(context)
        self._get_interfaces(context)

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'version',
            'derived_from',
            'members',
            'properties',
            'interfaces'))

@has_fields
@implements_specification('3.6.11', 'tosca-simple-1.0')
class PolicyType(ExtensiblePresentation):
    """
    A Policy Type defines a type of requirement that affects or governs an application or service's
    topology at some stage of its lifecycle, but is not explicitly part of the topology itself
    (i.e., it does not prevent the application or service from being deployed or run if it did not
    exist).

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ENTITY_POLICY_TYPE>`__
    """

    @field_validator(derived_from_validator(convert_shorthand_to_full_type_name, 'policy_types'))
    @primitive_field(str)
    def derived_from(self):
        """
        An optional parent Policy Type name the Policy Type derives from.

        :rtype: str
        """

    @object_field(Version)
    def version(self):
        """
        An optional version for the Policy Type definition.

        :rtype: :class:`Version`
        """

    @object_field(Description)
    def description(self):
        """
        The optional description for the Policy Type.

        :rtype: :class:`Description`
        """

    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        An optional list of property definitions for the Policy Type.

        :rtype: :class:`PropertyDefinition`
        """

    @field_validator(list_node_type_or_group_type_validator)
    @primitive_list_field(str)
    def targets(self):
        """
        An optional list of valid Node Types or Group Types the Policy Type can be applied to.

        Note: This can be viewed by TOSCA Orchestrators as an implied relationship to the target
        nodes, but one that does not have operational lifecycle considerations. For example, if we
        were to name this as an explicit Relationship Type we might call this "AppliesTo" (node or
        group).

        :rtype: list of str
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_parent_presentation(context, self, convert_shorthand_to_full_type_name,
                                       'policy_types')

    @cachedmethod
    def _get_properties(self, context):
        return FrozenDict(get_inherited_parameter_definitions(context, self, 'properties'))

    @cachedmethod
    def _get_targets(self, context):
        node_types, group_types = get_inherited_targets(context, self)
        return FrozenList(node_types), FrozenList(group_types)

    def _validate(self, context):
        super(PolicyType, self)._validate(context)
        self._get_properties(context)

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'version',
            'derived_from',
            'targets',
            'properties'))
