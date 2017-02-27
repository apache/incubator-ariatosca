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

from sqlalchemy import (
    Column,
    Text,
    Integer,
    Boolean,
)
from sqlalchemy import DateTime
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

from .base import ModelMixin
from ..parser import validation
from ..utils import collections, formatting, console

from . import (
    utils,
    type as modeling_type
)

# pylint: disable=no-self-argument, no-member, abstract-method


class _InstanceModelMixin(ModelMixin):
    """
    Mixin for :class:`ServiceInstance` models.

    All models support validation, diagnostic dumping, and representation as
    raw data (which can be translated into JSON or YAML) via :code:`as_raw`.
    """

    @property
    def as_raw(self):
        raise NotImplementedError

    def validate(self, context):
        pass

    def coerce_values(self, context, container, report_issues):
        pass

    def dump(self, context):
        pass


class ServiceBase(_InstanceModelMixin):
    """
    A service instance is an instance of a :class:`ServiceTemplate`.

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

    __private_fields__ = ['service_template_fk',
                          'substituion_fk']

    description = Column(Text)

    @declared_attr
    def meta_data(cls):
        # Warning! We cannot use the attr name "metadata" because it's used by SqlAlchemy!
        return cls.many_to_many_relationship('metadata', key_column_name='name')

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
                                             key_column_name='name')

    @declared_attr
    def outputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='outputs',
                                             key_column_name='name')

    @declared_attr
    def operations(cls):
        return cls.one_to_many_relationship('operation', key_column_name='name')

    @declared_attr
    def service_template(cls):
        return cls.many_to_one_relationship('service_template')

    # region orchestrator required columns

    created_at = Column(DateTime, nullable=False, index=True)
    permalink = Column(Text)
    policy_triggers = Column(modeling_type.Dict)
    policy_types = Column(modeling_type.Dict)
    scaling_groups = Column(modeling_type.Dict)
    updated_at = Column(DateTime)
    workflows = Column(modeling_type.Dict)

    @declared_attr
    def service_template_name(cls):
        return association_proxy('service_template', 'name')

    # endregion

    # region foreign keys

    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template')

    @declared_attr
    def substitution_fk(cls):
        return cls.foreign_key('substitution', nullable=True)

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
            if node.template_name == node_template_name:
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
        return collections.FrozenList((group.name for group in self.find_groups(group_template_name)))

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


class NodeBase(_InstanceModelMixin):
    """
    An instance of a :class:`NodeTemplate`.

    Nodes may have zero or more :class:`Relationship` instances to other nodes.

    :ivar name: Unique ID (prefixed with the template name)
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar template_name: Must be represented in the :class:`ServiceTemplate`
    :ivar properties: Dict of :class:`Parameter`
    :ivar interfaces: Dict of :class:`Interface`
    :ivar artifacts: Dict of :class:`Artifact`
    :ivar capabilities: Dict of :class:`CapabilityTemplate`
    :ivar relationships: List of :class:`Relationship`
    """

    __tablename__ = 'node'

    __private_fields__ = ['service_fk',
                          'node_template_fk',
                          'host_fk']

    type_name = Column(Text)
    template_name = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    @declared_attr
    def interfaces(cls):
        return cls.one_to_many_relationship('interface', key_column_name='name')

    @declared_attr
    def artifacts(cls):
        return cls.one_to_many_relationship('artifact', key_column_name='name')

    @declared_attr
    def capabilities(cls):
        return cls.one_to_many_relationship('capability', key_column_name='name')

    @declared_attr
    def outbound_relationships(cls):
        return cls.one_to_many_relationship('relationship',
                                            foreign_key_name='source_node_fk',
                                            backreference='source_node')

    @declared_attr
    def inbound_relationships(cls):
        return cls.one_to_many_relationship('relationship',
                                            foreign_key_name='target_node_fk',
                                            backreference='target_node')

    # region orchestrator required columns

    runtime_properties = Column(modeling_type.Dict)
    scaling_groups = Column(modeling_type.List)
    state = Column(Text, nullable=False)
    version = Column(Integer, default=1)

    @declared_attr
    def plugins(cls):
        return association_proxy('node_template', 'plugins')

    @declared_attr
    def host(cls):
        return cls.relationship_to_self('host_fk')

    @declared_attr
    def service_name(cls):
        return association_proxy('service', 'name')

    @property
    def ip(self):
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

    @declared_attr
    def node_template(cls):
        return cls.many_to_one_relationship('node_template')

    @declared_attr
    def service_template(cls):
        return association_proxy('service', 'service_template')

    # endregion

    # region foreign_keys

    @declared_attr
    def service_fk(cls):
        return cls.foreign_key('service')

    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template')

    @declared_attr
    def host_fk(cls):
        return cls.foreign_key('node', nullable=True)

    # endregion

    def satisfy_requirements(self, context):
        node_template = context.modeling.model.get_node_template(self.template_name)
        satisfied = True
        for i in range(len(node_template.requirement_templates)):
            requirement_template = node_template.requirement_templates[i]

            # Find target template
            target_node_template, target_node_capability = \
                requirement_template.find_target(context, node_template)
            if target_node_template is not None:
                satisfied = self._satisfy_capability(context,
                                                     target_node_capability,
                                                     target_node_template,
                                                     requirement_template,
                                                     requirement_template_index=i)
            else:
                context.validation.report('requirement "{0}" of node "{1}" has no target node '
                                          'template'.format(requirement_template.name, self.name),
                                          level=validation.Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    def _satisfy_capability(self, context, target_node_capability, target_node_template,
                            requirement_template, requirement_template_index):
        from . import model
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
                relationship = model.Relationship(
                    name=requirement_template.name,
                    source_requirement_index=requirement_template_index,
                    target_node_id=target_node.name
                )
                if target_capability is not None:
                    relationship.target_capability_name = target_capability.name
                self.outbound_relationships.append(relationship)
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
            ('template_name', self.template_name),
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
            console.puts('Template: {0}'.format(context.style.node(self.template_name)))
            console.puts('Type: {0}'.format(context.style.type(self.type_name)))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interfaces)
            utils.dump_dict_values(context, self.artifacts, 'Artifacts')
            utils.dump_dict_values(context, self.capabilities, 'Capabilities')
            utils.dump_list_values(context, self.outbound_relationships, 'Relationships')


class GroupBase(_InstanceModelMixin):
    """
    An instance of a :class:`GroupTemplate`.

    :ivar name: Unique ID (prefixed with the template name)
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar template_name: Must be represented in the :class:`ServiceTemplate`
    :ivar properties: Dict of :class:`Parameter`
    :ivar interfaces: Dict of :class:`Interface`
    :ivar member_node_ids: Must be represented in the :class:`ServiceInstance`
    :ivar member_group_ids: Must be represented in the :class:`ServiceInstance`
    """

    __tablename__ = 'group'

    __private_fields__ = ['service_fk']

    type_name = Column(Text)
    template_name = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    @declared_attr
    def interfaces(cls):
        return cls.one_to_many_relationship('interface', key_column_name='name')

    member_node_ids = Column(modeling_type.StrictList(basestring))
    member_group_ids = Column(modeling_type.StrictList(basestring))

    # region foreign_keys

    @declared_attr
    def service_fk(cls):
        return cls.foreign_key('service')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces)),
            ('member_node_ids', self.member_node_ids),
            ('member_group_ids', self.member_group_ids)))

    def validate(self, context):
        if context.modeling.group_types.get_descendant(self.type_name) is None:
            context.validation.report('group "{0}" has an unknown type: {1}'.format(
                                        self.name,  # pylint: disable=no-member
                                        # TODO fix self.name reference
                                        formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interfaces)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)
        utils.coerce_dict_values(context, container, self.interfaces, report_issues)

    def dump(self, context):
        console.puts('Group: {0}'.format(context.style.node(self.name)))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type_name)))
            console.puts('Template: {0}'.format(context.style.type(self.template_name)))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interfaces)
            if self.member_node_ids:
                console.puts('Member nodes:')
                with context.style.indent:
                    for node_id in self.member_node_ids:
                        console.puts(context.style.node(node_id))


class PolicyBase(_InstanceModelMixin):
    """
    An instance of a :class:`PolicyTemplate`.

    :ivar name: Name
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar properties: Dict of :class:`Parameter`
    :ivar target_node_ids: Must be represented in the :class:`ServiceInstance`
    :ivar target_group_ids: Must be represented in the :class:`ServiceInstance`
    """

    __tablename__ = 'policy'

    __private_fields__ = ['service_fk']

    type_name = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    target_node_ids = Column(modeling_type.StrictList(basestring))
    target_group_ids = Column(modeling_type.StrictList(basestring))

    # region foreign_keys

    @declared_attr
    def service_fk(cls):
        return cls.foreign_key('service')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('target_node_ids', self.target_node_ids),
            ('target_group_ids', self.target_group_ids)))

    def validate(self, context):
        if context.modeling.policy_types.get_descendant(self.type_name) is None:
            context.validation.report('policy "{0}" has an unknown type: {1}'.format(
                                        self.name, formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        console.puts('Policy: {0}'.format(context.style.node(self.name)))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type_name)))
            utils.dump_parameters(context, self.properties)
            if self.target_node_ids:
                console.puts('Target nodes:')
                with context.style.indent:
                    for node_id in self.target_node_ids:
                        console.puts(context.style.node(node_id))
            if self.target_group_ids:
                console.puts('Target groups:')
                with context.style.indent:
                    for group_id in self.target_group_ids:
                        console.puts(context.style.node(group_id))


class SubstitutionBase(_InstanceModelMixin):
    """
    An instance of a :class:`SubstitutionTemplate`.

    :ivar node_type_name: Must be represented in the :class:`ModelingContext`
    :ivar mappings: Dict of :class:` SubstitutionMapping`
    """

    __tablename__ = 'substitution'

    node_type_name = Column(Text)

    # region one-to-many relationships

    @declared_attr
    def mappings(cls):
        return cls.one_to_many_relationship('substitution_mapping', key_column_name='name')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('node_type_name', self.node_type_name),
            ('mappings', formatting.as_raw_dict(self.mappings))))

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.node_type_name) is None:
            context.validation.report('substitution "{0}" has an unknown type: {1}'.format(
                                        self.name,  # pylint: disable=no-member
                                        # TODO fix self.name reference
                                        formatting.safe_repr(self.node_type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.mappings)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.mappings, report_issues)

    def dump(self, context):
        console.puts('Substitution:')
        with context.style.indent:
            console.puts('Node type: {0}'.format(context.style.type(self.node_type_name)))
            utils.dump_dict_values(context, self.mappings, 'Mappings')


class SubstitutionMappingBase(_InstanceModelMixin):
    """
    An instance of a :class:`MappingTemplate`.

    :ivar mapped_name: Exposed capability or requirement name
    :ivar node_id: Must be represented in the :class:`ServiceInstance`
    :ivar name: Name of capability or requirement at the node
    """

    __tablename__ = 'substitution_mapping'

    __private_fields__ = ['substitution_fk']

    mapped_name = Column(Text)
    node_id = Column(Text)

    # region foreign keys

    @declared_attr
    def substitution_fk(cls):
        return cls.foreign_key('substitution', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('mapped_name', self.mapped_name),
            ('node_id', self.node_id),
            ('name', self.name)))

    def dump(self, context):
        console.puts('{0} -> {1}.{2}'.format(
                        context.style.node(self.mapped_name),
                        context.style.node(self.node_id),
                        context.style.node(self.name)))


class RelationshipBase(_InstanceModelMixin):
    """
    Connects :class:`Node` to another node.

    An instance of a :class:`RelationshipTemplate`.

    :ivar name: Name (usually the name of the requirement at the source node template)
    :ivar source_requirement_index: Must be represented in the source node template
    :ivar target_node_id: Must be represented in the :class:`ServiceInstance`
    :ivar target_capability_name: Matches the capability at the target node
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar template_name: Must be represented in the :class:`ServiceTemplate`
    :ivar properties: Dict of :class:`Parameter`
    :ivar interfaces: Dict of :class:`Interface`
    """

    __tablename__ = 'relationship'

    __private_fields__ = ['source_node_fk',
                          'target_node_fk']

    source_requirement_index = Column(Integer)
    target_node_id = Column(Text)
    target_capability_name = Column(Text)
    type_name = Column(Text)
    template_name = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    @declared_attr
    def interfaces(cls):
        return cls.one_to_many_relationship('interface', key_column_name='name')

    # region orchestrator required columns

    source_position = Column(Integer)
    target_position = Column(Integer)

    # endregion

    # region foreign keys

    @declared_attr
    def source_node_fk(cls):
        return cls.foreign_key('node', nullable=True)

    @declared_attr
    def target_node_fk(cls):
        return cls.foreign_key('node', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('source_requirement_index', self.source_requirement_index),
            ('target_node_id', self.target_node_id),
            ('target_capability_name', self.target_capability_name),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces))))

    def validate(self, context):
        if self.type_name:
            if context.modeling.relationship_types.get_descendant(self.type_name) is None:
                context.validation.report('relationship "{0}" has an unknown type: {1}'.format(
                                            self.name,
                                            formatting.safe_repr(self.type_name)),
                                          level=validation.Issue.BETWEEN_TYPES)
        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interfaces)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)
        utils.coerce_dict_values(context, container, self.interfaces, report_issues)

    def dump(self, context):
        if self.name:
            if self.source_requirement_index is not None:
                console.puts('{0} ({1:d}) ->'.format(
                                context.style.node(self.name),
                                self.source_requirement_index))
            else:
                console.puts('{0} ->'.format(context.style.node(self.name)))
        else:
            console.puts('->')
        with context.style.indent:
            console.puts('Node: {0}'.format(context.style.node(self.target_node_id)))
            if self.target_capability_name is not None:
                console.puts('Capability: {0}'.format(
                    context.style.node(self.target_capability_name)))
            if self.type_name is not None:
                console.puts('Relationship type: {0}'.format(context.style.type(self.type_name)))
            if self.template_name is not None:
                console.puts('Relationship template: {0}'.format(
                    context.style.node(self.template_name)))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interfaces, 'Interfaces')


class CapabilityBase(_InstanceModelMixin):
    """
    A capability of a :class:`Node`.

    An instance of a :class:`CapabilityTemplate`.

    :ivar name: Name
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar min_occurrences: Minimum number of requirement matches required
    :ivar max_occurrences: Maximum number of requirement matches allowed
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'capability'

    __private_fields__ = ['node_fk']

    type_name = Column(Text)
    min_occurrences = Column(Integer, default=None) # optional
    max_occurrences = Column(Integer, default=None) # optional
    occurrences = Column(Integer, default=0)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    # region foreign_keys

    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node')

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
        if context.modeling.capability_types.get_descendant(self.type_name) is None:
            context.validation.report('capability "{0}" has an unknown type: {1}'.format(
                                        self.name,
                                        formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type_name)))
            console.puts('Occurrences: {0:d} ({1:d}{2})'.format(
                            self.occurrences,
                            self.min_occurrences or 0,
                            ' to {0:d}'.format(self.max_occurrences)
                                if self.max_occurrences is not None
                                else ' or more'))
            utils.dump_parameters(context, self.properties)


