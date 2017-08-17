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

"""
ARIA modeling service template module
"""

# pylint: disable=too-many-lines, no-self-argument, no-member, abstract-method

from __future__ import absolute_import  # so we can import standard 'types'

from sqlalchemy import (
    Column,
    Text,
    Integer,
    Boolean,
    DateTime,
    PickleType
)
from sqlalchemy.ext.declarative import declared_attr

from ..utils import (collections, formatting)
from .mixins import TemplateModelMixin
from . import (
    relationship,
    types as modeling_types
)


class ServiceTemplateBase(TemplateModelMixin):
    """
    Template for creating :class:`Service` instances.

    Usually created by various DSL parsers, such as ARIA's TOSCA extension. However, it can also be
    created programmatically.
    """

    __tablename__ = 'service_template'

    __private_fields__ = ('substitution_template_fk',
                          'node_type_fk',
                          'group_type_fk',
                          'policy_type_fk',
                          'relationship_type_fk',
                          'capability_type_fk',
                          'interface_type_fk',
                          'artifact_type_fk')

    # region one_to_one relationships

    @declared_attr
    def substitution_template(cls):
        """
        Exposes an entire service as a single node.

        :type: :class:`SubstitutionTemplate`
        """
        return relationship.one_to_one(
            cls, 'substitution_template', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def node_types(cls):
        """
        Base for the node type hierarchy,

        :type: :class:`Type`
        """
        return relationship.one_to_one(
            cls, 'type', fk='node_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def group_types(cls):
        """
        Base for the group type hierarchy,

        :type: :class:`Type`
        """
        return relationship.one_to_one(
            cls, 'type', fk='group_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def policy_types(cls):
        """
        Base for the policy type hierarchy,

        :type: :class:`Type`
        """
        return relationship.one_to_one(
            cls, 'type', fk='policy_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def relationship_types(cls):
        """
        Base for the relationship type hierarchy,

        :type: :class:`Type`
        """
        return relationship.one_to_one(
            cls, 'type', fk='relationship_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def capability_types(cls):
        """
        Base for the capability type hierarchy,

        :type: :class:`Type`
        """
        return relationship.one_to_one(
            cls, 'type', fk='capability_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def interface_types(cls):
        """
        Base for the interface type hierarchy,

        :type: :class:`Type`
        """
        return relationship.one_to_one(
            cls, 'type', fk='interface_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def artifact_types(cls):
        """
        Base for the artifact type hierarchy,

        :type: :class:`Type`
        """
        return relationship.one_to_one(
            cls, 'type', fk='artifact_type_fk', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region one_to_many relationships

    @declared_attr
    def services(cls):
        """
        Instantiated services.

        :type: [:class:`Service`]
        """
        return relationship.one_to_many(cls, 'service', dict_key='name')

    @declared_attr
    def node_templates(cls):
        """
        Templates for creating nodes.

        :type: {:obj:`basestring`, :class:`NodeTemplate`}
        """
        return relationship.one_to_many(cls, 'node_template', dict_key='name')

    @declared_attr
    def group_templates(cls):
        """
        Templates for creating groups.

        :type: {:obj:`basestring`, :class:`GroupTemplate`}
        """
        return relationship.one_to_many(cls, 'group_template', dict_key='name')

    @declared_attr
    def policy_templates(cls):
        """
        Templates for creating policies.

        :type: {:obj:`basestring`, :class:`PolicyTemplate`}
        """
        return relationship.one_to_many(cls, 'policy_template', dict_key='name')

    @declared_attr
    def workflow_templates(cls):
        """
        Templates for creating workflows.

        :type: {:obj:`basestring`, :class:`OperationTemplate`}
        """
        return relationship.one_to_many(cls, 'operation_template', dict_key='name')

    @declared_attr
    def outputs(cls):
        """
        Declarations for output parameters are filled in after service installation.

        :type: {:obj:`basestring`: :class:`Output`}
        """
        return relationship.one_to_many(cls, 'output', dict_key='name')

    @declared_attr
    def inputs(cls):
        """
        Declarations for externally provided parameters.

        :type: {:obj:`basestring`: :class:`Input`}
        """
        return relationship.one_to_many(cls, 'input', dict_key='name')

    @declared_attr
    def plugin_specifications(cls):
        """
        Required plugins for instantiated services.

        :type: {:obj:`basestring`: :class:`PluginSpecification`}
        """
        return relationship.one_to_many(cls, 'plugin_specification', dict_key='name')

    # endregion

    # region many_to_many relationships

    @declared_attr
    def meta_data(cls):
        """
        Associated metadata.

        :type: {:obj:`basestring`: :class:`Metadata`}
        """
        # Warning! We cannot use the attr name "metadata" because it's used by SQLAlchemy!
        return relationship.many_to_many(cls, 'metadata', dict_key='name')

    # endregion

    # region foreign keys

    @declared_attr
    def substitution_template_fk(cls):
        """For ServiceTemplate one-to-one to SubstitutionTemplate"""
        return relationship.foreign_key('substitution_template', nullable=True)

    @declared_attr
    def node_type_fk(cls):
        """For ServiceTemplate one-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    @declared_attr
    def group_type_fk(cls):
        """For ServiceTemplate one-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    @declared_attr
    def policy_type_fk(cls):
        """For ServiceTemplate one-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    @declared_attr
    def relationship_type_fk(cls):
        """For ServiceTemplate one-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    @declared_attr
    def capability_type_fk(cls):
        """For ServiceTemplate one-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    @declared_attr
    def interface_type_fk(cls):
        """For ServiceTemplate one-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    @declared_attr
    def artifact_type_fk(cls):
        """For ServiceTemplate one-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    # endregion

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    main_file_name = Column(Text, doc="""
    Filename of CSAR or YAML file from which this service template was parsed.
    
    :type: :obj:`basestring`
    """)

    created_at = Column(DateTime, nullable=False, index=True, doc="""
    Creation timestamp.

    :type: :class:`~datetime.datetime`
    """)

    updated_at = Column(DateTime, doc="""
    Update timestamp.

    :type: :class:`~datetime.datetime`
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('description', self.description),
            ('metadata', formatting.as_raw_dict(self.meta_data)),
            ('node_templates', formatting.as_raw_list(self.node_templates)),
            ('group_templates', formatting.as_raw_list(self.group_templates)),
            ('policy_templates', formatting.as_raw_list(self.policy_templates)),
            ('substitution_template', formatting.as_raw(self.substitution_template)),
            ('inputs', formatting.as_raw_dict(self.inputs)),
            ('outputs', formatting.as_raw_dict(self.outputs)),
            ('workflow_templates', formatting.as_raw_list(self.workflow_templates))))

    @property
    def types_as_raw(self):
        return collections.OrderedDict((
            ('node_types', formatting.as_raw(self.node_types)),
            ('group_types', formatting.as_raw(self.group_types)),
            ('policy_types', formatting.as_raw(self.policy_types)),
            ('relationship_types', formatting.as_raw(self.relationship_types)),
            ('capability_types', formatting.as_raw(self.capability_types)),
            ('interface_types', formatting.as_raw(self.interface_types)),
            ('artifact_types', formatting.as_raw(self.artifact_types))))


class NodeTemplateBase(TemplateModelMixin):
    """
    Template for creating zero or more :class:`Node` instances, which are typed vertices in the
    service topology.
    """

    __tablename__ = 'node_template'

    __private_fields__ = ('type_fk',
                          'service_template_fk')

    # region one_to_many relationships

    @declared_attr
    def nodes(cls):
        """
        Instantiated nodes.

        :type: [:class:`Node`]
        """
        return relationship.one_to_many(cls, 'node')

    @declared_attr
    def interface_templates(cls):
        """
        Associated interface templates.

        :type: {:obj:`basestring`: :class:`InterfaceTemplate`}
        """
        return relationship.one_to_many(cls, 'interface_template', dict_key='name')

    @declared_attr
    def artifact_templates(cls):
        """
        Associated artifacts.

        :type: {:obj:`basestring`: :class:`ArtifactTemplate`}
        """
        return relationship.one_to_many(cls, 'artifact_template', dict_key='name')

    @declared_attr
    def capability_templates(cls):
        """
        Associated exposed capability templates.

        :type: {:obj:`basestring`: :class:`CapabilityTemplate`}
        """
        return relationship.one_to_many(cls, 'capability_template', dict_key='name')

    @declared_attr
    def requirement_templates(cls):
        """
        Associated potential relationships with other nodes.

        :type: [:class:`RequirementTemplate`]
        """
        return relationship.one_to_many(cls, 'requirement_template', other_fk='node_template_fk')

    @declared_attr
    def properties(cls):
        """
        Declarations for associated immutable parameters.

        :type: {:obj:`basestring`: :class:`Property`}
        """
        return relationship.one_to_many(cls, 'property', dict_key='name')

    @declared_attr
    def attributes(cls):
        """
        Declarations for associated mutable parameters.

        :type: {:obj:`basestring`: :class:`Attribute`}
        """
        return relationship.one_to_many(cls, 'attribute', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def type(cls):
        """
        Node type.

        :type: :class:`Type`
        """
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def service_template(cls):
        """
        Containing service template.

        :type: :class:`ServiceTemplate`
        """
        return relationship.many_to_one(cls, 'service_template')

    # endregion

    # region association proxies

    @declared_attr
    def service_template_name(cls):
        return relationship.association_proxy('service_template', 'name')

    @declared_attr
    def type_name(cls):
        return relationship.association_proxy('type', 'name')

    # endregion

    # region foreign_keys

    @declared_attr
    def type_fk(cls):
        """For NodeTemplate many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def service_template_fk(cls):
        """For ServiceTemplate one-to-many to NodeTemplate"""
        return relationship.foreign_key('service_template')

    # endregion

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    directives = Column(PickleType, doc="""
    Directives that apply to this node template.

    :type: [:obj:`basestring`]
    """)

    default_instances = Column(Integer, default=1, doc="""
    Default number nodes that will appear in the service.

    :type: :obj:`int`
    """)

    min_instances = Column(Integer, default=0, doc="""
    Minimum number nodes that will appear in the service.

    :type: :obj:`int`
    """)

    max_instances = Column(Integer, default=None, doc="""
    Maximum number nodes that will appear in the service.

    :type: :obj:`int`
    """)

    target_node_template_constraints = Column(PickleType, doc="""
    Constraints for filtering relationship targets.

    :type: [:class:`NodeTemplateConstraint`]
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('attributes', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates)),
            ('artifact_templates', formatting.as_raw_list(self.artifact_templates)),
            ('capability_templates', formatting.as_raw_list(self.capability_templates)),
            ('requirement_templates', formatting.as_raw_list(self.requirement_templates))))

    def is_target_node_template_valid(self, target_node_template):
        """
        Checks if ``target_node_template`` matches all our ``target_node_template_constraints``.
        """

        if self.target_node_template_constraints:
            for node_template_constraint in self.target_node_template_constraints:
                if not node_template_constraint.matches(self, target_node_template):
                    return False
        return True

    @property
    def _next_index(self):
        """
        Next available node index.

        :returns: node index
        :rtype: int
        """

        max_index = 0
        if self.nodes:
            max_index = max(int(n.name.rsplit('_', 1)[-1]) for n in self.nodes)
        return max_index + 1

    @property
    def _next_name(self):
        """
        Next available node name.

        :returns: node name
        :rtype: basestring
        """

        return '{name}_{index}'.format(name=self.name, index=self._next_index)

    @property
    def scaling(self):
        scaling = {}

        def extract_property(properties, name):
            if name in scaling:
                return
            prop = properties.get(name)
            if (prop is not None) and (prop.type_name == 'integer') and (prop.value is not None):
                scaling[name] = prop.value

        def extract_properties(properties):
            extract_property(properties, 'min_instances')
            extract_property(properties, 'max_instances')
            extract_property(properties, 'default_instances')

        # From our scaling capabilities
        for capability_template in self.capability_templates.itervalues():
            if capability_template.type.role == 'scaling':
                extract_properties(capability_template.properties)

        # From service scaling policies
        for policy_template in self.service_template.policy_templates.itervalues():
            if policy_template.type.role == 'scaling':
                if policy_template.is_for_node_template(self.name):
                    extract_properties(policy_template.properties)

        # Defaults
        scaling.setdefault('min_instances', 0)
        scaling.setdefault('max_instances', 1)
        scaling.setdefault('default_instances', 1)

        return scaling


class GroupTemplateBase(TemplateModelMixin):
    """
    Template for creating a :class:`Group` instance, which is a typed logical container for zero or
    more :class:`Node` instances.
    """

    __tablename__ = 'group_template'

    __private_fields__ = ('type_fk',
                          'service_template_fk')

    # region one_to_many relationships

    @declared_attr
    def groups(cls):
        """
        Instantiated groups.

        :type: [:class:`Group`]
        """
        return relationship.one_to_many(cls, 'group')

    @declared_attr
    def interface_templates(cls):
        """
        Associated interface templates.

        :type: {:obj:`basestring`: :class:`InterfaceTemplate`}
        """
        return relationship.one_to_many(cls, 'interface_template', dict_key='name')

    @declared_attr
    def properties(cls):
        """
        Declarations for associated immutable parameters.

        :type: {:obj:`basestring`: :class:`Property`}
        """
        return relationship.one_to_many(cls, 'property', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        """
        Containing service template.

        :type: :class:`ServiceTemplate`
        """
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def type(cls):
        """
        Group type.

        :type: :class:`Type`
        """
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def node_templates(cls):
        """
        Nodes instantiated by these templates will be members of the group.

        :type: [:class:`NodeTemplate`]
        """
        return relationship.many_to_many(cls, 'node_template')

    # endregion

    # region foreign keys

    @declared_attr
    def type_fk(cls):
        """For GroupTemplate many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def service_template_fk(cls):
        """For ServiceTemplate one-to-many to GroupTemplate"""
        return relationship.foreign_key('service_template')

    # endregion

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates))))

    def contains_node_template(self, name):
        for node_template in self.node_templates:
            if node_template.name == name:
                return True
        return False


class PolicyTemplateBase(TemplateModelMixin):
    """
    Template for creating a :class:`Policy` instance, which is a typed set of orchestration hints
    applied to zero or more :class:`Node` or :class:`Group` instances.
    """

    __tablename__ = 'policy_template'

    __private_fields__ = ('type_fk',
                          'service_template_fk')

    # region one_to_many relationships

    @declared_attr
    def policies(cls):
        """
        Instantiated policies.

        :type: [:class:`Policy`]
        """
        return relationship.one_to_many(cls, 'policy')

    @declared_attr
    def properties(cls):
        """
        Declarations for associated immutable parameters.

        :type: {:obj:`basestring`: :class:`Property`}
        """
        return relationship.one_to_many(cls, 'property', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        """
        Containing service template.

        :type: :class:`ServiceTemplate`
        """
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def type(cls):
        """
        Policy type.

        :type: :class:`Type`
        """
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def node_templates(cls):
        """
        Policy will be enacted on all nodes instantiated by these templates.

        :type: {:obj:`basestring`: :class:`NodeTemplate`}
        """
        return relationship.many_to_many(cls, 'node_template')

    @declared_attr
    def group_templates(cls):
        """
        Policy will be enacted on all nodes in all groups instantiated by these templates.

        :type: {:obj:`basestring`: :class:`GroupTemplate`}
        """
        return relationship.many_to_many(cls, 'group_template')

    # endregion

    # region foreign keys

    @declared_attr
    def type_fk(cls):
        """For PolicyTemplate many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def service_template_fk(cls):
        """For ServiceTemplate one-to-many to PolicyTemplate"""
        return relationship.foreign_key('service_template')

    # endregion

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties))))

    def is_for_node_template(self, name):
        for node_template in self.node_templates:
            if node_template.name == name:
                return True
        for group_template in self.group_templates:
            if group_template.contains_node_template(name):
                return True
        return False

    def is_for_group_template(self, name):
        for group_template in self.group_templates:
            if group_template.name == name:
                return True
        return False


class SubstitutionTemplateBase(TemplateModelMixin):
    """
    Template for creating a :class:`Substitution` instance, which exposes an entire instantiated
    service as a single node.
    """

    __tablename__ = 'substitution_template'

    __private_fields__ = ('node_type_fk',)

    # region one_to_many relationships

    @declared_attr
    def substitutions(cls):
        """
        Instantiated substitutions.

        :type: [:class:`Substitution`]
        """
        return relationship.one_to_many(cls, 'substitution')

    @declared_attr
    def mappings(cls):
        """
        Map requirement and capabilities to exposed node.

        :type: {:obj:`basestring`: :class:`SubstitutionTemplateMapping`}
        """
        return relationship.one_to_many(cls, 'substitution_template_mapping', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def node_type(cls):
        """
        Exposed node type.

        :type: :class:`Type`
        """
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region foreign keys

    @declared_attr
    def node_type_fk(cls):
        """For SubstitutionTemplate many-to-one to Type"""
        return relationship.foreign_key('type')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('node_type_name', self.node_type.name),
            ('mappings', formatting.as_raw_dict(self.mappings))))


