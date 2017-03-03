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

# pylint: disable=no-self-argument, no-member, abstract-method

from sqlalchemy import (
    Column,
    Text,
    Integer
)
from sqlalchemy import DateTime
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

from .bases import InstanceModelMixin
from ..parser import validation
from ..utils import collections, formatting, console

from . import (
    utils,
    types as modeling_types
)


class ServiceBase(InstanceModelMixin): # pylint: disable=too-many-public-methods
    """
    A service instance is usually an instance of a :class:`ServiceTemplate`.

    You will usually not create it programmatically, but instead instantiate it from the template.

    :ivar description: Human-readable description
    :ivar meta_data: Dict of :class:`Metadata`
    :ivar nodes: Dict of :class:`Node`
    :ivar groups: Dict of :class:`Group`
    :ivar policies: Dict of :class:`Policy`
    :ivar substitution: :class:`Substitution`
    :ivar inputs: Dict of :class:`Parameter`
    :ivar outputs: Dict of :class:`Parameter`
    :ivar operations: Dict of :class:`Operation`
    """

    __tablename__ = 'service'

    description = Column(Text)

    @declared_attr
    def meta_data(cls):
        # Warning! We cannot use the attr name "metadata" because it's used by SqlAlchemy!
        return cls.many_to_many_relationship('metadata', dict_key='name')

    @declared_attr
    def nodes(cls):
        return cls.one_to_many_relationship('node')

    @declared_attr
    def groups(cls):
        return cls.one_to_many_relationship('group')

    @declared_attr
    def policies(cls):
        return cls.one_to_many_relationship('policy')

    @declared_attr
    def substitution(cls):
        return cls.one_to_one_relationship('substitution')

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs',
                                             dict_key='name')

    @declared_attr
    def outputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='outputs',
                                             dict_key='name')

    @declared_attr
    def operations(cls):
        return cls.one_to_many_relationship('operation', dict_key='name')

    @declared_attr
    def service_template(cls):
        return cls.many_to_one_relationship('service_template')

    # region orchestration

    created_at = Column(DateTime, nullable=False, index=True)
    updated_at = Column(DateTime)
    permalink = Column(Text)
    scaling_groups = Column(modeling_types.Dict)
    workflows = Column(modeling_types.Dict)

    @declared_attr
    def service_template_name(cls):
        return association_proxy('service_template', 'name')

    # endregion

    # region foreign keys

    __private_fields__ = ['substituion_fk',
                          'service_template_fk']

    # Service one-to-one to Substitution
    @declared_attr
    def substitution_fk(cls):
        return cls.foreign_key('substitution', nullable=True)

    # Service many-to-one to ServiceTemplate
    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template', nullable=True)

    # endregion

    def satisfy_requirements(self, context):
        satisfied = True
        for node in self.nodes:
            if not node.satisfy_requirements(context):
                satisfied = False
        return satisfied

    def validate_capabilities(self, context):
        satisfied = True
        for node in self.nodes:
            if not node.validate_capabilities(context):
                satisfied = False
        return satisfied

    def find_nodes(self, node_template_name):
        nodes = []
        for node in self.nodes:
            if node.node_template.name == node_template_name:
                nodes.append(node)
        return collections.FrozenList(nodes)

    def get_node_ids(self, node_template_name):
        return collections.FrozenList((node.name for node in self.find_nodes(node_template_name)))

    def find_groups(self, group_template_name):
        groups = []
        for group in self.groups:
            if group.template_name == group_template_name:
                groups.append(group)
        return collections.FrozenList(groups)

    def get_group_ids(self, group_template_name):
        return collections.FrozenList((group.name
                                       for group in self.find_groups(group_template_name)))

    def is_node_a_target(self, context, target_node):
        for node in self.nodes:
            if self._is_node_a_target(context, node, target_node):
                return True
        return False

    def _is_node_a_target(self, context, source_node, target_node):
        if source_node.relationships:
            for relationship in source_node.relationships:
                if relationship.target_node_id == target_node.name:
                    return True
                else:
                    node = context.modeling.instance.nodes.get(relationship.target_node_id)
                    if node is not None:
                        if self._is_node_a_target(context, node, target_node):
                            return True
        return False

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('description', self.description),
            ('metadata', formatting.as_raw_dict(self.meta_data)),
            ('nodes', formatting.as_raw_list(self.nodes)),
            ('groups', formatting.as_raw_list(self.groups)),
            ('policies', formatting.as_raw_list(self.policies)),
            ('substitution', formatting.as_raw(self.substitution)),
            ('inputs', formatting.as_raw_dict(self.inputs)),
            ('outputs', formatting.as_raw_dict(self.outputs)),
            ('operations', formatting.as_raw_list(self.operations))))

    def validate(self, context):
        utils.validate_dict_values(context, self.meta_data)
        utils.validate_list_values(context, self.nodes)
        utils.validate_list_values(context, self.groups)
        utils.validate_list_values(context, self.policies)
        if self.substitution is not None:
            self.substitution.validate(context)
        utils.validate_dict_values(context, self.inputs)
        utils.validate_dict_values(context, self.outputs)
        utils.validate_dict_values(context, self.operations)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.meta_data, report_issues)
        utils.coerce_list_values(context, container, self.nodes, report_issues)
        utils.coerce_list_values(context, container, self.groups, report_issues)
        utils.coerce_list_values(context, container, self.policies, report_issues)
        if self.substitution is not None:
            self.substitution.coerce_values(context, container, report_issues)
        utils.coerce_dict_values(context, container, self.inputs, report_issues)
        utils.coerce_dict_values(context, container, self.outputs, report_issues)
        utils.coerce_dict_values(context, container, self.operations, report_issues)

    def dump(self, context):
        if self.description is not None:
            console.puts(context.style.meta(self.description))
        utils.dump_parameters(context, self.meta_data, 'Metadata')
        for node in self.nodes:
            node.dump(context)
        for group in self.groups:
            group.dump(context)
        for policy in self.policies:
            policy.dump(context)
        if self.substitution is not None:
            self.substitution.dump(context)
        utils.dump_parameters(context, self.inputs, 'Inputs')
        utils.dump_parameters(context, self.outputs, 'Outputs')
        utils.dump_dict_values(context, self.operations, 'Operations')

    def dump_graph(self, context):
        for node in self.nodes.itervalues():
            if not self.is_node_a_target(context, node):
                self._dump_graph_node(context, node)

    def _dump_graph_node(self, context, node):
        console.puts(context.style.node(node.name))
        if node.relationships:
            with context.style.indent:
                for relationship in node.relationships:
                    relationship_name = (context.style.node(relationship.template_name)
                                         if relationship.template_name is not None
                                         else context.style.type(relationship.type_name))
                    capability_name = (context.style.node(relationship.target_capability_name)
                                       if relationship.target_capability_name is not None
                                       else None)
                    if capability_name is not None:
                        console.puts('-> {0} {1}'.format(relationship_name, capability_name))
                    else:
                        console.puts('-> {0}'.format(relationship_name))
                    target_node = self.nodes.get(relationship.target_node_id)
                    with console.indent(3):
                        self._dump_graph_node(context, target_node)


