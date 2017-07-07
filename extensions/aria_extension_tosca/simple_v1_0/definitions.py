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
from aria.parser.presentation import (has_fields, short_form_field, allow_unknown_fields,
                                      primitive_field, primitive_list_field, object_field,
                                      object_list_field, object_dict_field,
                                      object_dict_unknown_fields, field_validator,
                                      field_getter, type_validator, list_type_validator)

from .data_types import Range
from .misc import (Description, ConstraintClause, OperationImplementation, EntrySchema)
from .presentation.extensible import ExtensiblePresentation
from .presentation.field_getters import data_type_class_getter
from .presentation.field_validators import (data_type_validator, data_value_validator,
                                            entry_schema_validator)
from .presentation.types import (convert_shorthand_typequalified_to_full_type_name,
                                 get_type_by_full_or_shorthand_or_typequalified_name)
from .modeling.data_types import get_data_type, get_property_constraints
from .modeling.interfaces import (get_and_override_input_definitions_from_type,
                                  get_and_override_operation_definitions_from_type)

@has_fields
@implements_specification('3.5.8', 'tosca-simple-1.0')
class PropertyDefinition(ExtensiblePresentation):
    """
    A property definition defines a named, typed value and related data that can be associated with
    an entity defined in this specification (e.g., Node Types, Relationship Types, Capability Types,
    etc.). Properties are used by template authors to provide input values to TOSCA entities which
    indicate their "desired state" when they are instantiated. The value of a property can be
    retrieved using the ``get_property`` function within TOSCA Service Templates.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_PROPERTY_DEFN>`__
    """

    @field_validator(data_type_validator())
    @primitive_field(str, required=True)
    def type(self):
        """
        The required data type for the property.

        :type: :obj:`basestring`
        """

    @object_field(Description)
    def description(self):
        """
        The optional description for the property.

        :type: :class:`Description`
        """

    @primitive_field(bool, default=True)
    def required(self):
        """
        An optional key that declares a property as required (true) or not (false).

        :type: bool
        """

    @field_validator(data_value_validator)
    @primitive_field()
    def default(self):
        """
        An optional key that may provide a value to be used as a default if not provided by another
        means.

        :type: :obj:`basestring`
        """

    @primitive_field(str, default='supported', allowed=('supported', 'unsupported', 'experimental',
                                                        'deprecated'))
    @implements_specification(section='3.5.8.3', spec='tosca-simple-1.0')
    def status(self):
        """
        The optional status of the property relative to the specification or implementation.

        :type: :obj:`basestring`
        """

    @object_list_field(ConstraintClause)
    def constraints(self):
        """
        The optional list of sequenced constraint clauses for the property.

        :type: list of (str, :class:`ConstraintClause`)
        """

    @field_validator(entry_schema_validator)
    @object_field(EntrySchema)
    def entry_schema(self):
        """
        The optional key that is used to declare the name of the Datatype definition for entries of
        set types such as the TOSCA list or map.

        :type: :obj:`basestring`
        """

    @cachedmethod
    def _get_type(self, context):
        return get_data_type(context, self, 'type')

    @cachedmethod
    def _get_constraints(self, context):
        return get_property_constraints(context, self)

@has_fields
@implements_specification('3.5.10', 'tosca-simple-1.0')
class AttributeDefinition(ExtensiblePresentation):
    """
    An attribute definition defines a named, typed value that can be associated with an entity
    defined in this specification (e.g., a Node, Relationship or Capability Type). Specifically, it
    is used to expose the "actual state" of some property of a TOSCA entity after it has been
    deployed and instantiated (as set by the TOSCA orchestrator). Attribute values can be retrieved
    via the ``get_attribute`` function from the instance model and used as values to other
    entities within TOSCA Service Templates.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_ATTRIBUTE_DEFN>`__
    """

    @field_validator(data_type_validator())
    @primitive_field(str, required=True)
    def type(self):
        """
        The required data type for the attribute.

        :type: :obj:`basestring`
        """

    @object_field(Description)
    def description(self):
        """
        The optional description for the attribute.

        :type: :class:`Description`
        """

    @field_validator(data_value_validator)
    @primitive_field()
    def default(self):
        """
        An optional key that may provide a value to be used as a default if not provided by another
        means.

        This value SHALL be type compatible with the type declared by the property definition's type
        keyname.

        :type: :obj:`basestring`
        """

    @primitive_field(str, default='supported', allowed=('supported', 'unsupported', 'experimental',
                                                        'deprecated'))
    def status(self):
        """
        The optional status of the attribute relative to the specification or implementation.

        :type: :obj:`basestring`
        """

    @field_validator(entry_schema_validator)
    @object_field(EntrySchema)
    def entry_schema(self):
        """
        The optional key that is used to declare the name of the Datatype definition for entries of
        set types such as the TOSCA list or map.

        :type: :obj:`basestring`
        """

    @cachedmethod
    def _get_type(self, context):
        return get_data_type(context, self, 'type')

