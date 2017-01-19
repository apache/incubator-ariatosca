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
from sqlalchemy.ext.orderinglist import ordering_list

from aria.parser import validation
from aria.utils import collections, formatting, console

from . import (
    utils,
    structure,
    type as aria_types
)

# pylint: disable=no-self-argument, no-member, abstract-method

# region Element instances


class ServiceInstanceBase(structure.ModelMixin):
    __tablename__ = 'service_instance'

    __private_fields__ = ['substituion_fk',
                          'service_template_fk']

    description = Column(Text)
    _metadata = Column(Text)

    # region orchestrator required columns

    created_at = Column(DateTime, nullable=False, index=True)
    permalink = Column(Text)
    policy_triggers = Column(aria_types.Dict)
    policy_types = Column(aria_types.Dict)
    scaling_groups = Column(aria_types.Dict)
    updated_at = Column(DateTime)
    workflows = Column(aria_types.Dict)

    @declared_attr
    def service_template_name(cls):
        return association_proxy('service_template', 'name')

    # endregion

    # region foreign keys
    @declared_attr
    def substitution_fk(cls):
        return cls.foreign_key('substitution', nullable=True)

    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template')

    # endregion

    # region one-to-one relationships
    @declared_attr
    def substitution(cls):
        return cls.one_to_one_relationship('substitution')
    # endregion

    # region many-to-one relationships
    @declared_attr
    def service_template(cls):
        return cls.many_to_one_relationship('service_template')

    # endregion

    # region many-to-many relationships
    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs')

    @declared_attr
    def outputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='outputs')

    # endregion

    # association proxies

    def satisfy_requirements(self, context):
        satisfied = True
        for node in self.nodes.all():
            if not node.satisfy_requirements(context):
                satisfied = False
        return satisfied

    def validate_capabilities(self, context):
        satisfied = True
        for node in self.nodes.all():
            if not node.validate_capabilities(context):
                satisfied = False
        return satisfied

    def find_nodes(self, node_template_name):
        nodes = []
        for node in self.nodes.all():
            if node.template_name == node_template_name:
                nodes.append(node)
        return collections.FrozenList(nodes)

    def get_node_ids(self, node_template_name):
        return collections.FrozenList((node.id for node in self.find_nodes(node_template_name)))

    def find_groups(self, group_template_name):
        groups = []
        for group in self.groups.all():
            if group.template_name == group_template_name:
                groups.append(group)
        return collections.FrozenList(groups)

    def get_group_ids(self, group_template_name):
        return collections.FrozenList((group.id for group in self.find_groups(group_template_name)))

    def is_node_a_target(self, context, target_node):
        for node in self.nodes.all():
            if self._is_node_a_target(context, node, target_node):
                return True
        return False

    def _is_node_a_target(self, context, source_node, target_node):
        if source_node.relationships:
            for relationship in source_node.relationships:
                if relationship.target_node_id == target_node.id:
                    return True
                else:
                    node = context.modeling.instance.nodes.get(relationship.target_node_id)
                    if node is not None:
                        if self._is_node_a_target(context, node, target_node):
                            return True
        return False


class OperationBase(structure.ModelMixin):
    """
    An operation in a :class:`Interface`.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`implementation`: Implementation string (interpreted by the orchestrator)
    * :code:`dependencies`: List of strings (interpreted by the orchestrator)
    * :code:`executor`: Executor string (interpreted by the orchestrator)
    * :code:`max_retries`: Maximum number of retries allowed in case of failure
    * :code:`retry_interval`: Interval between retries
    * :code:`inputs`: Dict of :class:`Parameter`
    """
    __tablename__ = 'operation'

    __private_fields__ = ['service_template_fk',
                          'interface_instance_fk']

    # region foreign_keys

    @declared_attr
    def service_instance_fk(cls):
        return cls.foreign_key('service_instance', nullable=True)

    @declared_attr
    def interface_instance_fk(cls):
        return cls.foreign_key('interface', nullable=True)

    # endregion
    description = Column(Text)
    implementation = Column(Text)
    dependencies = Column(aria_types.StrictList(item_cls=basestring))

    executor = Column(Text)
    max_retries = Column(Integer, default=None)
    retry_interval = Column(Integer, default=None)
    plugin = Column(Text)
    operation = Column(Boolean)

    # region many-to-one relationships
    @declared_attr
    def service_instance(cls):
        return cls.many_to_one_relationship('service_instance')

    @declared_attr
    def interface(cls):
        return cls.many_to_one_relationship('interface')
    # region many-to-many relationships

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs')

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
                console.puts('Implementation: %s' % context.style.literal(self.implementation))
            if self.dependencies:
                console.puts(
                    'Dependencies: %s'
                    % ', '.join((str(context.style.literal(v)) for v in self.dependencies)))
            if self.executor is not None:
                console.puts('Executor: %s' % context.style.literal(self.executor))
            if self.max_retries is not None:
                console.puts('Max retries: %s' % context.style.literal(self.max_retries))
            if self.retry_interval is not None:
                console.puts('Retry interval: %s' % context.style.literal(self.retry_interval))
            utils.dump_parameters(context, self.inputs, 'Inputs')


