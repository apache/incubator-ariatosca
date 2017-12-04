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
from aria.utils.console import puts
from aria.utils.formatting import as_raw
from aria.parser import implements_specification
from aria.parser.presentation import (AsIsPresentation, has_fields, allow_unknown_fields,
                                      short_form_field, primitive_field, primitive_list_field,
                                      primitive_dict_unknown_fields, object_field,
                                      object_list_field, object_dict_field, field_getter,
                                      field_validator, type_validator, not_negative_validator)

from .data_types import Version
from .modeling.data_types import (get_data_type, get_data_type_value, get_property_constraints,
                                  apply_constraint_to_value)
from .modeling.substitution_mappings import (validate_substitution_mappings_requirement,
                                             validate_substitution_mappings_capability)
from .presentation.extensible import ExtensiblePresentation
from .presentation.field_getters import data_type_class_getter
from .presentation.field_validators import (constraint_clause_field_validator,
                                            constraint_clause_in_range_validator,
                                            constraint_clause_valid_values_validator,
                                            constraint_clause_pattern_validator,
                                            data_type_validator)
from .presentation.types import (convert_name_to_full_type_name, get_type_by_name)



@implements_specification('3.5.1', 'tosca-simple-1.0')
class Description(AsIsPresentation):
    """
    Human-readable description.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_DESCRIPTION>`__
    """

    def __init__(self, name=None, raw=None, container=None, cls=None):                              # pylint: disable=unused-argument
        super(Description, self).__init__(name, raw, container, cls=unicode)

    def _dump(self, context):
        value = as_raw(self.value)
        puts(context.style.meta_style(value))


@allow_unknown_fields
@has_fields
@implements_specification('3.9.3.2', 'tosca-simple-1.0')
class MetaData(ExtensiblePresentation):
    """
    Meta data.
    """

    @primitive_field(str)
    @implements_specification('3.9.3.3', 'tosca-simple-1.0')
    def template_name(self):
        """
        This optional metadata keyname can be used to declare the name of service template as a
        single-line string value.
        """

    @primitive_field(str)
    @implements_specification('3.9.3.4', 'tosca-simple-1.0')
    def template_author(self):
        """
        This optional metadata keyname can be used to declare the author(s) of the service template
        as a single-line string value.
        """

    @field_getter(data_type_class_getter(Version, allow_null=True))
    @primitive_field(str)
    @implements_specification('3.9.3.5', 'tosca-simple-1.0')
    def template_version(self):
        """
        This optional metadata keyname can be used to declare a domain specific version of the
        service template as a single-line string value.
        """

    @primitive_dict_unknown_fields(str)
    def custom(self):
        """
        :type: dict
        """


@short_form_field('url')
@has_fields
@implements_specification('3.5.5', 'tosca-simple-1.0')
class Repository(ExtensiblePresentation):
    """
    A repository definition defines a named external repository which contains deployment and
    implementation artifacts that are referenced within the TOSCA Service Template.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_REPOSITORY_DEF>`__
    """

    @object_field(Description)
    def description(self):
        """
        The optional description for the repository.

        :type: :class:`Description`
        """

    @primitive_field(str, required=True)
    def url(self):
        """
        The required URL or network address used to access the repository.

        :type: :obj:`basestring`
        """

    @primitive_field()
    def credential(self):
        """
        The optional Credential used to authorize access to the repository.

        :type: tosca.datatypes.Credential
        """

    @cachedmethod
    def _get_credential(self, context):
        return get_data_type_value(context, self, 'credential', 'tosca.datatypes.Credential')

    def _validate(self, context):
        super(Repository, self)._validate(context)
        self._get_credential(context)


@short_form_field('file')
@has_fields
@implements_specification('3.5.7', 'tosca-simple-1.0')
class Import(ExtensiblePresentation):
    """
    An import definition is used within a TOSCA Service Template to locate and uniquely name another
    TOSCA Service Template file which has type and template definitions to be imported (included)
    and referenced within another Service Template.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_IMPORT_DEF>`__
    """

    @primitive_field(str, required=True)
    def file(self):
        """
        The required symbolic name for the imported file.

        :type: :obj:`basestring`
        """

    @primitive_field(str)
    def repository(self):
        """
        The optional symbolic name of the repository definition where the imported file can be found
        as a string.

        :type: :obj:`basestring`
        """

    @primitive_field(str)
    def namespace_uri(self):
        """
        The optional namespace URI to that will be applied to type definitions found within the
        imported file as a string.

        :type: :obj:`basestring`
        """

    @primitive_field(str)
    def namespace_prefix(self):
        """
        The optional namespace prefix (alias) that will be used to indicate the namespace_uri when
        forming a qualified name (i.e., qname) when referencing type definitions from the imported
        file.

        :type: :obj:`basestring`
        """