@has_fields
@implements_specification('3.5.12', 'tosca-simple-1.0')
class ParameterDefinition(PropertyDefinition):
    """
    A parameter definition is essentially a TOSCA property definition; however, it also allows a
    value to be assigned to it (as for a TOSCA property assignment). In addition, in the case of
    output parameters, it can optionally inherit the data type of the value assigned to it rather
    than have an explicit data type defined for it.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_PARAMETER_DEF>`__
    """

    @field_validator(data_type_validator())
    @primitive_field(str)
    def type(self):
        """
        The required data type for the parameter.

        Note: This keyname is required for a TOSCA Property definition, but is not for a TOSCA
        Parameter definition.

        :type: :obj:`basestring`
        """

    @field_validator(data_value_validator)
    @primitive_field()
    def value(self):
        """
        The type-compatible value to assign to the named parameter. Parameter values may be provided
        as the result from the evaluation of an expression or a function.
        """

@short_form_field('implementation')
@has_fields
@implements_specification('3.5.13-1', 'tosca-simple-1.0')
class OperationDefinition(ExtensiblePresentation):
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

    @object_dict_field(PropertyDefinition)
    def inputs(self):
        """
        The optional list of input property definitions available to all defined operations for
        interface definitions that are within TOSCA Node or Relationship Type definitions. This
        includes when interface definitions are included as part of a Requirement definition in a
        Node Type.

        :type: {:obj:`basestring`: :class:`PropertyDefinition`}
        """

@allow_unknown_fields
@has_fields
@implements_specification('3.5.14-1', 'tosca-simple-1.0')
class InterfaceDefinition(ExtensiblePresentation):
    """
    An interface definition defines a named interface that can be associated with a Node or
    Relationship Type.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_INTERFACE_DEF>`__
    """

    @field_validator(type_validator('interface type',
                                    convert_shorthand_typequalified_to_full_type_name,
                                    'interface_types'))
    @primitive_field(str)
    def type(self):
        """
        ARIA NOTE: This field is not mentioned in the spec, but is implied.

        :type: :obj:`basestring`
        """

    @object_dict_field(PropertyDefinition)
    def inputs(self):
        """
        The optional list of input property definitions available to all defined operations for
        interface definitions that are within TOSCA Node or Relationship Type definitions. This
        includes when interface definitions are included as part of a Requirement definition in a
        Node Type.

        :type: {:obj:`basestring`: :class:`PropertyDefinition`}
        """

    @object_dict_unknown_fields(OperationDefinition)
    def operations(self):
        """
        :type: {:obj:`basestring`: :class:`OperationDefinition`}
        """

    @cachedmethod
    def _get_type(self, context):
        return get_type_by_full_or_shorthand_or_typequalified_name(context,
                                                                   self.type, 'interface_types')

    @cachedmethod
    def _get_inputs(self, context):
        return FrozenDict(get_and_override_input_definitions_from_type(context, self))

    @cachedmethod
    def _get_operations(self, context):
        return FrozenDict(get_and_override_operation_definitions_from_type(context, self))

    def _validate(self, context):
        super(InterfaceDefinition, self)._validate(context)
        if self.operations:
            for operation in self.operations.itervalues(): # pylint: disable=no-member
                operation._validate(context)

@short_form_field('type')
@has_fields
class RelationshipDefinition(ExtensiblePresentation):
    """
    Relationship definition.
    """

    @field_validator(type_validator('relationship type',
                                    convert_shorthand_typequalified_to_full_type_name,
                                    'relationship_types'))
    @primitive_field(str, required=True)
    def type(self):
        """
        The optional reserved keyname used to provide the name of the Relationship Type for the
        requirement definition's relationship keyname.

        :type: :obj:`basestring`
        """

    @object_dict_field(InterfaceDefinition)
    def interfaces(self):
        """
        The optional reserved keyname used to reference declared (named) interface definitions of
        the corresponding Relationship Type in order to declare additional Property definitions for
        these interfaces or operations of these interfaces.

        :type: list of :class:`InterfaceDefinition`
        """

    @cachedmethod
    def _get_type(self, context):
        return get_type_by_full_or_shorthand_or_typequalified_name(context,
                                                                   self.type, 'relationship_types')