class InterfaceBase(structure.ModelMixin):
    """
    A typed set of :class:`Operation`.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`inputs`: Dict of :class:`Parameter`
    * :code:`operations`: Dict of :class:`Operation`
    """
    __tablename__ = 'interface'

    __private_fields__ = ['group_fk',
                          'node_fk',
                          'relationship_fk']


    # region foreign_keys
    @declared_attr
    def group_fk(cls):
        return cls.foreign_key('group', nullable=True)

    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node', nullable=True)

    @declared_attr
    def relationship_fk(cls):
        return cls.foreign_key('relationship', nullable=True)

    # endregion

    description = Column(Text)
    type_name = Column(Text)
    edge = Column(Text)

    # region many-to-one relationships

    @declared_attr
    def node(cls):
        return cls.many_to_one_relationship('node')

    @declared_attr
    def relationship(cls):
        return cls.many_to_one_relationship('relationship')

    @declared_attr
    def group(cls):
        return cls.many_to_one_relationship('group')

    # endregion

    # region many-to-many relationships

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs')

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
                context.validation.report('interface "%s" has an unknown type: %s'
                                          % (self.name,
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
            console.puts('Interface type: %s' % context.style.type(self.type_name))
            utils.dump_parameters(context, self.inputs, 'Inputs')
            utils.dump_dict_values(context, self.operations, 'Operations')


class CapabilityBase(structure.ModelMixin):
    """
    A capability of a :class:`Node`.

    An instance of a :class:`CapabilityTemplate`.

    Properties:

    * :code:`name`: Name
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`min_occurrences`: Minimum number of requirement matches required
    * :code:`max_occurrences`: Maximum number of requirement matches allowed
    * :code:`properties`: Dict of :class:`Parameter`
    """
    __tablename__ = 'capability'

    __private_fields__ = ['node_fk']

    # region foreign_keys
    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node')

    # endregion
    type_name = Column(Text)

    min_occurrences = Column(Integer, default=None) # optional
    max_occurrences = Column(Integer, default=None) # optional
    occurrences = Column(Integer, default=0)

    # region many-to-one relationships
    @declared_attr
    def node(cls):
        return cls.many_to_one_relationship('node')

    # endregion


    # region many-to-many relationships
    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

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
            context.validation.report('capability "%s" has an unknown type: %s'
                                      % (self.name,
                                         formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        with context.style.indent:
            console.puts('Type: %s' % context.style.type(self.type_name))
            console.puts('Occurrences: %s (%s%s)'
                         % (self.occurrences,
                            self.min_occurrences or 0,
                            (' to %d' % self.max_occurrences)
                            if self.max_occurrences is not None
                            else ' or more'))
            utils.dump_parameters(context, self.properties)


class ArtifactBase(structure.ModelMixin):
    """
    A file associated with a :class:`Node`.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`source_path`: Source path (CSAR or repository)
    * :code:`target_path`: Path at destination machine
    * :code:`repository_url`: Repository URL
    * :code:`repository_credential`: Dict of string
    * :code:`properties`: Dict of :class:`Parameter`
    """
    __tablename__ = 'artifact'

    __private_fields__ = ['node_fk']

    # region foreign_keys

    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node')

    # endregion

    description = Column(Text)
    type_name = Column(Text)
    source_path = Column(Text)
    target_path = Column(Text)
    repository_url = Column(Text)
    repository_credential = Column(aria_types.StrictDict(basestring, basestring))

    # region many-to-one relationships
    @declared_attr
    def node(cls):
        return cls.many_to_one_relationship('node')

    # endregion


    # region many-to-many relationships

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

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
            context.validation.report('artifact "%s" has an unknown type: %s'
                                      % (self.name,
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
            console.puts('Artifact type: %s' % context.style.type(self.type_name))
            console.puts('Source path: %s' % context.style.literal(self.source_path))
            if self.target_path is not None:
                console.puts('Target path: %s' % context.style.literal(self.target_path))
            if self.repository_url is not None:
                console.puts('Repository URL: %s' % context.style.literal(self.repository_url))
            if self.repository_credential:
                console.puts('Repository credential: %s'
                             % context.style.literal(self.repository_credential))
            utils.dump_parameters(context, self.properties)


class PolicyBase(structure.ModelMixin):
    """
    An instance of a :class:`PolicyTemplate`.

    Properties:

    * :code:`name`: Name
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`target_node_ids`: Must be represented in the :class:`ServiceInstance`
    * :code:`target_group_ids`: Must be represented in the :class:`ServiceInstance`
    """
    __tablename__ = 'policy'

    __private_fields__ = ['service_instance_fk']

    # region foreign_keys

    @declared_attr
    def service_instance_fk(cls):
        return cls.foreign_key('service_instance')

    # endregion
    type_name = Column(Text)
    target_node_ids = Column(aria_types.StrictList(basestring))
    target_group_ids = Column(aria_types.StrictList(basestring))

    # region many-to-one relationships
    @declared_attr
    def service_instnce(cls):
        return cls.many_to_one_relationship('service_instance')

    # region many-to-many relationships

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

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
            context.validation.report('policy "%s" has an unknown type: %s'
                                      % (self.name, utils.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        console.puts('Policy: %s' % context.style.node(self.name))
        with context.style.indent:
            console.puts('Type: %s' % context.style.type(self.type_name))
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


class GroupPolicyBase(structure.ModelMixin):
    """
    Policies applied to groups.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`triggers`: Dict of :class:`GroupPolicyTrigger`
    """
    __tablename__ = 'group_policy'

    __private_fields__ = ['group_fk']

    # region foreign_keys

    @declared_attr
    def group_fk(cls):
        return cls.foreign_key('group')

    # endregion

    description = Column(Text)
    type_name = Column(Text)

    # region many-to-one relationships
    @declared_attr
    def group(cls):
        return cls.many_to_one_relationship('group')

    # end region

    # region many-to-many relationships
    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('triggers', formatting.as_raw_list(self.triggers))))

    def validate(self, context):
        if context.modeling.policy_types.get_descendant(self.type_name) is None:
            context.validation.report(
                'group policy "%s" has an unknown type: %s'
                % (self.name,
                   formatting.safe_repr(self.type_name)),
                level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.triggers)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)
        utils.coerce_dict_values(context, container, self.triggers, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Group policy type: %s' % context.style.type(self.type_name))
            utils.dump_parameters(context, self.properties)
            utils.dump_dict_values(context, self.triggers, 'Triggers')


class GroupPolicyTriggerBase(structure.ModelMixin):
    """
    Triggers for :class:`GroupPolicy`.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`implementation`: Implementation string (interpreted by the orchestrator)
    * :code:`properties`: Dict of :class:`Parameter`
    """
    __tablename__ = 'group_policy_trigger'

    __private_fields__ = ['group_policy_fk']

    # region foreign keys

    @declared_attr
    def group_policy_fk(cls):
        return cls.foreign_key('group_policy')

    # endregion

    description = Column(Text)
    implementation = Column(Text)

    # region many-to-one relationships

    @declared_attr
    def group_policy(cls):
        return cls.many_to_one_relationship('group_policy')

    # endregion

    # region many-to-many relationships

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('implementation', self.implementation),
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
            console.puts('Implementation: %s' % context.style.literal(self.implementation))
            utils.dump_parameters(context, self.properties)


class MappingBase(structure.ModelMixin):
    """
    An instance of a :class:`MappingTemplate`.

    Properties:

    * :code:`mapped_name`: Exposed capability or requirement name
    * :code:`node_id`: Must be represented in the :class:`ServiceInstance`
    * :code:`name`: Name of capability or requirement at the node
    """
    __tablename__ = 'mapping'

    mapped_name = Column(Text)
    node_id = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('mapped_name', self.mapped_name),
            ('node_id', self.node_id),
            ('name', self.name)))

    def dump(self, context):
        console.puts('%s -> %s.%s'
                     % (context.style.node(self.mapped_name),
                        context.style.node(self.node_id),
                        context.style.node(self.name)))


class SubstitutionBase(structure.ModelMixin):
    """
    An instance of a :class:`SubstitutionTemplate`.

    Properties:

    * :code:`node_type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`capabilities`: Dict of :class:`Mapping`
    * :code:`requirements`: Dict of :class:`Mapping`
    """
    __tablename__ = 'substitution'

    node_type_name = Column(Text)

    # region many-to-many relationships

    @declared_attr
    def capabilities(cls):
        return cls.many_to_many_relationship('mapping', table_prefix='capabilities')

    @declared_attr
    def requirements(cls):
        return cls.many_to_many_relationship('mapping',
                                             table_prefix='requirements',
                                             relationship_kwargs=dict(lazy='dynamic'))


    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('node_type_name', self.node_type_name),
            ('capabilities', formatting.as_raw_list(self.capabilities)),
            ('requirements', formatting.as_raw_list(self.requirements))))

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.node_type_name) is None:
            context.validation.report('substitution "%s" has an unknown type: %s'
                                      % (self.name,  # pylint: disable=no-member
                                         # TODO fix self.name reference
                                         formatting.safe_repr(self.node_type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.capabilities)
        utils.validate_dict_values(context, self.requirements)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.capabilities, report_issues)
        utils.coerce_dict_values(context, container, self.requirements, report_issues)

    def dump(self, context):
        console.puts('Substitution:')
        with context.style.indent:
            console.puts('Node type: %s' % context.style.type(self.node_type_name))
            utils.dump_dict_values(context, self.capabilities, 'Capability mappings')
            utils.dump_dict_values(context, self.requirements, 'Requirement mappings')


# endregion

# region Node instances

class NodeBase(structure.ModelMixin):
    """
    An instance of a :class:`NodeTemplate`.

    Nodes may have zero or more :class:`Relationship` instances to other nodes.

    Properties:

    * :code:`id`: Unique ID (prefixed with the template name)
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`interfaces`: Dict of :class:`Interface`
    * :code:`artifacts`: Dict of :class:`Artifact`
    * :code:`capabilities`: Dict of :class:`CapabilityTemplate`
    * :code:`relationships`: List of :class:`Relationship`
    """
    __tablename__ = 'node'

    __private_fields__ = ['service_instance_fk',
                          'host_fk',
                          'node_template_fk']

    # region foreign_keys
    @declared_attr
    def service_instance_fk(cls):
        return cls.foreign_key('service_instance')

    @declared_attr
    def host_fk(cls):
        return cls.foreign_key('node', nullable=True)

    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template')

    # endregion

    type_name = Column(Text)
    template_name = Column(Text)

    # region orchestrator required columns
    runtime_properties = Column(aria_types.Dict)
    scaling_groups = Column(aria_types.List)
    state = Column(Text, nullable=False)
    version = Column(Integer, default=1)

    @declared_attr
    def plugins(cls):
        return association_proxy('node_template', 'plugins')

    @declared_attr
    def host(cls):
        return cls.relationship_to_self('host_fk')

    @declared_attr
    def service_instance_name(cls):
        return association_proxy('service_instance', 'name')

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
        return association_proxy('service_instance', 'service_template')
    # endregion

    # region many-to-one relationships
    @declared_attr
    def service_instance(cls):
        return cls.many_to_one_relationship('service_instance')

    # endregion

    # region many-to-many relationships

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

    # endregion

    def satisfy_requirements(self, context):
        node_template = context.modeling.model.node_templates.get(self.template_name)
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
                context.validation.report('requirement "%s" of node "%s" has no target node '
                                          'template' % (requirement_template.name,
                                                        self.id),
                                          level=validation.Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    def _satisfy_capability(self, context, target_node_capability, target_node_template,
                            requirement_template, requirement_template_index):
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
                relationship = RelationshipBase(
                    name=requirement_template.name,
                    source_requirement_index=requirement_template_index,
                    target_node_id=target_node.id,
                    target_capability_name=target_capability.name
                )
                self.relationships.append(relationship)
            else:
                context.validation.report('requirement "%s" of node "%s" targets node '
                                          'template "%s" but its instantiated nodes do not '
                                          'have enough capacity'
                                          % (requirement_template.name,
                                             self.id,
                                             target_node_template.name),
                                          level=validation.Issue.BETWEEN_INSTANCES)
                return False
        else:
            context.validation.report('requirement "%s" of node "%s" targets node template '
                                      '"%s" but it has no instantiated nodes'
                                      % (requirement_template.name,
                                         self.id,
                                         target_node_template.name),
                                      level=validation.Issue.BETWEEN_INSTANCES)
            return False

    def validate_capabilities(self, context):
        satisfied = False
        for capability in self.capabilities.itervalues():
            if not capability.has_enough_relationships:
                context.validation.report('capability "%s" of node "%s" requires at least %d '
                                          'relationships but has %d'
                                          % (capability.name,
                                             self.id,
                                             capability.min_occurrences,
                                             capability.occurrences),
                                          level=validation.Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('id', self.id),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces)),
            ('artifacts', formatting.as_raw_list(self.artifacts)),
            ('capabilities', formatting.as_raw_list(self.capabilities)),
            ('relationships', formatting.as_raw_list(self.relationships))))

    def validate(self, context):
        if len(self.id) > context.modeling.id_max_length:
            context.validation.report('"%s" has an ID longer than the limit of %d characters: %d'
                                      % (self.id,
                                         context.modeling.id_max_length,
                                         len(self.id)),
                                      level=validation.Issue.BETWEEN_INSTANCES)

        # TODO: validate that node template is of type?

        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interfaces)
        utils.validate_dict_values(context, self.artifacts)
        utils.validate_dict_values(context, self.capabilities)
        utils.validate_list_values(context, self.relationships)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)
        utils.coerce_dict_values(context, self, self.interfaces, report_issues)
        utils.coerce_dict_values(context, self, self.artifacts, report_issues)
        utils.coerce_dict_values(context, self, self.capabilities, report_issues)
        utils.coerce_list_values(context, self, self.relationships, report_issues)

    def dump(self, context):
        console.puts('Node: %s' % context.style.node(self.id))
        with context.style.indent:
            console.puts('Template: %s' % context.style.node(self.template_name))
            console.puts('Type: %s' % context.style.type(self.type_name))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interfaces)
            utils.dump_dict_values(context, self.artifacts, 'Artifacts')
            utils.dump_dict_values(context, self.capabilities, 'Capabilities')
            utils.dump_list_values(context, self.relationships, 'Relationships')