class InterfaceBase(_InstanceModelMixin):
    """
    A typed set of :class:`Operation`.

    :ivar name: Name
    :ivar description: Description
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar edge: Edge
    :ivar inputs: Dict of :class:`Parameter`
    :ivar operations: Dict of :class:`Operation`
    """

    __tablename__ = 'interface'

    __private_fields__ = ['node_fk',
                          'group_fk',
                          'relationship_fk']

    description = Column(Text)
    type_name = Column(Text)
    edge = Column(Text)

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs',
                                             key_column_name='name')

    @declared_attr
    def operations(cls):
        return cls.one_to_many_relationship('operation', key_column_name='name')

    # region foreign_keys

    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node', nullable=True)

    @declared_attr
    def group_fk(cls):
        return cls.foreign_key('group', nullable=True)

    @declared_attr
    def relationship_fk(cls):
        return cls.foreign_key('relationship', nullable=True)

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
        if self.type_name:
            if context.modeling.interface_types.get_descendant(self.type_name) is None:
                context.validation.report('interface "{0}" has an unknown type: {1}'.format(
                                            self.name,
                                            formatting.safe_repr(self.type_name)),
                                          level=validation.Issue.BETWEEN_TYPES)

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
            console.puts('Interface type: {0}'.format(context.style.type(self.type_name)))
            utils.dump_parameters(context, self.inputs, 'Inputs')
            utils.dump_dict_values(context, self.operations, 'Operations')