@has_fields
@implements_specification('3.5.2-1', 'tosca-simple-1.0')
class ConstraintClause(ExtensiblePresentation):
    """
    A constraint clause defines an operation along with one or more compatible values that can be
    used to define a constraint on a property or parameter's allowed values when it is defined in a
    TOSCA Service Template or one of its entities.

    See the `TOSCA Simple Profile v1.0 cos01 specification <http://docs.oasis-open.org/tosca
    /TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html
    #DEFN_ELEMENT_CONSTRAINTS_CLAUSE>`__
    """

    @field_validator(constraint_clause_field_validator)
    @primitive_field()
    def equal(self):
        """
        Constrains a property or parameter to a value equal to ('=') the value declared.
        """

    @field_validator(constraint_clause_field_validator)
    @primitive_field()
    def greater_than(self):
        """
        Constrains a property or parameter to a value greater than ('>') the value declared.
        """

    @field_validator(constraint_clause_field_validator)
    @primitive_field()
    def greater_or_equal(self):
        """
        Constrains a property or parameter to a value greater than or equal to ('>=') the value
        declared.
        """

    @field_validator(constraint_clause_field_validator)
    @primitive_field()
    def less_than(self):
        """
        Constrains a property or parameter to a value less than ('<') the value declared.
        """

    @field_validator(constraint_clause_field_validator)
    @primitive_field()
    def less_or_equal(self):
        """
        Constrains a property or parameter to a value less than or equal to ('<=') the value
        declared.
        """

    @field_validator(constraint_clause_in_range_validator)
    @primitive_list_field()
    def in_range(self):
        """
        Constrains a property or parameter to a value in range of (inclusive) the two values
        declared.

        Note: subclasses or templates of types that declare a property with the ``in_range``
        constraint MAY only further restrict the range specified by the parent type.
        """

    @field_validator(constraint_clause_valid_values_validator)
    @primitive_list_field()
    def valid_values(self):
        """
        Constrains a property or parameter to a value that is in the list of declared values.
        """

    @field_validator(not_negative_validator)
    @primitive_field(int)
    def length(self):
        """
        Constrains the property or parameter to a value of a given length.
        """

    @field_validator(not_negative_validator)
    @primitive_field(int)
    def min_length(self):
        """
        Constrains the property or parameter to a value to a minimum length.
        """

    @field_validator(not_negative_validator)
    @primitive_field(int)
    def max_length(self):
        """
        Constrains the property or parameter to a value to a maximum length.
        """

    @field_validator(constraint_clause_pattern_validator)
    @primitive_field(str)
    def pattern(self):
        """
        Constrains the property or parameter to a value that is allowed by the provided regular
        expression.

        Note: Future drafts of this specification will detail the use of regular expressions and
        reference an appropriate standardized grammar.
        """

    @cachedmethod
    def _get_type(self, context):
        if hasattr(self._container, '_get_type_for_name'):
            # NodeFilter or CapabilityFilter
            return self._container._get_type_for_name(context, self._name)
        elif hasattr(self._container, '_get_type'):
            # Properties
            return self._container._get_type(context)
        else:
            # DataType (the DataType itself is our type)
            return self._container

    def _apply_to_value(self, context, presentation, value):
        return apply_constraint_to_value(context, presentation, self, value)


@short_form_field('type')
@has_fields
class EntrySchema(ExtensiblePresentation):
    """
    ARIA NOTE: The specification does not properly explain this type, however it is implied by
    examples.
    """

    @field_validator(data_type_validator('entry schema data type'))
    @primitive_field(str, required=True)
    def type(self):
        """
        :type: :obj:`basestring`
        """

    @object_field(Description)
    def description(self):
        """
        :type: :class:`Description`
        """

    @object_list_field(ConstraintClause)
    def constraints(self):
        """
        :type: list of (str, :class:`ConstraintClause`)
        """

    @cachedmethod
    def _get_type(self, context):
        return get_data_type(context, self, 'type')

    @cachedmethod
    def _get_constraints(self, context):
        return get_property_constraints(context, self)


@short_form_field('primary')
@has_fields
class OperationImplementation(ExtensiblePresentation):
    """
    Operation implementation.
    """

    @primitive_field(str)
    def primary(self):
        """
        The optional implementation artifact name (i.e., the primary script file name within a
        TOSCA CSAR file).

        :type: :obj:`basestring`
        """

    @primitive_list_field(str)
    def dependencies(self):
        """
        The optional ordered list of one or more dependent or secondary implementation artifact name
        which are referenced by the primary implementation artifact (e.g., a library the script
        installs or a secondary script).

        :type: [:obj:`basestring`]
        """


class SubstitutionMappingsRequirement(AsIsPresentation):
    """
    Substitution mapping for requirement.
    """

    @property
    @cachedmethod
    def node_template(self):
        return str(self._raw[0])

    @property
    @cachedmethod
    def requirement(self):
        return str(self._raw[1])

    def _validate(self, context):
        super(SubstitutionMappingsRequirement, self)._validate(context)
        validate_substitution_mappings_requirement(context, self)


class SubstitutionMappingsCapability(AsIsPresentation):
    """
    Substitution mapping for capability.
    """

    @property
    @cachedmethod
    def node_template(self):
        return str(self._raw[0])

    @property
    @cachedmethod
    def capability(self):
        return str(self._raw[1])

    def _validate(self, context):
        super(SubstitutionMappingsCapability, self)._validate(context)
        validate_substitution_mappings_capability(context, self)


@has_fields
@implements_specification('2.10', 'tosca-simple-1.0')
class SubstitutionMappings(ExtensiblePresentation):
    """
    Substitution mappings.
    """

    @field_validator(type_validator('node type', convert_name_to_full_type_name, 'node_types'))
    @primitive_field(str, required=True)
    def node_type(self):
        """
        :type: :obj:`basestring`
        """

    @object_dict_field(SubstitutionMappingsRequirement)
    def requirements(self):
        """
        :type: {:obj:`basestring`: :class:`SubstitutionMappingsRequirement`}
        """

    @object_dict_field(SubstitutionMappingsCapability)
    def capabilities(self):
        """
        :type: {:obj:`basestring`: :class:`SubstitutionMappingsCapability`}
        """

    @cachedmethod
    def _get_type(self, context):
        return get_type_by_name(context, self.node_type, 'node_types')

    def _validate(self, context):
        super(SubstitutionMappings, self)._validate(context)
        self._get_type(context)

    def _dump(self, context):
        self._dump_content(context, (
            'node_type',
            'requirements',
            'capabilities'))