class GroupBase(structure.ModelMixin):
    """
    An instance of a :class:`GroupTemplate`.

    Properties:

    * :code:`id`: Unique ID (prefixed with the template name)
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`interfaces`: Dict of :class:`Interface`
    * :code:`policies`: Dict of :class:`GroupPolicy`
    * :code:`member_node_ids`: Must be represented in the :class:`ServiceInstance`
    * :code:`member_group_ids`: Must be represented in the :class:`ServiceInstance`
    """
    __tablename__ = 'group'

    __private_fields__ = ['service_instance_fk']

    # region foreign_keys

    @declared_attr
    def service_instance_fk(cls):
        return cls.foreign_key('service_instance')

    # endregion

    type_name = Column(Text)
    template_name = Column(Text)
    member_node_ids = Column(aria_types.StrictList(basestring))
    member_group_ids = Column(aria_types.StrictList(basestring))

    # region many-to-one relationships
    @declared_attr
    def service_instance(cls):
        return cls.many_to_one_relationship('service_instance')

    # region many-to-many relationships
    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('id', self.id),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces)),
            ('policies', formatting.as_raw_list(self.policies)),
            ('member_node_ids', self.member_node_ids),
            ('member_group_ids', self.member_group_ids)))

    def validate(self, context):
        if context.modeling.group_types.get_descendant(self.type_name) is None:
            context.validation.report('group "%s" has an unknown type: %s'
                                      % (self.name,  # pylint: disable=no-member
                                         # TODO fix self.name reference
                                         formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interfaces)
        utils.validate_dict_values(context, self.policies)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)
        utils.coerce_dict_values(context, container, self.interfaces, report_issues)
        utils.coerce_dict_values(context, container, self.policies, report_issues)

    def dump(self, context):
        console.puts('Group: %s' % context.style.node(self.id))
        with context.style.indent:
            console.puts('Type: %s' % context.style.type(self.type_name))
            console.puts('Template: %s' % context.style.type(self.template_name))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interfaces)
            utils.dump_dict_values(context, self.policies, 'Policies')
            if self.member_node_ids:
                console.puts('Member nodes:')
                with context.style.indent:
                    for node_id in self.member_node_ids:
                        console.puts(context.style.node(node_id))