class NodeBase(InstanceModelMixin):
    """
    Usually an instance of a :class:`NodeTemplate`.

    Nodes may have zero or more :class:`Relationship` instances to other nodes.

    :ivar name: Unique ID (often prefixed with the template name)
    :ivar properties: Dict of :class:`Parameter`
    :ivar interfaces: Dict of :class:`Interface`
    :ivar artifacts: Dict of :class:`Artifact`
    :ivar capabilities: Dict of :class:`CapabilityTemplate`
    :ivar relationships: List of :class:`Relationship`
    """

    __tablename__ = 'node'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def interfaces(cls):
        return cls.one_to_many_relationship('interface', dict_key='name')

    @declared_attr
    def artifacts(cls):
        return cls.one_to_many_relationship('artifact', dict_key='name')

    @declared_attr
    def capabilities(cls):
        return cls.one_to_many_relationship('capability', dict_key='name')

    @declared_attr
    def outbound_relationships(cls):
        return cls.one_to_many_relationship('relationship',
                                            foreign_key='source_node_fk',
                                            backreference='source_node')

    @declared_attr
    def inbound_relationships(cls):
        return cls.one_to_many_relationship('relationship',
                                            foreign_key='target_node_fk',
                                            backreference='target_node')

    @declared_attr
    def host(cls):
        return cls.relationship_to_self('host_fk')

    @declared_attr
    def node_template(cls):
        return cls.many_to_one_relationship('node_template')

    # region orchestration

    runtime_properties = Column(modeling_types.Dict)
    scaling_groups = Column(modeling_types.List)
    state = Column(Text, nullable=False)
    version = Column(Integer, default=1)

    @declared_attr
    def plugins(cls):
        return association_proxy('node_template', 'plugins')

    @declared_attr
    def service_name(cls):
        return association_proxy('service', 'name')

    @property
    def ip(self):
        # TODO: totally broken
        if not self.host_fk:
            return None
        host_node = self.host
        if 'ip' in host_node.runtime_properties:  # pylint: disable=no-member
            return host_node.runtime_properties['ip']  # pylint: disable=no-member
        host_node = host_node.node_template  # pylint: disable=no-member
        host_ip_property = [prop for prop in host_node.properties if prop.name == 'ip']
        if host_ip_property:
            return host_ip_property[0].value
        return None

    # endregion

    # region foreign_keys

    __private_fields__ = ['type_fk',
                          'host_fk',
                          'service_fk',
                          'node_template_fk']

    # Node many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # Node one-to-one to Node
    @declared_attr
    def host_fk(cls):
        return cls.foreign_key('node', nullable=True)

    # Service one-to-many to Node
    @declared_attr
    def service_fk(cls):
        return cls.foreign_key('service')

    # Node many-to-one to NodeTemplate
    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template', nullable=True)

    # endregion

    def satisfy_requirements(self, context):
        node_template = self.node_template
        satisfied = True
        for requirement_template in node_template.requirement_templates:
            # Find target template
            target_node_template, target_node_capability = \
                requirement_template.find_target(context, node_template)
            if target_node_template is not None:
                satisfied = self._satisfy_capability(context,
                                                     target_node_capability,
                                                     target_node_template,
                                                     requirement_template)
            else:
                context.validation.report('requirement "{0}" of node "{1}" has no target node '
                                          'template'.format(requirement_template.name, self.name),
                                          level=validation.Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    def _satisfy_capability(self, context, target_node_capability, target_node_template,
                            requirement_template):
        from . import models
        # Find target nodes
        target_nodes = context.modeling.instance.find_nodes(target_node_template.name)
        if target_nodes:
            target_node = None
            target_capability = None

            if target_node_capability is not None:
                # Relate to the first target node that has capacity
                for node in target_nodes:
                    target_capability = node.capabilities.get(target_node_capability.name)
                    if target_capability.relate():
                        target_node = node
                        break
            else:
                # Use first target node
                target_node = target_nodes[0]

            if target_node is not None:
                if requirement_template.relationship_template is not None:
                    relationship = \
                        requirement_template.relationship_template.instantiate(context, self)
                else:
                    relationship = models.Relationship(capability=target_capability)
                relationship.name = requirement_template.name
                relationship.requirement_template = requirement_template
                relationship.target_node = target_node
                self.outbound_relationships.append(relationship)
                return True
            else:
                context.validation.report('requirement "{0}" of node "{1}" targets node '
                                          'template "{2}" but its instantiated nodes do not '
                                          'have enough capacity'.format(
                                              requirement_template.name,
                                              self.name,
                                              target_node_template.name),
                                          level=validation.Issue.BETWEEN_INSTANCES)
                return False
        else:
            context.validation.report('requirement "{0}" of node "{1}" targets node template '
                                      '"{2}" but it has no instantiated nodes'.format(
                                          requirement_template.name,
                                          self.name,
                                          target_node_template.name),
                                      level=validation.Issue.BETWEEN_INSTANCES)
            return False

    def validate_capabilities(self, context):
        satisfied = False
        for capability in self.capabilities.itervalues():
            if not capability.has_enough_relationships:
                context.validation.report('capability "{0}" of node "{1}" requires at least {2:d} '
                                          'relationships but has {3:d}'.format(
                                              capability.name,
                                              self.name,
                                              capability.min_occurrences,
                                              capability.occurrences),
                                          level=validation.Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces)),
            ('artifacts', formatting.as_raw_list(self.artifacts)),
            ('capabilities', formatting.as_raw_list(self.capabilities)),
            ('relationships', formatting.as_raw_list(self.outbound_relationships))))

    def validate(self, context):
        if len(self.name) > context.modeling.id_max_length:
            context.validation.report('"{0}" has an ID longer than the limit of {1:d} characters: '
                                      '{2:d}'.format(
                                          self.name,
                                          context.modeling.id_max_length,
                                          len(self.name)),
                                      level=validation.Issue.BETWEEN_INSTANCES)

        # TODO: validate that node template is of type?

        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interfaces)
        utils.validate_dict_values(context, self.artifacts)
        utils.validate_dict_values(context, self.capabilities)
        utils.validate_list_values(context, self.outbound_relationships)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)
        utils.coerce_dict_values(context, self, self.interfaces, report_issues)
        utils.coerce_dict_values(context, self, self.artifacts, report_issues)
        utils.coerce_dict_values(context, self, self.capabilities, report_issues)
        utils.coerce_list_values(context, self, self.outbound_relationships, report_issues)

    def dump(self, context):
        console.puts('Node: {0}'.format(context.style.node(self.name)))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            console.puts('Template: {0}'.format(context.style.node(self.node_template.name)))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interfaces)
            utils.dump_dict_values(context, self.artifacts, 'Artifacts')
            utils.dump_dict_values(context, self.capabilities, 'Capabilities')
            utils.dump_list_values(context, self.outbound_relationships, 'Relationships')