class OperationBase(_InstanceModelMixin):
    """
    An operation in a :class:`Interface`.

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

    __private_fields__ = ['service_fk',
                          'interface_fk']


    description = Column(Text)
    implementation = Column(Text)
    dependencies = Column(modeling_type.StrictList(item_cls=basestring))
    executor = Column(Text)
    max_retries = Column(Integer)
    retry_interval = Column(Integer)

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs',
                                             key_column_name='name')

    plugin = Column(Text)
    operation = Column(Boolean)

    # region foreign_keys

    @declared_attr
    def service_fk(cls):
        return cls.foreign_key('service', nullable=True)

    @declared_attr
    def interface_fk(cls):
        return cls.foreign_key('interface', nullable=True)

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


class ArtifactBase(_InstanceModelMixin):
    """
    A file associated with a :class:`Node`.

    :ivar name: Name
    :ivar description: Description
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar source_path: Source path (CSAR or repository)
    :ivar target_path: Path at destination machine
    :ivar repository_url: Repository URL
    :ivar repository_credential: Dict of string
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'artifact'

    __private_fields__ = ['node_fk']

    description = Column(Text)
    type_name = Column(Text)
    source_path = Column(Text)
    target_path = Column(Text)
    repository_url = Column(Text)
    repository_credential = Column(modeling_type.StrictDict(basestring, basestring))

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    # region foreign_keys

    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node')

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
        if context.modeling.artifact_types.get_descendant(self.type_name) is None:
            context.validation.report('artifact "{0}" has an unknown type: {1}'.format(
                                        self.name,
                                        formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)
        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Artifact type: {0}'.format(context.style.type(self.type_name)))
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