# endregion

# region Relationship instances


class RelationshipBase(structure.ModelMixin):
    """
    Connects :class:`Node` to another node.

    An instance of a :class:`RelationshipTemplate`.

    Properties:

    * :code:`name`: Name (usually the name of the requirement at the source node template)
    * :code:`source_requirement_index`: Must be represented in the source node template
    * :code:`target_node_id`: Must be represented in the :class:`ServiceInstance`
    * :code:`target_capability_name`: Matches the capability at the target node
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`source_interfaces`: Dict of :class:`Interface`
    * :code:`target_interfaces`: Dict of :class:`Interface`
    """
    __tablename__ = 'relationship'

    __private_fields__ = ['source_node_fk',
                          'target_node_fk']

    source_requirement_index = Column(Integer)
    target_node_id = Column(Text)
    target_capability_name = Column(Text)
    type_name = Column(Text)
    template_name = Column(Text)

    # # region orchestrator required columns
    source_position = Column(Integer)
    target_position = Column(Integer)

    @declared_attr
    def source_node_fk(cls):
        return cls.foreign_key('node', nullable=True)

    @declared_attr
    def source_node(cls):
        return cls.many_to_one_relationship(
            'node',
            'source_node_fk',
            backreference='outbound_relationships',
            backref_kwargs=dict(
                order_by=cls.source_position,
                collection_class=ordering_list('source_position', count_from=0),
            )
        )

    @declared_attr
    def source_node_name(cls):
        return association_proxy('source_node', cls.name_column_name())

    @declared_attr
    def target_node_fk(cls):
        return cls.foreign_key('node', nullable=True)

    @declared_attr
    def target_node(cls):
        return cls.many_to_one_relationship(
            'node',
            'target_node_fk',
            backreference='inbound_relationships',
            backref_kwargs=dict(
                order_by=cls.target_position,
                collection_class=ordering_list('target_position', count_from=0),
            )
        )

    @declared_attr
    def target_node_name(cls):
        return association_proxy('target_node', cls.name_column_name())
    # endregion

    # region many-to-many relationship

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

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
            ('source_interfaces', formatting.as_raw_list(self.source_interfaces)),
            ('target_interfaces', formatting.as_raw_list(self.target_interfaces))))

    def validate(self, context):
        if self.type_name:
            if context.modeling.relationship_types.get_descendant(self.type_name) is None:
                context.validation.report('relationship "%s" has an unknown type: %s'
                                          % (self.name,
                                             formatting.safe_repr(self.type_name)),
                                          level=validation.Issue.BETWEEN_TYPES)
        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.source_interfaces)
        utils.validate_dict_values(context, self.target_interfaces)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.properties, report_issues)
        utils.coerce_dict_values(context, container, self.source_interfaces, report_issues)
        utils.coerce_dict_values(context, container, self.target_interfaces, report_issues)

    def dump(self, context):
        if self.name:
            if self.source_requirement_index is not None:
                console.puts('%s (%d) ->' % (
                    context.style.node(self.name),
                    self.source_requirement_index))
            else:
                console.puts('%s ->' % context.style.node(self.name))
        else:
            console.puts('->')
        with context.style.indent:
            console.puts('Node: %s' % context.style.node(self.target_node_id))
            if self.target_capability_name is not None:
                console.puts('Capability: %s' % context.style.node(self.target_capability_name))
            if self.type_name is not None:
                console.puts('Relationship type: %s' % context.style.type(self.type_name))
            if self.template_name is not None:
                console.puts('Relationship template: %s' % context.style.node(self.template_name))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.source_interfaces, 'Source interfaces')
            utils.dump_interfaces(context, self.target_interfaces, 'Target interfaces')

# endregion