class GroupBase(InstanceModelMixin):
    """
    Usually an instance of a :class:`GroupTemplate`.

    :ivar name: Unique ID (often equal to the template name)
    :ivar properties: Dict of :class:`Parameter`
    :ivar interfaces: Dict of :class:`Interface`
    """

    __tablename__ = 'group'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def interfaces(cls):
        return cls.one_to_many_relationship('interface', dict_key='name')

    @declared_attr
    def nodes(cls):
        return cls.many_to_many_relationship('node')

    @declared_attr
    def group_template(cls):
        return cls.many_to_one_relationship('group_template')

    # region foreign_keys

    __private_fields__ = ['type_fk',
                          'service_fk',
                          'group_template_fk']

    # Group many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # Service one-to-many to Group
    @declared_attr
    def service_fk(cls):
        return cls.foreign_key('service')

    # Group many-to-one to GroupTemplate
    @declared_attr
    def group_template_fk(cls):
        return cls.foreign_key('group_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces))))

    def validate(self, context):
        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interfaces)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)
        utils.coerce_dict_values(context, container, self.interfaces, report_issues)

    def dump(self, context):
        console.puts('Group: {0}'.format(context.style.node(self.name)))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interfaces)
            if self.nodes:
                console.puts('Member nodes:')
                with context.style.indent:
                    for node in self.nodes:
                        console.puts(context.style.node(node.name))