@short_form_field('capability')
@has_fields
@implements_specification('3.6.2', 'tosca-simple-1.0')
class RequirementDefinition(ExtensiblePresentation):
    """
    The Requirement definition describes a named requirement (dependencies) of a TOSCA Node Type or
    Node template which needs to be fulfilled by a matching Capability definition declared by
    another TOSCA modelable entity. The requirement definition may itself include the specific name
    of the fulfilling entity (explicitly) or provide an abstract type, along with additional
    filtering characteristics, that a TOSCA orchestrator can use to fulfill the capability at
    runtime (implicitly).

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_REQUIREMENT_DEF>`__
    """

    @field_validator(type_validator('capability type',
                                    convert_shorthand_typequalified_to_full_type_name,
                                    'capability_types'))
    @primitive_field(str, required=True)
    def capability(self):
        """
        The required reserved keyname used that can be used to provide the name of a valid
        Capability Type that can fulfill the requirement.

        :type: :obj:`basestring`
        """

    @field_validator(type_validator('node type',
                                    convert_shorthand_typequalified_to_full_type_name,
                                    'node_types'))
    @primitive_field(str)
    def node(self):
        """
        The optional reserved keyname used to provide the name of a valid Node Type that contains
        the capability definition that can be used to fulfill the requirement.

        :type: :obj:`basestring`
        """

    @object_field(RelationshipDefinition)
    def relationship(self):
        """
        The optional reserved keyname used to provide the name of a valid Relationship Type to
        construct when fulfilling the requirement.

        :type: :class:`RelationshipDefinition`
        """

    @field_getter(data_type_class_getter(Range))
    @primitive_field()
    def occurrences(self):
        """
        The optional minimum and maximum occurrences for the requirement.

        Note: the keyword UNBOUNDED is also supported to represent any positive integer.

        :type: :class:`Range`
        """

    @cachedmethod
    def _get_capability_type(self, context):
        return get_type_by_full_or_shorthand_or_typequalified_name(context,
                                                                   self.capability,
                                                                   'capability_types')

    @cachedmethod
    def _get_node_type(self, context):
        return context.presentation.get_from_dict('service_template', 'node_types', self.node)

@short_form_field('type')
@has_fields
@implements_specification('3.6.1', 'tosca-simple-1.0')
class CapabilityDefinition(ExtensiblePresentation):
    """
    A capability definition defines a named, typed set of data that can be associated with Node Type
    or Node Template to describe a transparent capability or feature of the software component the
    node describes.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_CAPABILITY_DEFN>`__
    """

    @field_validator(type_validator('capability type',
                                    convert_shorthand_typequalified_to_full_type_name,
                                    'capability_types'))
    @primitive_field(str, required=True)
    def type(self):
        """
        The required name of the Capability Type the capability definition is based upon.

        :type: :obj:`basestring`
        """

    @object_field(Description)
    def description(self):
        """
        The optional description of the Capability definition.

        :type: :class:`Description`
        """

    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        An optional list of property definitions for the Capability definition.

        :type: {:obj:`basestring`: :class:`PropertyDefinition`}
        """

    @object_dict_field(AttributeDefinition)
    def attributes(self):
        """
        An optional list of attribute definitions for the Capability definition.

        :type: {:obj:`basestring`: :class:`AttributeDefinition`}
        """

    @field_validator(list_type_validator('node type',
                                         convert_shorthand_typequalified_to_full_type_name,
                                         'node_types'))
    @primitive_list_field(str)
    def valid_source_types(self):
        """
        An optional list of one or more valid names of Node Types that are supported as valid
        sources of any relationship established to the declared Capability Type.

        :type: [:obj:`basestring`]
        """

    @field_getter(data_type_class_getter(Range))
    @primitive_field()
    def occurrences(self):
        """
        The optional minimum and maximum occurrences for the capability. By default, an exported
        Capability should allow at least one relationship to be formed with it with a maximum of
        ``UNBOUNDED`` relationships.

        Note: the keyword ``UNBOUNDED`` is also supported to represent any positive integer.

        ARIA NOTE: The spec seems wrong here: the implied default should be ``[0,UNBOUNDED]``, not
        ``[1,UNBOUNDED]``, otherwise it would imply that at 1 least one relationship *must* be
        formed.

        :type: :class:`Range`
        """

    @cachedmethod
    def _get_type(self, context):
        return get_type_by_full_or_shorthand_or_typequalified_name(context,
                                                                   self.type, 'capability_types')

    @cachedmethod
    def _get_parent(self, context):
        container_parent = self._container._get_parent(context)
        container_parent_capabilities = container_parent._get_capabilities(context) \
            if container_parent is not None else None
        return container_parent_capabilities.get(self._name) \
            if container_parent_capabilities is not None else None
