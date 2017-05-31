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

# pylint: disable=too-many-lines, no-self-argument, no-member, abstract-method

from sqlalchemy import (
    Column,
    Text,
    Integer,
    Enum,
    Boolean
)
from sqlalchemy import DateTime
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.orderinglist import ordering_list

from .mixins import InstanceModelMixin
from ..orchestrator import execution_plugin
from ..parser import validation
from ..parser.consumption import ConsumptionContext
from ..utils import (
    collections,
    formatting,
    console
)
from . import (
    relationship,
    utils,
    types as modeling_types
)


class ServiceBase(InstanceModelMixin):
    """
    A service is usually an instance of a :class:`ServiceTemplate`.

    You will usually not create it programmatically, but instead instantiate it from a service
    template.

    :ivar name: Name (unique for this ARIA installation)
    :vartype name: basestring
    :ivar service_template: Template from which this service was instantiated (optional)
    :vartype service_template: :class:`ServiceTemplate`
    :ivar description: Human-readable description
    :vartype description: string
    :ivar meta_data: Custom annotations
    :vartype meta_data: {basestring: :class:`Metadata`}
    :ivar node: Nodes
    :vartype node: {basestring: :class:`Node`}
    :ivar groups: Groups of nodes
    :vartype groups: {basestring: :class:`Group`}
    :ivar policies: Policies
    :vartype policies: {basestring: :class:`Policy`]}
    :ivar substitution: The entire service can appear as a node
    :vartype substitution: :class:`Substitution`
    :ivar inputs: Externally provided parameters
    :vartype inputs: {basestring: :class:`Parameter`}
    :ivar outputs: These parameters are filled in after service installation
    :vartype outputs: {basestring: :class:`Parameter`}
    :ivar workflows: Custom workflows that can be performed on the service
    :vartype workflows: {basestring: :class:`Operation`}
    :ivar plugins: Plugins used by the service
    :vartype plugins: {basestring: :class:`Plugin`}
    :ivar created_at: Creation timestamp
    :vartype created_at: :class:`datetime.datetime`
    :ivar updated_at: Update timestamp
    :vartype updated_at: :class:`datetime.datetime`
    :ivar modifications: Modifications of this service
    :vartype modifications: [:class:`ServiceModification`]
    :ivar updates: Updates of this service
    :vartype updates: [:class:`ServiceUpdate`]
    :ivar executions: Executions on this service
    :vartype executions: [:class:`Execution`]
    """

    __tablename__ = 'service'

    __private_fields__ = ['substitution_fk',
                          'service_template_fk']

    # region foreign keys

    @declared_attr
    def substitution_fk(cls):
        """Service one-to-one to Substitution"""
        return relationship.foreign_key('substitution', nullable=True)

    @declared_attr
    def service_template_fk(cls):
        """For Service many-to-one to ServiceTemplate"""
        return relationship.foreign_key('service_template', nullable=True)

    # endregion

    # region association proxies

    @declared_attr
    def service_template_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('service_template', 'name')

    # endregion

    # region one_to_one relationships

    @declared_attr
    def substitution(cls):
        return relationship.one_to_one(cls, 'substitution', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region one_to_many relationships

    @declared_attr
    def updates(cls):
        return relationship.one_to_many(cls, 'service_update')

    @declared_attr
    def modifications(cls):
        return relationship.one_to_many(cls, 'service_modification')

    @declared_attr
    def executions(cls):
        return relationship.one_to_many(cls, 'execution')

    @declared_attr
    def nodes(cls):
        return relationship.one_to_many(cls, 'node', dict_key='name')

    @declared_attr
    def groups(cls):
        return relationship.one_to_many(cls, 'group', dict_key='name')

    @declared_attr
    def policies(cls):
        return relationship.one_to_many(cls, 'policy', dict_key='name')

    @declared_attr
    def workflows(cls):
        return relationship.one_to_many(cls, 'operation', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        return relationship.many_to_one(cls, 'service_template')

    # endregion

    # region many_to_many relationships

    @declared_attr
    def meta_data(cls):
        # Warning! We cannot use the attr name "metadata" because it's used by SQLAlchemy!
        return relationship.many_to_many(cls, 'metadata', dict_key='name')

    @declared_attr
    def inputs(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='inputs', dict_key='name')

    @declared_attr
    def outputs(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='outputs', dict_key='name')

    @declared_attr
    def plugins(cls):
        return relationship.many_to_many(cls, 'plugin', dict_key='name')

    # endregion

    description = Column(Text)
    created_at = Column(DateTime, nullable=False, index=True)
    updated_at = Column(DateTime)

    def satisfy_requirements(self):
        satisfied = True
        for node in self.nodes.itervalues():
            if not node.satisfy_requirements():
                satisfied = False
        return satisfied

    def validate_capabilities(self):
        satisfied = True
        for node in self.nodes.itervalues():
            if not node.validate_capabilities():
                satisfied = False
        return satisfied

    def find_hosts(self):
        for node in self.nodes.itervalues():
            node.find_host()

    def configure_operations(self):
        for node in self.nodes.itervalues():
            node.configure_operations()
        for group in self.groups.itervalues():
            group.configure_operations()
        for operation in self.workflows.itervalues():
            operation.configure()

    def is_node_a_target(self, target_node):
        for node in self.nodes.itervalues():
            if self._is_node_a_target(node, target_node):
                return True
        return False

    def _is_node_a_target(self, source_node, target_node):
        if source_node.outbound_relationships:
            for relationship_model in source_node.outbound_relationships:
                if relationship_model.target_node.name == target_node.name:
                    return True
                else:
                    node = relationship_model.target_node
                    if node is not None:
                        if self._is_node_a_target(node, target_node):
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
            ('workflows', formatting.as_raw_list(self.workflows))))

    def validate(self):
        utils.validate_dict_values(self.meta_data)
        utils.validate_dict_values(self.nodes)
        utils.validate_dict_values(self.groups)
        utils.validate_dict_values(self.policies)
        if self.substitution is not None:
            self.substitution.validate()
        utils.validate_dict_values(self.inputs)
        utils.validate_dict_values(self.outputs)
        utils.validate_dict_values(self.workflows)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.meta_data, report_issues)
        utils.coerce_dict_values(self.nodes, report_issues)
        utils.coerce_dict_values(self.groups, report_issues)
        utils.coerce_dict_values(self.policies, report_issues)
        if self.substitution is not None:
            self.substitution.coerce_values(report_issues)
        utils.coerce_dict_values(self.inputs, report_issues)
        utils.coerce_dict_values(self.outputs, report_issues)
        utils.coerce_dict_values(self.workflows, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        if self.description is not None:
            console.puts(context.style.meta(self.description))
        utils.dump_dict_values(self.meta_data, 'Metadata')
        for node in self.nodes.itervalues():
            node.dump()
        for group in self.groups.itervalues():
            group.dump()
        for policy in self.policies.itervalues():
            policy.dump()
        if self.substitution is not None:
            self.substitution.dump()
        utils.dump_dict_values(self.inputs, 'Inputs')
        utils.dump_dict_values(self.outputs, 'Outputs')
        utils.dump_dict_values(self.workflows, 'Workflows')

    def dump_graph(self):
        for node in self.nodes.itervalues():
            if not self.is_node_a_target(node):
                self._dump_graph_node(node)

    def _dump_graph_node(self, node, capability=None):
        context = ConsumptionContext.get_thread_local()
        console.puts(context.style.node(node.name))
        if capability is not None:
            console.puts('{0} ({1})'.format(context.style.property(capability.name),
                                            context.style.type(capability.type.name)))
        if node.outbound_relationships:
            with context.style.indent:
                for relationship_model in node.outbound_relationships:
                    relationship_name = context.style.property(relationship_model.name)
                    if relationship_model.type is not None:
                        console.puts('-> {0} ({1})'.format(relationship_name,
                                                           context.style.type(
                                                               relationship_model.type.name)))
                    else:
                        console.puts('-> {0}'.format(relationship_name))
                    with console.indent(3):
                        self._dump_graph_node(relationship_model.target_node,
                                              relationship_model.target_capability)


class NodeBase(InstanceModelMixin):
    """
    Usually an instance of a :class:`NodeTemplate`.

    Nodes may have zero or more :class:`Relationship` instances to other nodes.

    :ivar name: Name (unique for this service)
    :vartype name: basestring
    :ivar node_template: Template from which this node was instantiated (optional)
    :vartype node_template: :class:`NodeTemplate`
    :ivar type: Node type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: string
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar interfaces: Bundles of operations
    :vartype interfaces: {basestring: :class:`Interface`}
    :ivar artifacts: Associated files
    :vartype artifacts: {basestring: :class:`Artifact`}
    :ivar capabilities: Exposed capabilities
    :vartype capabilities: {basestring: :class:`Capability`}
    :ivar outbound_relationships: Relationships to other nodes
    :vartype outbound_relationships: [:class:`Relationship`]
    :ivar inbound_relationships: Relationships from other nodes
    :vartype inbound_relationships: [:class:`Relationship`]
    :ivar host: Host node (can be self)
    :vartype host: :class:`Node`
    :ivar state: The state of the node, according to to the TOSCA-defined node states
    :vartype state: string
    :ivar version: Used by `aria.storage.instrumentation`
    :vartype version: int
    :ivar service: Containing service
    :vartype service: :class:`Service`
    :ivar groups: We are a member of these groups
    :vartype groups: [:class:`Group`]
    :ivar policies: Policies enacted on this node
    :vartype policies: [:class:`Policy`]
    :ivar substitution_mapping: Our contribution to service substitution
    :vartype substitution_mapping: :class:`SubstitutionMapping`
    :ivar tasks: Tasks for this node
    :vartype tasks: [:class:`Task`]
    :ivar hosted_tasks: Tasks on this node
    :vartype hosted_tasks: [:class:`Task`]
    """

    __tablename__ = 'node'

    __private_fields__ = ['type_fk',
                          'host_fk',
                          'service_fk',
                          'node_template_fk']

    INITIAL = 'initial'
    CREATING = 'creating'
    CREATED = 'created'
    CONFIGURING = 'configuring'
    CONFIGURED = 'configured'
    STARTING = 'starting'
    STARTED = 'started'
    STOPPING = 'stopping'
    DELETING = 'deleting'
    # 'deleted' isn't actually part of the tosca spec, since according the description of the
    # 'deleting' state: "Node is transitioning from its current state to one where it is deleted and
    #  its state is no longer tracked by the instance model."
    # However, we prefer to be able to retrieve information about deleted nodes, so we chose to add
    # this 'deleted' state to enable us to do so.
    DELETED = 'deleted'
    ERROR = 'error'

    STATES = [INITIAL, CREATING, CREATED, CONFIGURING, CONFIGURED, STARTING, STARTED, STOPPING,
              DELETING, DELETED, ERROR]

    _op_to_state = {'create': {'transitional': CREATING, 'finished': CREATED},
                    'configure': {'transitional': CONFIGURING, 'finished': CONFIGURED},
                    'start': {'transitional': STARTING, 'finished': STARTED},
                    'stop': {'transitional': STOPPING, 'finished': CONFIGURED},
                    'delete': {'transitional': DELETING, 'finished': DELETED}}

    @classmethod
    def determine_state(cls, op_name, is_transitional):
        """ :returns the state the node should be in as a result of running the
            operation on this node.

            e.g. if we are running tosca.interfaces.node.lifecycle.Standard.create, then
            the resulting state should either 'creating' (if the task just started) or 'created'
            (if the task ended).

            If the operation is not a standard tosca lifecycle operation, then we return None"""

        state_type = 'transitional' if is_transitional else 'finished'
        try:
            return cls._op_to_state[op_name][state_type]
        except KeyError:
            return None

    def is_available(self):
        return self.state not in (self.INITIAL, self.DELETED, self.ERROR)

    # region foreign_keys

    @declared_attr
    def type_fk(cls):
        """For Node many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def host_fk(cls):
        """For Node one-to-one to Node"""
        return relationship.foreign_key('node', nullable=True)

    @declared_attr
    def service_fk(cls):
        """For Service one-to-many to Node"""
        return relationship.foreign_key('service')

    @declared_attr
    def node_template_fk(cls):
        """For Node many-to-one to NodeTemplate"""
        return relationship.foreign_key('node_template')

    # endregion

    # region association proxies

    @declared_attr
    def service_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('service', 'name')

    @declared_attr
    def node_template_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('node_template', 'name')

    # endregion

    # region one_to_one relationships

    @declared_attr
    def host(cls): # pylint: disable=method-hidden
        return relationship.one_to_one_self(cls, 'host_fk')

    # endregion

    # region one_to_many relationships

    @declared_attr
    def tasks(cls):
        return relationship.one_to_many(cls, 'task')

    @declared_attr
    def interfaces(cls):
        return relationship.one_to_many(cls, 'interface', dict_key='name')

    @declared_attr
    def artifacts(cls):
        return relationship.one_to_many(cls, 'artifact', dict_key='name')

    @declared_attr
    def capabilities(cls):
        return relationship.one_to_many(cls, 'capability', dict_key='name')

    @declared_attr
    def outbound_relationships(cls):
        return relationship.one_to_many(
            cls, 'relationship', child_fk='source_node_fk', back_populates='source_node',
            rel_kwargs=dict(
                order_by='Relationship.source_position',
                collection_class=ordering_list('source_position', count_from=0)
            )
        )

    @declared_attr
    def inbound_relationships(cls):
        return relationship.one_to_many(
            cls, 'relationship', child_fk='target_node_fk', back_populates='target_node',
            rel_kwargs=dict(
                order_by='Relationship.target_position',
                collection_class=ordering_list('target_position', count_from=0)
            )
        )

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service(cls):
        return relationship.many_to_one(cls, 'service')

    @declared_attr
    def node_template(cls):
        return relationship.many_to_one(cls, 'node_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships
    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')

    @declared_attr
    def attributes(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='attributes', dict_key='name')

    # endregion

    description = Column(Text)
    state = Column(Enum(*STATES, name='node_state'), nullable=False, default=INITIAL)
    version = Column(Integer, default=1)

    __mapper_args__ = {'version_id_col': version} # Enable SQLAlchemy automatic version counting

    @property
    def host_address(self):
        if self.host and self.host.attributes:
            attribute = self.host.attributes.get('ip')
            return attribute.value if attribute else None
        return None

    def satisfy_requirements(self):
        node_template = self.node_template
        satisfied = True
        for requirement_template in node_template.requirement_templates:
            # Find target template
            target_node_template, target_node_capability = \
                requirement_template.find_target(node_template)
            if target_node_template is not None:
                satisfied = self._satisfy_capability(target_node_capability,
                                                     target_node_template,
                                                     requirement_template)
            else:
                context = ConsumptionContext.get_thread_local()
                context.validation.report('requirement "{0}" of node "{1}" has no target node '
                                          'template'.format(requirement_template.name, self.name),
                                          level=validation.Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    def _satisfy_capability(self, target_node_capability, target_node_template,
                            requirement_template):
        from . import models
        context = ConsumptionContext.get_thread_local()
        # Find target nodes
        target_nodes = target_node_template.nodes
        if target_nodes:
            target_node = None
            target_capability = None

            if target_node_capability is not None:
                # Relate to the first target node that has capacity
                for node in target_nodes:
                    a_target_capability = node.capabilities.get(target_node_capability.name)
                    if a_target_capability.relate():
                        target_node = node
                        target_capability = a_target_capability
                        break
            else:
                # Use first target node
                target_node = target_nodes[0]

            if target_node is not None:
                if requirement_template.relationship_template is not None:
                    relationship_model = \
                        requirement_template.relationship_template.instantiate(self)
                else:
                    relationship_model = models.Relationship()
                relationship_model.name = requirement_template.name
                relationship_model.requirement_template = requirement_template
                relationship_model.target_node = target_node
                relationship_model.target_capability = target_capability
                self.outbound_relationships.append(relationship_model)
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

    def validate_capabilities(self):
        context = ConsumptionContext.get_thread_local()
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

    def find_host(self):
        def _find_host(node):
            if node.type.role == 'host':
                return node
            for the_relationship in node.outbound_relationships:
                if (the_relationship.target_capability is not None) and \
                    the_relationship.target_capability.type.role == 'host':
                    host = _find_host(the_relationship.target_node)
                    if host is not None:
                        return host
            for the_relationship in node.inbound_relationships:
                if (the_relationship.target_capability is not None) and \
                    the_relationship.target_capability.type.role == 'feature':
                    host = _find_host(the_relationship.source_node)
                    if host is not None:
                        return host
            return None

        self.host = _find_host(self)

    def configure_operations(self):
        for interface in self.interfaces.itervalues():
            interface.configure_operations()
        for the_relationship in self.outbound_relationships:
            the_relationship.configure_operations()

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('attributes', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces)),
            ('artifacts', formatting.as_raw_list(self.artifacts)),
            ('capabilities', formatting.as_raw_list(self.capabilities)),
            ('relationships', formatting.as_raw_list(self.outbound_relationships))))

    def validate(self):
        context = ConsumptionContext.get_thread_local()
        if len(self.name) > context.modeling.id_max_length:
            context.validation.report('"{0}" has an ID longer than the limit of {1:d} characters: '
                                      '{2:d}'.format(
                                          self.name,
                                          context.modeling.id_max_length,
                                          len(self.name)),
                                      level=validation.Issue.BETWEEN_INSTANCES)

        # TODO: validate that node template is of type?

        utils.validate_dict_values(self.properties)
        utils.validate_dict_values(self.attributes)
        utils.validate_dict_values(self.interfaces)
        utils.validate_dict_values(self.artifacts)
        utils.validate_dict_values(self.capabilities)
        utils.validate_list_values(self.outbound_relationships)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)
        utils.coerce_dict_values(self.attributes, report_issues)
        utils.coerce_dict_values(self.interfaces, report_issues)
        utils.coerce_dict_values(self.artifacts, report_issues)
        utils.coerce_dict_values(self.capabilities, report_issues)
        utils.coerce_list_values(self.outbound_relationships, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('Node: {0}'.format(context.style.node(self.name)))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            console.puts('Template: {0}'.format(context.style.node(self.node_template.name)))
            utils.dump_dict_values(self.properties, 'Properties')
            utils.dump_dict_values(self.attributes, 'Attributes')
            utils.dump_interfaces(self.interfaces)
            utils.dump_dict_values(self.artifacts, 'Artifacts')
            utils.dump_dict_values(self.capabilities, 'Capabilities')
            utils.dump_list_values(self.outbound_relationships, 'Relationships')


class GroupBase(InstanceModelMixin):
    """
    Usually an instance of a :class:`GroupTemplate`.

    :ivar name: Name (unique for this service)
    :vartype name: basestring
    :ivar group_template: Template from which this group was instantiated (optional)
    :vartype group_template: :class:`GroupTemplate`
    :ivar type: Group type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: string
    :ivar nodes: Members of this group
    :vartype nodes: [:class:`Node`]
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar interfaces: Bundles of operations
    :vartype interfaces: {basestring: :class:`Interface`}
    :ivar service: Containing service
    :vartype service: :class:`Service`
    :ivar policies: Policies enacted on this group
    :vartype policies: [:class:`Policy`]
    """

    __tablename__ = 'group'

    __private_fields__ = ['type_fk', 'service_fk', 'group_template_fk']

    # region foreign_keys

    @declared_attr
    def type_fk(cls):
        """For Group many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def service_fk(cls):
        """For Service one-to-many to Group"""
        return relationship.foreign_key('service')

    @declared_attr
    def group_template_fk(cls):
        """For Group many-to-one to GroupTemplate"""
        return relationship.foreign_key('group_template', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def interfaces(cls):
        return relationship.one_to_many(cls, 'interface', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service(cls):
        return relationship.many_to_one(cls, 'service')

    @declared_attr
    def group_template(cls):
        return relationship.many_to_one(cls, 'group_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def nodes(cls):
        return relationship.many_to_many(cls, 'node')

    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')

    # endregion

    description = Column(Text)

    def configure_operations(self):
        for interface in self.interfaces.itervalues():
            interface.configure_operations()

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces))))

    def validate(self):
        utils.validate_dict_values(self.properties)
        utils.validate_dict_values(self.interfaces)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)
        utils.coerce_dict_values(self.interfaces, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('Group: {0}'.format(context.style.node(self.name)))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_dict_values(self.properties, 'Properties')
            utils.dump_interfaces(self.interfaces)
            if self.nodes:
                console.puts('Member nodes:')
                with context.style.indent:
                    for node in self.nodes:
                        console.puts(context.style.node(node.name))


class PolicyBase(InstanceModelMixin):
    """
    Usually an instance of a :class:`PolicyTemplate`.

    :ivar name: Name (unique for this service)
    :vartype name: basestring
    :ivar policy_template: Template from which this policy was instantiated (optional)
    :vartype policy_template: :class:`PolicyTemplate`
    :ivar type: Policy type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: string
    :ivar nodes: Policy will be enacted on all these nodes
    :vartype nodes: [:class:`Node`]
    :ivar groups: Policy will be enacted on all nodes in these groups
    :vartype groups: [:class:`Group`]
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar service: Containing service
    :vartype service: :class:`Service`
    """

    __tablename__ = 'policy'

    __private_fields__ = ['type_fk', 'service_fk', 'policy_template_fk']

    # region foreign_keys

    @declared_attr
    def type_fk(cls):
        """For Policy many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def service_fk(cls):
        """For Service one-to-many to Policy"""
        return relationship.foreign_key('service')

    @declared_attr
    def policy_template_fk(cls):
        """For Policy many-to-one to PolicyTemplate"""
        return relationship.foreign_key('policy_template', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service(cls):
        return relationship.many_to_one(cls, 'service')

    @declared_attr
    def policy_template(cls):
        return relationship.many_to_one(cls, 'policy_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')

    @declared_attr
    def nodes(cls):
        return relationship.many_to_many(cls, 'node')

    @declared_attr
    def groups(cls):
        return relationship.many_to_many(cls, 'group')

    # endregion

    description = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties))))

    def validate(self):
        utils.validate_dict_values(self.properties)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('Policy: {0}'.format(context.style.node(self.name)))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_dict_values(self.properties, 'Properties')
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
    Used to substitute a single node for the entire deployment.

    Usually an instance of a :class:`SubstitutionTemplate`.

    :ivar substitution_template: Template from which this substitution was instantiated (optional)
    :vartype substitution_template: :class:`SubstitutionTemplate`
    :ivar node_type: Exposed node type
    :vartype node_type: :class:`Type`
    :ivar mappings: Requirement and capability mappings
    :vartype mappings: {basestring: :class:`SubstitutionTemplate`}
    :ivar service: Containing service
    :vartype service: :class:`Service`
    """

    __tablename__ = 'substitution'

    __private_fields__ = ['node_type_fk',
                          'substitution_template_fk']

    # region foreign_keys

    @declared_attr
    def node_type_fk(cls):
        """For Substitution many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def substitution_template_fk(cls):
        """For Substitution many-to-one to SubstitutionTemplate"""
        return relationship.foreign_key('substitution_template', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def mappings(cls):
        return relationship.one_to_many(cls, 'substitution_mapping', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service(cls):
        return relationship.one_to_one(cls, 'service', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def substitution_template(cls):
        return relationship.many_to_one(cls, 'substitution_template')

    @declared_attr
    def node_type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('node_type_name', self.node_type.name),
            ('mappings', formatting.as_raw_dict(self.mappings))))

    def validate(self):
        utils.validate_dict_values(self.mappings)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.mappings, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('Substitution:')
        with context.style.indent:
            console.puts('Node type: {0}'.format(context.style.type(self.node_type.name)))
            utils.dump_dict_values(self.mappings, 'Mappings')


class SubstitutionMappingBase(InstanceModelMixin):
    """
    Used by :class:`Substitution` to map a capability or a requirement to a node.

    Only one of `capability_template` and `requirement_template` can be set.

    Usually an instance of a :class:`SubstitutionTemplate`.

    :ivar name: Exposed capability or requirement name
    :vartype name: basestring
    :ivar node: Node
    :vartype node: :class:`Node`
    :ivar capability: Capability in the node
    :vartype capability: :class:`Capability`
    :ivar requirement_template: Requirement template in the node template
    :vartype requirement_template: :class:`RequirementTemplate`
    :ivar substitution: Containing substitution
    :vartype substitution: :class:`Substitution`
    """

    __tablename__ = 'substitution_mapping'

    __private_fields__ = ['substitution_fk',
                          'node_fk',
                          'capability_fk',
                          'requirement_template_fk']

    # region foreign keys

    @declared_attr
    def substitution_fk(cls):
        """For Substitution one-to-many to SubstitutionMapping"""
        return relationship.foreign_key('substitution')

    @declared_attr
    def node_fk(cls):
        """For Substitution one-to-one to NodeTemplate"""
        return relationship.foreign_key('node')

    @declared_attr
    def capability_fk(cls):
        """For Substitution one-to-one to Capability"""
        return relationship.foreign_key('capability', nullable=True)

    @declared_attr
    def requirement_template_fk(cls):
        """For Substitution one-to-one to RequirementTemplate"""
        return relationship.foreign_key('requirement_template', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    @declared_attr
    def substitution(cls):
        return relationship.many_to_one(cls, 'substitution', back_populates='mappings')

    @declared_attr
    def node(cls):
        return relationship.one_to_one(cls, 'node', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def capability(cls):
        return relationship.one_to_one(cls, 'capability', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def requirement_template(cls):
        return relationship.one_to_one(
            cls, 'requirement_template', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region one_to_many relationships

    # endregion

    # region many_to_one relationships

    # endregion

    # region many_to_many relationships

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),))

    def coerce_values(self, report_issues):
        pass

    def validate(self):
        context = ConsumptionContext.get_thread_local()
        if (self.capability is None) and (self.requirement_template is None):
            context.validation.report('mapping "{0}" refers to neither capability nor a requirement'
                                      ' in node: {1}'.format(
                                          self.name,
                                          formatting.safe_repr(self.node.name)),
                                      level=validation.Issue.BETWEEN_TYPES)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('{0} -> {1}.{2}'.format(
            context.style.node(self.name),
            context.style.node(self.node.name),
            context.style.node(self.capability.name
                               if self.capability
                               else self.requirement_template.name)))


class RelationshipBase(InstanceModelMixin):
    """
    Connects :class:`Node` to a capability in another node.

    Might be an instance of a :class:`RelationshipTemplate`.

    :ivar name: Name (usually the name of the requirement at the source node template)
    :vartype name: basestring
    :ivar relationship_template: Template from which this relationship was instantiated (optional)
    :vartype relationship_template: :class:`RelationshipTemplate`
    :ivar requirement_template: Template from which this relationship was instantiated (optional)
    :vartype requirement_template: :class:`RequirementTemplate`
    :ivar type: Relationship type
    :vartype type: :class:`Type`
    :ivar target_capability: Capability at the target node (optional)
    :vartype target_capability: :class:`Capability`
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar interfaces: Bundles of operations
    :vartype interfaces: {basestring: :class:`Interfaces`}
    :ivar source_position: The position of the relationship in the outbound relationships.
    :vartype source_position: int
    :ivar target_position: The position of the relationship in the inbound relationships.
    :vartype target_position: int
    :ivar source_node: Source node
    :vartype source_node: :class:`Node`
    :ivar target_node: Target node
    :vartype target_node: :class:`Node`
    :ivar tasks: Tasks for this relationship
    :vartype tasks: [:class:`Task`]
    """

    __tablename__ = 'relationship'

    __private_fields__ = ['type_fk',
                          'source_node_fk',
                          'target_node_fk',
                          'target_capability_fk',
                          'requirement_template_fk',
                          'relationship_template_fk',
                          'target_position',
                          'source_position']

    # region foreign keys

    @declared_attr
    def type_fk(cls):
        """For Relationship many-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    @declared_attr
    def source_node_fk(cls):
        """For Node one-to-many to Relationship"""
        return relationship.foreign_key('node')

    @declared_attr
    def target_node_fk(cls):
        """For Node one-to-many to Relationship"""
        return relationship.foreign_key('node')

    @declared_attr
    def target_capability_fk(cls):
        """For Relationship one-to-one to Capability"""
        return relationship.foreign_key('capability', nullable=True)

    @declared_attr
    def requirement_template_fk(cls):
        """For Relationship many-to-one to RequirementTemplate"""
        return relationship.foreign_key('requirement_template', nullable=True)

    @declared_attr
    def relationship_template_fk(cls):
        """For Relationship many-to-one to RelationshipTemplate"""
        return relationship.foreign_key('relationship_template', nullable=True)

    # endregion

    # region association proxies

    @declared_attr
    def source_node_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('source_node', 'name')

    @declared_attr
    def target_node_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('target_node', 'name')

    # endregion

    # region one_to_one relationships

    @declared_attr
    def target_capability(cls):
        return relationship.one_to_one(cls, 'capability', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region one_to_many relationships

    @declared_attr
    def tasks(cls):
        return relationship.one_to_many(cls, 'task')

    @declared_attr
    def interfaces(cls):
        return relationship.one_to_many(cls, 'interface', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def source_node(cls):
        return relationship.many_to_one(
            cls, 'node', fk='source_node_fk', back_populates='outbound_relationships')

    @declared_attr
    def target_node(cls):
        return relationship.many_to_one(
            cls, 'node', fk='target_node_fk', back_populates='inbound_relationships')

    @declared_attr
    def relationship_template(cls):
        return relationship.many_to_one(cls, 'relationship_template')

    @declared_attr
    def requirement_template(cls):
        return relationship.many_to_one(cls, 'requirement_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')

    # endregion

    source_position = Column(Integer)
    target_position = Column(Integer)

    def configure_operations(self):
        for interface in self.interfaces.itervalues():
            interface.configure_operations()

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('target_node_id', self.target_node.name),
            ('type_name', self.type.name
             if self.type is not None else None),
            ('template_name', self.relationship_template.name
             if self.relationship_template is not None else None),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interfaces', formatting.as_raw_list(self.interfaces))))

    def validate(self):
        utils.validate_dict_values(self.properties)
        utils.validate_dict_values(self.interfaces)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)
        utils.coerce_dict_values(self.interfaces, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        if self.name:
            console.puts('{0} ->'.format(context.style.node(self.name)))
        else:
            console.puts('->')
        with context.style.indent:
            console.puts('Node: {0}'.format(context.style.node(self.target_node.name)))
            if self.target_capability:
                console.puts('Capability: {0}'.format(context.style.node(
                    self.target_capability.name)))
            if self.type is not None:
                console.puts('Relationship type: {0}'.format(context.style.type(self.type.name)))
            if (self.relationship_template is not None) and self.relationship_template.name:
                console.puts('Relationship template: {0}'.format(
                    context.style.node(self.relationship_template.name)))
            utils.dump_dict_values(self.properties, 'Properties')
            utils.dump_interfaces(self.interfaces, 'Interfaces')


class CapabilityBase(InstanceModelMixin):
    """
    A capability of a :class:`Node`.

    Usually an instance of a :class:`CapabilityTemplate`.

    :ivar name: Name (unique for the node)
    :vartype name: basestring
    :ivar capability_template: Template from which this capability was instantiated (optional)
    :vartype capability_template: :class:`capabilityTemplate`
    :ivar type: Capability type
    :vartype type: :class:`Type`
    :ivar min_occurrences: Minimum number of requirement matches required
    :vartype min_occurrences: int
    :ivar max_occurrences: Maximum number of requirement matches allowed
    :vartype min_occurrences: int
    :ivar occurrences: Actual number of requirement matches
    :vartype occurrences: int
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar node: Containing node
    :vartype node: :class:`Node`
    :ivar relationship: Available when we are the target of a relationship
    :vartype relationship: :class:`Relationship`
    :ivar substitution_mapping: Our contribution to service substitution
    :vartype substitution_mapping: :class:`SubstitutionMapping`
    """

    __tablename__ = 'capability'

    __private_fields__ = ['capability_fk',
                          'node_fk',
                          'capability_template_fk']

    # region foreign_keys

    @declared_attr
    def type_fk(cls):
        """For Capability many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def node_fk(cls):
        """For Node one-to-many to Capability"""
        return relationship.foreign_key('node')

    @declared_attr
    def capability_template_fk(cls):
        """For Capability many-to-one to CapabilityTemplate"""
        return relationship.foreign_key('capability_template', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    # endregion

    # region many_to_one relationships

    @declared_attr
    def node(cls):
        return relationship.many_to_one(cls, 'node')

    @declared_attr
    def capability_template(cls):
        return relationship.many_to_one(cls, 'capability_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')

    # endregion

    min_occurrences = Column(Integer, default=None)
    max_occurrences = Column(Integer, default=None)
    occurrences = Column(Integer, default=0)

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
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties))))

    def validate(self):
        utils.validate_dict_values(self.properties)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts(context.style.node(self.name))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            console.puts('Occurrences: {0:d} ({1:d}{2})'.format(
                self.occurrences,
                self.min_occurrences or 0,
                ' to {0:d}'.format(self.max_occurrences)
                if self.max_occurrences is not None
                else ' or more'))
            utils.dump_dict_values(self.properties, 'Properties')


class InterfaceBase(InstanceModelMixin):
    """
    A typed set of :class:`Operation`.

    Usually an instance of :class:`InterfaceTemplate`.

    :ivar name: Name (unique for the node, group, or relationship)
    :vartype name: basestring
    :ivar interface_template: Template from which this interface was instantiated (optional)
    :vartype interface_template: :class:`InterfaceTemplate`
    :ivar type: Interface type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: string
    :ivar inputs: Parameters that can be used by all operations in the interface
    :vartype inputs: {basestring: :class:`Parameter`}
    :ivar operations: Operations
    :vartype operations: {basestring: :class:`Operation`}
    :ivar node: Containing node
    :vartype node: :class:`Node`
    :ivar group: Containing group
    :vartype group: :class:`Group`
    :ivar relationship: Containing relationship
    :vartype relationship: :class:`Relationship`
    """

    __tablename__ = 'interface'

    __private_fields__ = ['type_fk',
                          'node_fk',
                          'group_fk',
                          'relationship_fk',
                          'interface_template_fk']

    # region foreign_keys

    @declared_attr
    def type_fk(cls):
        """For Interface many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def node_fk(cls):
        """For Node one-to-many to Interface"""
        return relationship.foreign_key('node', nullable=True)

    @declared_attr
    def group_fk(cls):
        """For Group one-to-many to Interface"""
        return relationship.foreign_key('group', nullable=True)

    @declared_attr
    def relationship_fk(cls):
        """For Relationship one-to-many to Interface"""
        return relationship.foreign_key('relationship', nullable=True)

    @declared_attr
    def interface_template_fk(cls):
        """For Interface many-to-one to InterfaceTemplate"""
        return relationship.foreign_key('interface_template', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def operations(cls):
        return relationship.one_to_many(cls, 'operation', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def node(cls):
        return relationship.many_to_one(cls, 'node')

    @declared_attr
    def relationship(cls):
        return relationship.many_to_one(cls, 'relationship')

    @declared_attr
    def group(cls):
        return relationship.many_to_one(cls, 'group')

    @declared_attr
    def interface_template(cls):
        return relationship.many_to_one(cls, 'interface_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def inputs(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='inputs', dict_key='name')

    # endregion

    description = Column(Text)

    def configure_operations(self):
        for operation in self.operations.itervalues():
            operation.configure()

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('inputs', formatting.as_raw_dict(self.inputs)),
            ('operations', formatting.as_raw_list(self.operations))))

    def validate(self):
        utils.validate_dict_values(self.inputs)
        utils.validate_dict_values(self.operations)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.inputs, report_issues)
        utils.coerce_dict_values(self.operations, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Interface type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_dict_values(self.inputs, 'Inputs')
            utils.dump_dict_values(self.operations, 'Operations')


class OperationBase(InstanceModelMixin):
    """
    An operation in a :class:`Interface`.

    Might be an instance of :class:`OperationTemplate`.

    :ivar name: Name (unique for the interface or service)
    :vartype name: basestring
    :ivar operation_template: Template from which this operation was instantiated (optional)
    :vartype operation_template: :class:`OperationTemplate`
    :ivar description: Human-readable description
    :vartype description: string
    :ivar relationship_edge: When true specified that the operation is on the relationship's
                             target edge instead of its source (only used by relationship
                             operations)
    :vartype relationship_edge: bool
    :ivar implementation: Implementation (interpreted by the plugin)
    :vartype implementation: basestring
    :ivar dependencies: Dependency strings (interpreted by the plugin)
    :vartype dependencies: [basestring]
    :ivar inputs: Parameters that can be used by this operation
    :vartype inputs: {basestring: :class:`Parameter`}
    :ivar plugin: Associated plugin
    :vartype plugin: :class:`Plugin`
    :ivar configuration: Configuration (interpreted by the plugin)
    :vartype configuration: {basestring, :class:`Parameter`}
    :ivar function: Name of the operation function
    :vartype function: basestring
    :ivar arguments: Arguments to send to the operation function
    :vartype arguments: {basestring: :class:`Parameter`}
    :ivar executor: Name of executor to run the operation with
    :vartype executor: basestring
    :ivar max_attempts: Maximum number of attempts allowed in case of failure
    :vartype max_attempts: int
    :ivar retry_interval: Interval between retries (in seconds)
    :vartype retry_interval: int
    :ivar interface: Containing interface
    :vartype interface: :class:`Interface`
    :ivar service: Containing service
    :vartype service: :class:`Service`
    """

    __tablename__ = 'operation'

    __private_fields__ = ['service_fk',
                          'interface_fk',
                          'plugin_fk',
                          'operation_template_fk']

    # region foreign_keys

    @declared_attr
    def service_fk(cls):
        """For Service one-to-many to Operation"""
        return relationship.foreign_key('service', nullable=True)

    @declared_attr
    def interface_fk(cls):
        """For Interface one-to-many to Operation"""
        return relationship.foreign_key('interface', nullable=True)

    @declared_attr
    def plugin_fk(cls):
        """For Operation one-to-one to Plugin"""
        return relationship.foreign_key('plugin', nullable=True)

    @declared_attr
    def operation_template_fk(cls):
        """For Operation many-to-one to OperationTemplate"""
        return relationship.foreign_key('operation_template', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    @declared_attr
    def plugin(cls):
        return relationship.one_to_one(cls, 'plugin', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region one_to_many relationships

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service(cls):
        return relationship.many_to_one(cls, 'service', back_populates='workflows')

    @declared_attr
    def interface(cls):
        return relationship.many_to_one(cls, 'interface')

    @declared_attr
    def operation_template(cls):
        return relationship.many_to_one(cls, 'operation_template')

    # endregion

    # region many_to_many relationships

    @declared_attr
    def inputs(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='inputs', dict_key='name')

    @declared_attr
    def configuration(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='configuration', dict_key='name')

    @declared_attr
    def arguments(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='arguments', dict_key='name')

    # endregion

    description = Column(Text)
    relationship_edge = Column(Boolean)
    implementation = Column(Text)
    dependencies = Column(modeling_types.StrictList(item_cls=basestring))
    function = Column(Text)
    executor = Column(Text)
    max_attempts = Column(Integer)
    retry_interval = Column(Integer)

    def configure(self):
        if (self.implementation is None) and (self.function is None):
            return

        if (self.interface is not None) and (self.plugin is None) and (self.function is None):
            # ("interface" is None for workflow operations, which do not currently use "plugin")
            # The default (None) plugin is the execution plugin
            execution_plugin.instantiation.configure_operation(self)
        else:
            # In the future plugins may be able to add their own "configure_operation" hook that
            # can validate the configuration and otherwise create specially derived arguments. For
            # now, we just send all configuration parameters as arguments without validation.
            utils.instantiate_dict(self, self.arguments, self.configuration)

        # Send all inputs as extra arguments
        # Note that they will override existing arguments of the same names
        utils.instantiate_dict(self, self.arguments, self.inputs)

        # Check for reserved arguments
        from ..orchestrator.decorators import OPERATION_DECORATOR_RESERVED_ARGUMENTS
        used_reserved_names = \
            OPERATION_DECORATOR_RESERVED_ARGUMENTS.intersection(self.arguments.keys())
        if used_reserved_names:
            context = ConsumptionContext.get_thread_local()
            context.validation.report('using reserved arguments in node "{0}": {1}'
                                      .format(
                                          self.name,
                                          formatting.string_list_as_string(used_reserved_names)),
                                      level=validation.Issue.EXTERNAL)


    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('implementation', self.implementation),
            ('dependencies', self.dependencies),
            ('inputs', formatting.as_raw_dict(self.inputs))))

    def validate(self):
        # TODO must be associated with either interface or service
        utils.validate_dict_values(self.inputs)
        utils.validate_dict_values(self.configuration)
        utils.validate_dict_values(self.arguments)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.inputs, report_issues)
        utils.coerce_dict_values(self.configuration, report_issues)
        utils.coerce_dict_values(self.arguments, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
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
            utils.dump_dict_values(self.inputs, 'Inputs')
            if self.executor is not None:
                console.puts('Executor: {0}'.format(context.style.literal(self.executor)))
            if self.max_attempts is not None:
                console.puts('Max attempts: {0}'.format(context.style.literal(self.max_attempts)))
            if self.retry_interval is not None:
                console.puts('Retry interval: {0}'.format(
                    context.style.literal(self.retry_interval)))
            if self.plugin is not None:
                console.puts('Plugin: {0}'.format(
                    context.style.literal(self.plugin.name)))
            utils.dump_dict_values(self.configuration, 'Configuration')
            if self.function is not None:
                console.puts('Function: {0}'.format(context.style.literal(self.function)))
            utils.dump_dict_values(self.arguments, 'Arguments')


class ArtifactBase(InstanceModelMixin):
    """
    A file associated with a :class:`Node`.

    Usually an instance of :class:`ArtifactTemplate`.

    :ivar name: Name (unique for the node)
    :vartype name: basestring
    :ivar artifact_template: Template from which this artifact was instantiated (optional)
    :vartype artifact_template: :class:`ArtifactTemplate`
    :ivar type: Artifact type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: string
    :ivar source_path: Source path (CSAR or repository)
    :vartype source_path: basestring
    :ivar target_path: Path at destination machine
    :vartype target_path: basestring
    :ivar repository_url: Repository URL
    :vartype repository_path: basestring
    :ivar repository_credential: Credentials for accessing the repository
    :vartype repository_credential: {basestring: basestring}
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar node: Containing node
    :vartype node: :class:`Node`
    """

    __tablename__ = 'artifact'

    __private_fields__ = ['type_fk',
                          'node_fk',
                          'artifact_template_fk']

    # region foreign_keys

    @declared_attr
    def type_fk(cls):
        """For Artifact many-to-one to Type"""
        return relationship.foreign_key('type')

    @declared_attr
    def node_fk(cls):
        """For Node one-to-many to Artifact"""
        return relationship.foreign_key('node')

    @declared_attr
    def artifact_template_fk(cls):
        """For Artifact many-to-one to ArtifactTemplate"""
        return relationship.foreign_key('artifact_template', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    # endregion

    # region many_to_one relationships
    @declared_attr
    def node(cls):
        return relationship.many_to_one(cls, 'node')

    @declared_attr
    def artifact_template(cls):
        return relationship.many_to_one(cls, 'artifact_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)
    # endregion

    # region many_to_many relationships
    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')
    # endregion

    description = Column(Text)
    source_path = Column(Text)
    target_path = Column(Text)
    repository_url = Column(Text)
    repository_credential = Column(modeling_types.StrictDict(basestring, basestring))

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

    def validate(self):
        utils.validate_dict_values(self.properties)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
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
            utils.dump_dict_values(self.properties, 'Properties')