class PolicyBase(InstanceModelMixin):
    """
    Usually an instance of a :class:`PolicyTemplate`.

    :ivar name: Name
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'policy'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def nodes(cls):
        return cls.many_to_many_relationship('node')

    @declared_attr
    def groups(cls):
        return cls.many_to_many_relationship('group')

    @declared_attr
    def policy_template(cls):
        return cls.many_to_one_relationship('policy_template')

    # region foreign_keys

    __private_fields__ = ['type_fk',
                          'service_fk',
                          'policy_template_fk']

    # Policy many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # Service one-to-many to Policy
    @declared_attr
    def service_fk(cls):
        return cls.foreign_key('service')

    # Policy many-to-one to PolicyTemplate
    @declared_attr
    def policy_template_fk(cls):
        return cls.foreign_key('policy_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('properties', formatting.as_raw_dict(self.properties))))

    def validate(self, context):
        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        console.puts('Policy: {0}'.format(context.style.node(self.name)))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_parameters(context, self.properties)
            if self.nodes:
                console.puts('Target nodes:')
                with context.style.indent:
                    for node in self.nodes:
                        console.puts(context.style.node(node.name))
            if self.groups:
                console.puts('Target groups:')
                with context.style.indent:
                    for group in self.groups:
                        console.puts(context.style.node(group.name))


class SubstitutionBase(InstanceModelMixin):
    """
    Usually an instance of a :class:`SubstitutionTemplate`.

    :ivar mappings: Dict of :class:` SubstitutionMapping`
    """

    __tablename__ = 'substitution'

    @declared_attr
    def node_type(cls):
        return cls.many_to_one_relationship('type')

    @declared_attr
    def mappings(cls):
        return cls.one_to_many_relationship('substitution_mapping', dict_key='name')

    @declared_attr
    def substitution_template(cls):
        return cls.many_to_one_relationship('substitution_template')

    # region foreign_keys

    __private_fields__ = ['node_type_fk',
                          'substitution_template_fk']

    # Substitution many-to-one to Type
    @declared_attr
    def node_type_fk(cls):
        return cls.foreign_key('type')

    # Substitution many-to-one to SubstitutionTemplate
    @declared_attr
    def substitution_template_fk(cls):
        return cls.foreign_key('substitution_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('node_type_name', self.node_type_name),
            ('mappings', formatting.as_raw_dict(self.mappings))))

    def validate(self, context):
        utils.validate_dict_values(context, self.mappings)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.mappings, report_issues)

    def dump(self, context):
        console.puts('Substitution:')
        with context.style.indent:
            console.puts('Node type: {0}'.format(context.style.type(self.node_type.name)))
            utils.dump_dict_values(context, self.mappings, 'Mappings')


class SubstitutionMappingBase(InstanceModelMixin):
    """
    An instance of a :class:`SubstitutionMappingTemplate`.

    :ivar name: Exposed capability or requirement name
    """

    __tablename__ = 'substitution_mapping'

    @declared_attr
    def node(cls):
        return cls.one_to_one_relationship('node')

    @declared_attr
    def capability(cls):
        return cls.one_to_one_relationship('capability')

    @declared_attr
    def requirement_template(cls):
        return cls.one_to_one_relationship('requirement_template')

    # region foreign keys

    __private_fields__ = ['substitution_fk',
                          'node_fk',
                          'capability_fk',
                          'requirement_template_fk']

    # Substitution one-to-many to SubstitutionMapping
    @declared_attr
    def substitution_fk(cls):
        return cls.foreign_key('substitution')

    # Substitution one-to-one to NodeTemplate
    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node')

    # Substitution one-to-one to Capability
    @declared_attr
    def capability_fk(cls):
        return cls.foreign_key('capability', nullable=True)

    # Substitution one-to-one to RequirementTemplate
    @declared_attr
    def requirement_template_fk(cls):
        return cls.foreign_key('requirement_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name)))

    def validate(self, context):
        if (self.capability is None) and (self.requirement_template is None):
            context.validation.report('mapping "{0}" refers to neither capability nor a requirement'
                                      ' in node: {1}'.format(
                                          self.name,
                                          formatting.safe_repr(self.node.name)),
                                      level=validation.Issue.BETWEEN_TYPES)

    def dump(self, context):
        console.puts('{0} -> {1}.{2}'.format(
            context.style.node(self.name),
            context.style.node(self.node.name),
            context.style.node(self.capability.name
                               if self.capability
                               else self.requirement_template.name)))


class RelationshipBase(InstanceModelMixin):
    """
    Connects :class:`Node` to another node.

    Might be an instance of a :class:`RelationshipTemplate`.

    :ivar name: Name (usually the name of the requirement at the source node template)
    :ivar properties: Dict of :class:`Parameter`
    :ivar interfaces: Dict of :class:`Interface`
    """

    __tablename__ = 'relationship'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def interfaces(cls):
        return cls.one_to_many_relationship('interface', dict_key='name')

    @declared_attr
    def capability(cls):
        return cls.one_to_one_relationship('capability')

    @declared_attr
    def requirement_template(cls):
        return cls.many_to_one_relationship('requirement_template')

    @declared_attr
    def relationship_template(cls):
        return cls.many_to_one_relationship('relationship_template')

    # region orchestration

    source_position = Column(Integer) # ???
    target_position = Column(Integer) # ???

    # endregion

    # region foreign keys

    __private_fields__ = ['type_fk',
                          'source_node_fk',
                          'target_node_fk',
                          'capability_fk',
                          'requirement_template_fk',
                          'relationship_template_fk']

    # Relationship many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # Node one-to-many to Relationship
    @declared_attr
    def source_node_fk(cls):
        return cls.foreign_key('node')

    # Node one-to-many to Relationship
    @declared_attr
    def target_node_fk(cls):
        return cls.foreign_key('node')

    # Relationship one-to-one to Capability
    @declared_attr
    def capability_fk(cls):
        return cls.foreign_key('capability', nullable=True)

    # Relationship many-to-one to RequirementTemplate
    @declared_attr
    def requirement_template_fk(cls):
        return cls.foreign_key('requirement_template', nullable=True)

    # Relationship many-to-one to RelationshipTemplate
    @declared_attr
    def relationship_template_fk(cls):
        return cls.foreign_key('relationship_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('target_node_id', self.target_node.name),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces))))

    def validate(self, context):
        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interfaces)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)
        utils.coerce_dict_values(context, container, self.interfaces, report_issues)

    def dump(self, context):
        if self.name:
            console.puts('{0} ->'.format(context.style.node(self.name)))
        else:
            console.puts('->')
        with context.style.indent:
            console.puts('Node: {0}'.format(context.style.node(self.target_node.name)))
            if self.capability:
                console.puts('Capability: {0}'.format(context.style.node(self.capability.name)))
            if self.type is not None:
                console.puts('Relationship type: {0}'.format(context.style.type(self.type.name)))
            if (self.relationship_template is not None) and self.relationship_template.name:
                console.puts('Relationship template: {0}'.format(
                    context.style.node(self.relationship_template.name)))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interfaces, 'Interfaces')


class CapabilityBase(InstanceModelMixin):
    """
    A capability of a :class:`Node`.

    Usually an instance of a :class:`CapabilityTemplate`.

    :ivar name: Name
    :ivar min_occurrences: Minimum number of requirement matches required
    :ivar max_occurrences: Maximum number of requirement matches allowed
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'capability'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    min_occurrences = Column(Integer, default=None) # optional
    max_occurrences = Column(Integer, default=None) # optional
    occurrences = Column(Integer, default=0)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def capability_template(cls):
        return cls.many_to_one_relationship('capability_template')

    # region foreign_keys

    __private_fields__ = ['capability_fk',
                          'node_fk',
                          'capability_template_fk']

    # Capability many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # Node one-to-many to Capability
    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node')

    # Capability many-to-one to CapabilityTemplate
    @declared_attr
    def capability_template_fk(cls):
        return cls.foreign_key('capability_template', nullable=True)

    # endregion

    @property
    def has_enough_relationships(self):
        if self.min_occurrences is not None:
            return self.occurrences >= self.min_occurrences
        return True

    def relate(self):
        if self.max_occurrences is not None:
            if self.occurrences == self.max_occurrences:
                return False
        self.occurrences += 1
        return True

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('properties', formatting.as_raw_dict(self.properties))))

    def validate(self, context):
        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            console.puts('Occurrences: {0:d} ({1:d}{2})'.format(
                self.occurrences,
                self.min_occurrences or 0,
                ' to {0:d}'.format(self.max_occurrences)
                if self.max_occurrences is not None
                else ' or more'))
            utils.dump_parameters(context, self.properties)