class SubstitutionTemplateMappingBase(TemplateModelMixin):
    """
    Used by :class:`SubstitutionTemplate` to map a capability template or a requirement template to
    the exposed node.

    The :attr:`name` field should match the capability or requirement name on the exposed node's
    type.

    Only one of :attr:`capability_template` and :attr:`requirement_template` can be set.
    """

    __tablename__ = 'substitution_template_mapping'

    __private_fields__ = ('substitution_template_fk',
                          'capability_template_fk',
                          'requirement_template_fk')

    # region one_to_one relationships

    @declared_attr
    def capability_template(cls):
        """
        Capability template to expose (can be ``None``).

        :type: :class:`CapabilityTemplate`
        """
        return relationship.one_to_one(
            cls, 'capability_template', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def requirement_template(cls):
        """
        Requirement template to expose (can be ``None``).

        :type: :class:`RequirementTemplate`
        """
        return relationship.one_to_one(
            cls, 'requirement_template', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_one relationships

    @declared_attr
    def substitution_template(cls):
        """
        Containing substitution template.

        :type: :class:`SubstitutionTemplate`
        """
        return relationship.many_to_one(cls, 'substitution_template', back_populates='mappings')

    # endregion

    # region foreign keys

    @declared_attr
    def substitution_template_fk(cls):
        """For SubstitutionTemplate one-to-many to SubstitutionTemplateMapping"""
        return relationship.foreign_key('substitution_template')

    @declared_attr
    def capability_template_fk(cls):
        """For SubstitutionTemplate one-to-one to CapabilityTemplate"""
        return relationship.foreign_key('capability_template', nullable=True)

    @declared_attr
    def requirement_template_fk(cls):
        """For SubstitutionTemplate one-to-one to RequirementTemplate"""
        return relationship.foreign_key('requirement_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),))


class RequirementTemplateBase(TemplateModelMixin):
    """
    Template for creating :class:`Relationship` instances, which are optionally-typed edges in the
    service topology, connecting a :class:`Node` to a :class:`Capability` of another node.

    Note that there is no equivalent "Requirement" instance model. Instead, during instantiation a
    requirement template is matched with a capability and a :class:`Relationship` is instantiated.

    A requirement template *must* target a :class:`CapabilityType` or a capability name. It can
    optionally target a specific :class:`NodeType` or :class:`NodeTemplate`.

    Requirement templates may optionally contain a :class:`RelationshipTemplate`. If they do not,
    a :class:`Relationship` will be instantiated with default values.
    """

    __tablename__ = 'requirement_template'

    __private_fields__ = ('target_capability_type_fk',
                          'target_node_template_fk',
                          'target_node_type_fk',
                          'relationship_template_fk',
                          'node_template_fk')

    # region one_to_one relationships

    @declared_attr
    def target_capability_type(cls):
        """
        Target capability type.

        :type: :class:`CapabilityType`
        """
        return relationship.one_to_one(cls,
                                       'type',
                                       fk='target_capability_type_fk',
                                       back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def target_node_template(cls):
        """
        Target node template (can be ``None``).

        :type: :class:`NodeTemplate`
        """
        return relationship.one_to_one(cls,
                                       'node_template',
                                       fk='target_node_template_fk',
                                       back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def relationship_template(cls):
        """
        Associated relationship template (can be ``None``).

        :type: :class:`RelationshipTemplate`
        """
        return relationship.one_to_one(cls, 'relationship_template')

    # endregion

    # region one_to_many relationships

    @declared_attr
    def relationships(cls):
        """
        Instantiated relationships.

        :type: [:class:`Relationship`]
        """
        return relationship.one_to_many(cls, 'relationship')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        """
        Containing node template.

        :type: :class:`NodeTemplate`
        """
        return relationship.many_to_one(cls, 'node_template', fk='node_template_fk')

    @declared_attr
    def target_node_type(cls):
        """
        Target node type (can be ``None``).

        :type: :class:`Type`
        """
        return relationship.many_to_one(
            cls, 'type', fk='target_node_type_fk', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region foreign keys

    @declared_attr
    def target_node_type_fk(cls):
        """For RequirementTemplate many-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    @declared_attr
    def target_node_template_fk(cls):
        """For RequirementTemplate one-to-one to NodeTemplate"""
        return relationship.foreign_key('node_template', nullable=True)

    @declared_attr
    def target_capability_type_fk(cls):
        """For RequirementTemplate one-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    @declared_attr
    def node_template_fk(cls):
        """For NodeTemplate one-to-many to RequirementTemplate"""
        return relationship.foreign_key('node_template')

    @declared_attr
    def relationship_template_fk(cls):
        """For RequirementTemplate one-to-one to RelationshipTemplate"""
        return relationship.foreign_key('relationship_template', nullable=True)

    # endregion

    target_capability_name = Column(Text, doc="""
    Target capability name in node template or node type (can be ``None``).

    :type: :obj:`basestring`
    """)

    target_node_template_constraints = Column(PickleType, doc="""
    Constraints for filtering relationship targets.

    :type: [:class:`NodeTemplateConstraint`]
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('target_node_type_name', self.target_node_type.name
             if self.target_node_type is not None else None),
            ('target_node_template_name', self.target_node_template.name
             if self.target_node_template is not None else None),
            ('target_capability_type_name', self.target_capability_type.name
             if self.target_capability_type is not None else None),
            ('target_capability_name', self.target_capability_name),
            ('relationship_template', formatting.as_raw(self.relationship_template))))


class RelationshipTemplateBase(TemplateModelMixin):
    """
    Optional addition to a :class:`RequirementTemplate`.

    Note that a relationship template here is not exactly equivalent to a relationship template
    entity in TOSCA. For example, a TOSCA requirement specifying a relationship type rather than a
    relationship template would still be represented here as a relationship template.
    """

    __tablename__ = 'relationship_template'

    __private_fields__ = ('type_fk',)

    # region one_to_many relationships

    @declared_attr
    def relationships(cls):
        """
        Instantiated relationships.

        :type: [:class:`Relationship`]
        """
        return relationship.one_to_many(cls, 'relationship')

    @declared_attr
    def interface_templates(cls):
        """
        Associated interface templates.

        :type: {:obj:`basestring`: :class:`InterfaceTemplate`}
        """
        return relationship.one_to_many(cls, 'interface_template', dict_key='name')

    @declared_attr
    def properties(cls):
        """
        Declarations for associated immutable parameters.

        :type: {:obj:`basestring`: :class:`Property`}
        """
        return relationship.one_to_many(cls, 'property', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def type(cls):
        """
        Relationship type.

        :type: :class:`Type`
        """
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region foreign keys

    @declared_attr
    def type_fk(cls):
        """For RelationshipTemplate many-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    # endregion

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('type_name', self.type.name if self.type is not None else None),
            ('name', self.name),
            ('description', self.description),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates))))


class CapabilityTemplateBase(TemplateModelMixin):
    """
    Template for creating :class:`Capability` instances, typed attachments which serve two purposes:
    to provide extra properties and attributes to :class:`Node` instances, and to expose targets for
    :class:`Relationship` instances from other nodes.
    """

    __tablename__ = 'capability_template'

    __private_fields__ = ('type_fk',
                          'node_template_fk')

    # region one_to_many relationships

    @declared_attr
    def capabilities(cls):
        """
        Instantiated capabilities.

        :type: [:class:`Capability`]
        """
        return relationship.one_to_many(cls, 'capability')

    @declared_attr
    def properties(cls):
        """
        Declarations for associated immutable parameters.

        :type: {:obj:`basestring`: :class:`Property`}
        """
        return relationship.one_to_many(cls, 'property', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        """
        Containing node template.

        :type: :class:`NodeTemplate`
        """
        return relationship.many_to_one(cls, 'node_template')

    @declared_attr
    def type(cls):
        """
        Capability type.

        :type: :class:`Type`
        """
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def valid_source_node_types(cls):
        """
        Reject requirements that are not from these node types.

        :type: [:class:`Type`]
        """
        return relationship.many_to_many(cls, 'type', prefix='valid_sources')

    # endregion

    # region foreign keys

    @declared_attr
    def type_fk(cls):
        """For CapabilityTemplate many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def node_template_fk(cls):
        """For NodeTemplate one-to-many to CapabilityTemplate"""
        return relationship.foreign_key('node_template')

    # endregion

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    min_occurrences = Column(Integer, default=None, doc="""
    Minimum number of requirement matches required.

    :type: :obj:`int`
    """)

    max_occurrences = Column(Integer, default=None, doc="""
    Maximum number of requirement matches allowed.

    :type: :obj:`int`
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('min_occurrences', self.min_occurrences),
            ('max_occurrences', self.max_occurrences),
            ('valid_source_node_types', [v.name for v in self.valid_source_node_types]),
            ('properties', formatting.as_raw_dict(self.properties))))


class InterfaceTemplateBase(TemplateModelMixin):
    """
    Template for creating :class:`Interface` instances, which are typed bundles of
    :class:`Operation` instances.

    Can be associated with a :class:`NodeTemplate`, a :class:`GroupTemplate`, or a
    :class:`RelationshipTemplate`.
    """

    __tablename__ = 'interface_template'

    __private_fields__ = ('type_fk',
                          'node_template_fk',
                          'group_template_fk',
                          'relationship_template_fk')

    # region one_to_many relationships

    @declared_attr
    def inputs(cls):
        """
        Declarations for externally provided parameters that can be used by all operations of the
        interface.

        :type: {:obj:`basestring`: :class:`Input`}
        """
        return relationship.one_to_many(cls, 'input', dict_key='name')

    @declared_attr
    def interfaces(cls):
        """
        Instantiated interfaces.

        :type: [:class:`Interface`]
        """
        return relationship.one_to_many(cls, 'interface')

    @declared_attr
    def operation_templates(cls):
        """
        Associated operation templates.

        :type: {:obj:`basestring`: :class:`OperationTemplate`}
        """
        return relationship.one_to_many(cls, 'operation_template', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        """
        Containing node template (can be ``None``).

        :type: :class:`NodeTemplate`
        """
        return relationship.many_to_one(cls, 'node_template')

    @declared_attr
    def group_template(cls):
        """
        Containing group template (can be ``None``).

        :type: :class:`GroupTemplate`
        """
        return relationship.many_to_one(cls, 'group_template')

    @declared_attr
    def relationship_template(cls):
        """
        Containing relationship template (can be ``None``).

        :type: :class:`RelationshipTemplate`
        """
        return relationship.many_to_one(cls, 'relationship_template')

    @declared_attr
    def type(cls):
        """
        Interface type.

        :type: :class:`Type`
        """
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region foreign keys

    @declared_attr
    def type_fk(cls):
        """For InterfaceTemplate many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def node_template_fk(cls):
        """For NodeTemplate one-to-many to InterfaceTemplate"""
        return relationship.foreign_key('node_template', nullable=True)

    @declared_attr
    def group_template_fk(cls):
        """For GroupTemplate one-to-many to InterfaceTemplate"""
        return relationship.foreign_key('group_template', nullable=True)

    @declared_attr
    def relationship_template_fk(cls):
        """For RelationshipTemplate one-to-many to InterfaceTemplate"""
        return relationship.foreign_key('relationship_template', nullable=True)

    # endregion

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('inputs', formatting.as_raw_dict(self.inputs)),                                        # pylint: disable=no-member
            # TODO fix self.properties reference
            ('operation_templates', formatting.as_raw_list(self.operation_templates))))


class OperationTemplateBase(TemplateModelMixin):
    """
    Template for creating :class:`Operation` instances, which are entry points to Python functions
    called as part of a workflow execution.
    """

    __tablename__ = 'operation_template'

    __private_fields__ = ('service_template_fk',
                          'interface_template_fk',
                          'plugin_fk')

    # region one_to_one relationships

    @declared_attr
    def plugin_specification(cls):
        """
        Associated plugin specification.

        :type: :class:`PluginSpecification`
        """
        return relationship.one_to_one(
            cls, 'plugin_specification', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region one_to_many relationships

    @declared_attr
    def operations(cls):
        """
        Instantiated operations.

        :type: [:class:`Operation`]
        """
        return relationship.one_to_many(cls, 'operation')

    @declared_attr
    def inputs(cls):
        """
        Declarations for parameters provided to the :attr:`implementation`.

        :type: {:obj:`basestring`: :class:`Input`}
        """
        return relationship.one_to_many(cls, 'input', dict_key='name')

    @declared_attr
    def configurations(cls):
        """
        Configuration parameters for the operation instance Python :attr:`function`.

        :type: {:obj:`basestring`: :class:`Configuration`}
        """
        return relationship.one_to_many(cls, 'configuration', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        """
        Containing service template (can be ``None``). For workflow operation templates.

        :type: :class:`ServiceTemplate`
        """
        return relationship.many_to_one(cls, 'service_template',
                                        back_populates='workflow_templates')

    @declared_attr
    def interface_template(cls):
        """
        Containing interface template (can be ``None``).

        :type: :class:`InterfaceTemplate`
        """
        return relationship.many_to_one(cls, 'interface_template')

    # endregion

    # region foreign keys

    @declared_attr
    def service_template_fk(cls):
        """For ServiceTemplate one-to-many to OperationTemplate"""
        return relationship.foreign_key('service_template', nullable=True)

    @declared_attr
    def interface_template_fk(cls):
        """For InterfaceTemplate one-to-many to OperationTemplate"""
        return relationship.foreign_key('interface_template', nullable=True)

    @declared_attr
    def plugin_specification_fk(cls):
        """For OperationTemplate one-to-one to PluginSpecification"""
        return relationship.foreign_key('plugin_specification', nullable=True)

    # endregion

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    relationship_edge = Column(Boolean, doc="""
    When ``True`` specifies that the operation is on the relationship's target edge; ``False`` is
    the source edge (only used by operations on relationships)

    :type: :obj:`bool`
    """)

    implementation = Column(Text, doc="""
    Implementation (usually the name of an artifact).

    :type: :obj:`basestring`
    """)

    dependencies = Column(modeling_types.StrictList(item_cls=basestring), doc="""
    Dependencies (usually names of artifacts).

    :type: [:obj:`basestring`]
    """)

    function = Column(Text, doc="""
    Full path to Python function.

    :type: :obj:`basestring`
    """)

    executor = Column(Text, doc="""
    Name of executor.

    :type: :obj:`basestring`
    """)

    max_attempts = Column(Integer, doc="""
    Maximum number of attempts allowed in case of task failure.

    :type: :obj:`int`
    """)

    retry_interval = Column(Integer, doc="""
    Interval between task retry attemps (in seconds).

    :type: :obj:`float`
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('implementation', self.implementation),
            ('dependencies', self.dependencies),
            ('inputs', formatting.as_raw_dict(self.inputs))))


class ArtifactTemplateBase(TemplateModelMixin):
    """
    Template for creating an :class:`Artifact` instance, which is a typed file, either provided in a
    CSAR or downloaded from a repository.
    """

    __tablename__ = 'artifact_template'

    __private_fields__ = ('type_fk',
                          'node_template_fk')

    # region one_to_many relationships

    @declared_attr
    def artifacts(cls):
        """
        Instantiated artifacts.

        :type: [:class:`Artifact`]
        """
        return relationship.one_to_many(cls, 'artifact')

    @declared_attr
    def properties(cls):
        """
        Declarations for associated immutable parameters.

        :type: {:obj:`basestring`: :class:`Property`}
        """
        return relationship.one_to_many(cls, 'property', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        """
        Containing node template.

        :type: :class:`NodeTemplate`
        """
        return relationship.many_to_one(cls, 'node_template')

    @declared_attr
    def type(cls):
        """
        Artifact type.

        :type: :class:`Type`
        """
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region foreign keys

    @declared_attr
    def type_fk(cls):
        """For ArtifactTemplate many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def node_template_fk(cls):
        """For NodeTemplate one-to-many to ArtifactTemplate"""
        return relationship.foreign_key('node_template')

    # endregion

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    source_path = Column(Text, doc="""
    Source path (in CSAR or repository).

    :type: :obj:`basestring`
    """)

    target_path = Column(Text, doc="""
    Path at which to install at destination.

    :type: :obj:`basestring`
    """)

    repository_url = Column(Text, doc="""
    Repository URL.

    :type: :obj:`basestring`
    """)

    repository_credential = Column(modeling_types.StrictDict(basestring, basestring), doc="""
    Credentials for accessing the repository.

    :type: {:obj:`basestring`, :obj:`basestring`}
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('source_path', self.source_path),
            ('target_path', self.target_path),
            ('repository_url', self.repository_url),
            ('repository_credential', formatting.as_agnostic(self.repository_credential)),
            ('properties', formatting.as_raw_dict(self.properties))))


class PluginSpecificationBase(TemplateModelMixin):
    """
    Requirement for a :class:`Plugin`.

    The actual plugin to be selected depends on those currently installed in ARIA.
    """

    __tablename__ = 'plugin_specification'

    __private_fields__ = ('service_template_fk',
                          'plugin_fk')

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        """
        Containing service template.

        :type: :class:`ServiceTemplate`
        """
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def plugin(cls):                                                                                # pylint: disable=method-hidden
        """
        Matched plugin.

        :type: :class:`Plugin`
        """
        return relationship.many_to_one(cls, 'plugin', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region foreign keys

    @declared_attr
    def service_template_fk(cls):
        """For ServiceTemplate one-to-many to PluginSpecification"""
        return relationship.foreign_key('service_template', nullable=True)

    @declared_attr
    def plugin_fk(cls):
        """For PluginSpecification many-to-one to Plugin"""
        return relationship.foreign_key('plugin', nullable=True)

    # endregion

    version = Column(Text, doc="""
    Minimum plugin version.

    :type: :obj:`basestring`
    """)

    enabled = Column(Boolean, nullable=False, default=True, doc="""
    Whether the plugin is enabled.

    :type: :obj:`bool`
    """)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('version', self.version),
            ('enabled', self.enabled)))