class InterfaceBase(InstanceModelMixin):
    """
    A typed set of :class:`Operation`.
    
    Usually an instance of :class:`InterfaceTemplate`.

    :ivar name: Name
    :ivar description: Description
    :ivar inputs: Dict of :class:`Parameter`
    :ivar operations: Dict of :class:`Operation`
    """

    __tablename__ = 'interface'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    description = Column(Text)

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs',
                                             dict_key='name')

    @declared_attr
    def operations(cls):
        return cls.one_to_many_relationship('operation', dict_key='name')

    @declared_attr
    def interface_template(cls):
        return cls.many_to_one_relationship('interface_template')

    # region foreign_keys

    __private_fields__ = ['type_fk',
                          'node_fk',
                          'group_fk',
                          'relationship_fk',
                          'interface_template_fk']

    # Interface many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # Node one-to-many to Interface
    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node', nullable=True)

    # Group one-to-many to Interface
    @declared_attr
    def group_fk(cls):
        return cls.foreign_key('group', nullable=True)

    # Relationship one-to-many to Interface
    @declared_attr
    def relationship_fk(cls):
        return cls.foreign_key('relationship', nullable=True)

    # Interface many-to-one to InterfaceTemplate
    @declared_attr
    def interface_template_fk(cls):
        return cls.foreign_key('interface_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('inputs', formatting.as_raw_dict(self.inputs)),
            ('operations', formatting.as_raw_list(self.operations))))

    def validate(self, context):
        utils.validate_dict_values(context, self.inputs)
        utils.validate_dict_values(context, self.operations)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.inputs, report_issues)
        utils.coerce_dict_values(context, container, self.operations, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Interface type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_parameters(context, self.inputs, 'Inputs')
            utils.dump_dict_values(context, self.operations, 'Operations')


class OperationBase(InstanceModelMixin):
    """
    An operation in a :class:`Interface`.
    
    Might be an instance of :class:`OperationTemplate`.

    :ivar name: Name
    :ivar description: Description
    :ivar implementation: Implementation string (interpreted by the orchestrator)
    :ivar dependencies: List of strings (interpreted by the orchestrator)
    :ivar executor: Executor string (interpreted by the orchestrator)
    :ivar max_retries: Maximum number of retries allowed in case of failure
    :ivar retry_interval: Interval between retries
    :ivar inputs: Dict of :class:`Parameter`
    """

    __tablename__ = 'operation'

    description = Column(Text)
    implementation = Column(Text)
    dependencies = Column(modeling_types.StrictList(item_cls=basestring))
    executor = Column(Text)
    max_retries = Column(Integer)
    retry_interval = Column(Integer)

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs',
                                             dict_key='name')

    @declared_attr
    def plugin(cls):
        return cls.one_to_one_relationship('plugin')

    @declared_attr
    def operation_template(cls):
        return cls.many_to_one_relationship('operation_template')

    # region foreign_keys

    __private_fields__ = ['service_fk',
                          'interface_fk',
                          'plugin_fk',
                          'operation_template_fk']

    # Service one-to-many to Operation
    @declared_attr
    def service_fk(cls):
        return cls.foreign_key('service', nullable=True)

    # Interface one-to-many to Operation
    @declared_attr
    def interface_fk(cls):
        return cls.foreign_key('interface', nullable=True)

    # Operation one-to-one to Plugin
    @declared_attr
    def plugin_fk(cls):
        return cls.foreign_key('plugin', nullable=True)

    # Operation many-to-one to OperationTemplate
    @declared_attr
    def operation_template_fk(cls):
        return cls.foreign_key('operation_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('implementation', self.implementation),
            ('dependencies', self.dependencies),
            ('executor', self.executor),
            ('max_retries', self.max_retries),
            ('retry_interval', self.retry_interval),
            ('inputs', formatting.as_raw_dict(self.inputs))))

    def validate(self, context):
        # TODO must be associated with interface or service
        utils.validate_dict_values(context, self.inputs)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.inputs, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            if self.implementation is not None:
                console.puts('Implementation: {0}'.format(
                    context.style.literal(self.implementation)))
            if self.dependencies:
                console.puts(
                    'Dependencies: {0}'.format(
                        ', '.join((str(context.style.literal(v)) for v in self.dependencies))))
            if self.executor is not None:
                console.puts('Executor: {0}'.format(context.style.literal(self.executor)))
            if self.max_retries is not None:
                console.puts('Max retries: {0}'.format(context.style.literal(self.max_retries)))
            if self.retry_interval is not None:
                console.puts('Retry interval: {0}'.format(
                    context.style.literal(self.retry_interval)))
            utils.dump_parameters(context, self.inputs, 'Inputs')


class ArtifactBase(InstanceModelMixin):
    """
    A file associated with a :class:`Node`.
    
    Usually an instance of :class:`ArtifactTemplate`.

    :ivar name: Name
    :ivar description: Description
    :ivar source_path: Source path (CSAR or repository)
    :ivar target_path: Path at destination machine
    :ivar repository_url: Repository URL
    :ivar repository_credential: Dict of string
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'artifact'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    description = Column(Text)
    type_name = Column(Text)
    source_path = Column(Text)
    target_path = Column(Text)
    repository_url = Column(Text)
    repository_credential = Column(modeling_types.StrictDict(basestring, basestring))

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def artifact_template(cls):
        return cls.many_to_one_relationship('artifact_template')

    # region foreign_keys

    __private_fields__ = ['type_fk',
                          'node_fk',
                          'artifact_template_fk']

    # Artifact many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # Node one-to-many to Artifact
    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node')

    # Artifact many-to-one to ArtifactTemplate
    @declared_attr
    def artifact_template_fk(cls):
        return cls.foreign_key('artifact_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('source_path', self.source_path),
            ('target_path', self.target_path),
            ('repository_url', self.repository_url),
            ('repository_credential', formatting.as_agnostic(self.repository_credential)),
            ('properties', formatting.as_raw_dict(self.properties))))

    def validate(self, context):
        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Artifact type: {0}'.format(context.style.type(self.type.name)))
            console.puts('Source path: {0}'.format(context.style.literal(self.source_path)))
            if self.target_path is not None:
                console.puts('Target path: {0}'.format(context.style.literal(self.target_path)))
            if self.repository_url is not None:
                console.puts('Repository URL: {0}'.format(
                    context.style.literal(self.repository_url)))
            if self.repository_credential:
                console.puts('Repository credential: {0}'.format(
                    context.style.literal(self.repository_credential)))
            utils.dump_parameters(context, self.properties)
