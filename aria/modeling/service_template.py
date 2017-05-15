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

from __future__ import absolute_import  # so we can import standard 'types'

from datetime import datetime

from sqlalchemy import (
    Column,
    Text,
    Integer,
    Boolean,
    DateTime,
    PickleType
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.associationproxy import association_proxy

from ..parser import validation
from ..parser.consumption import ConsumptionContext
from ..parser.reading import deepcopy_with_locators
from ..utils import (collections, formatting, console)
from ..utils.versions import VersionString
from .mixins import TemplateModelMixin
from . import (
    relationship,
    utils,
    types as modeling_types
)


class ServiceTemplateBase(TemplateModelMixin):
    """
    A service template is a source for creating :class:`Service` instances.

    It is usually created by various DSL parsers, such as ARIA's TOSCA extension. However, it can
    also be created programmatically.

    :ivar name: Name (unique for this ARIA installation)
    :vartype name: basestring
    :ivar description: Human-readable description
    :vartype description: basestring
    :ivar main_file_name: Filename of CSAR or YAML file from which this service template was parsed
    :vartype main_file_name: basestring
    :ivar meta_data: Custom annotations
    :vartype meta_data: {basestring: :class:`Metadata`}
    :ivar node_templates: Templates for creating nodes
    :vartype node_templates: {basestring: :class:`NodeTemplate`}
    :ivar group_templates: Templates for creating groups
    :vartype group_templates: {basestring: :class:`GroupTemplate`}
    :ivar policy_templates: Templates for creating policies
    :vartype policy_templates: {basestring: :class:`PolicyTemplate`}
    :ivar substitution_template: The entire service can appear as a node
    :vartype substitution_template: :class:`SubstitutionTemplate`
    :ivar inputs: Externally provided parameters
    :vartype inputs: {basestring: :class:`Parameter`}
    :ivar outputs: These parameters are filled in after service installation
    :vartype outputs: {basestring: :class:`Parameter`}
    :ivar workflow_templates: Custom workflows that can be performed on the service
    :vartype workflow_templates: {basestring: :class:`OperationTemplate`}
    :ivar plugin_specifications: Plugins used by the service
    :vartype plugin_specifications: {basestring: :class:`PluginSpecification`}
    :ivar node_types: Base for the node type hierarchy
    :vartype node_types: :class:`Type`
    :ivar group_types: Base for the group type hierarchy
    :vartype group_types: :class:`Type`
    :ivar policy_types: Base for the policy type hierarchy
    :vartype policy_types: :class:`Type`
    :ivar relationship_types: Base for the relationship type hierarchy
    :vartype relationship_types: :class:`Type`
    :ivar capability_types: Base for the capability type hierarchy
    :vartype capability_types: :class:`Type`
    :ivar interface_types: Base for the interface type hierarchy
    :vartype interface_types: :class:`Type`
    :ivar artifact_types: Base for the artifact type hierarchy
    :vartype artifact_types: :class:`Type`
    :ivar created_at: Creation timestamp
    :vartype created_at: :class:`datetime.datetime`
    :ivar updated_at: Update timestamp
    :vartype updated_at: :class:`datetime.datetime`
    :ivar services: Instantiated services
    :vartype services: [:class:`Service`]
    """

    __tablename__ = 'service_template'

    __private_fields__ = ['substitution_template_fk',
                          'node_type_fk',
                          'group_type_fk',
                          'policy_type_fk',
                          'relationship_type_fk',
                          'capability_type_fk',
                          'interface_type_fk',
                          'artifact_type_fk']

    description = Column(Text)
    main_file_name = Column(Text)
    created_at = Column(DateTime, nullable=False, index=True)
    updated_at = Column(DateTime)

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

    # region association proxies

    # endregion

    # region one_to_one relationships

    @declared_attr
    def substitution_template(cls):
        return relationship.one_to_one(
            cls, 'substitution_template', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def node_types(cls):
        return relationship.one_to_one(
            cls, 'type', fk='node_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def group_types(cls):
        return relationship.one_to_one(
            cls, 'type', fk='group_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def policy_types(cls):
        return relationship.one_to_one(
            cls, 'type', fk='policy_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def relationship_types(cls):
        return relationship.one_to_one(
            cls, 'type', fk='relationship_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def capability_types(cls):
        return relationship.one_to_one(
            cls, 'type', fk='capability_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def interface_types(cls):
        return relationship.one_to_one(
            cls, 'type', fk='interface_type_fk', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def artifact_types(cls):
        return relationship.one_to_one(
            cls, 'type', fk='artifact_type_fk', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region one_to_many relationships

    @declared_attr
    def services(cls):
        return relationship.one_to_many(cls, 'service', dict_key='name')

    @declared_attr
    def operation_templates(cls):
        return relationship.one_to_many(cls, 'operation_template')

    @declared_attr
    def node_templates(cls):
        return relationship.one_to_many(cls, 'node_template', dict_key='name')

    @declared_attr
    def group_templates(cls):
        return relationship.one_to_many(cls, 'group_template', dict_key='name')

    @declared_attr
    def policy_templates(cls):
        return relationship.one_to_many(cls, 'policy_template', dict_key='name')

    @declared_attr
    def workflow_templates(cls):
        return relationship.one_to_many(cls, 'operation_template', dict_key='name')

    @declared_attr
    def plugin_specifications(cls):
        return relationship.one_to_many(cls, 'plugin_specification', dict_key='name')

    # endregion

    # region many_to_one relationships

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

    # endregion

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

    def instantiate(self, container, model_storage, inputs=None):  # pylint: disable=arguments-differ
        from . import models
        context = ConsumptionContext.get_thread_local()
        now = datetime.now()
        service = models.Service(created_at=now,
                                 updated_at=now,
                                 description=deepcopy_with_locators(self.description),
                                 service_template=self)
        context.modeling.instance = service

        service.inputs = utils.create_inputs(inputs or {}, self.inputs)
        # TODO: now that we have inputs, we should scan properties and inputs and evaluate functions

        for plugin_specification in self.plugin_specifications.itervalues():
            if plugin_specification.enabled:
                if plugin_specification.resolve(model_storage):
                    plugin = plugin_specification.plugin
                    service.plugins[plugin.name] = plugin
                else:
                    context = ConsumptionContext.get_thread_local()
                    context.validation.report('specified plugin not found: {0}'.format(
                        plugin_specification.name), level=validation.Issue.EXTERNAL)

        utils.instantiate_dict(self, service.meta_data, self.meta_data)

        for node_template in self.node_templates.itervalues():
            for _ in range(node_template.default_instances):
                node = node_template.instantiate(container)
                service.nodes[node.name] = node

        utils.instantiate_dict(self, service.groups, self.group_templates)
        utils.instantiate_dict(self, service.policies, self.policy_templates)
        utils.instantiate_dict(self, service.workflows, self.workflow_templates)

        if self.substitution_template is not None:
            service.substitution = self.substitution_template.instantiate(container)

        utils.instantiate_dict(self, service.outputs, self.outputs)

        return service

    def validate(self):
        utils.validate_dict_values(self.meta_data)
        utils.validate_dict_values(self.node_templates)
        utils.validate_dict_values(self.group_templates)
        utils.validate_dict_values(self.policy_templates)
        if self.substitution_template is not None:
            self.substitution_template.validate()
        utils.validate_dict_values(self.inputs)
        utils.validate_dict_values(self.outputs)
        utils.validate_dict_values(self.workflow_templates)
        if self.node_types is not None:
            self.node_types.validate()
        if self.group_types is not None:
            self.group_types.validate()
        if self.policy_types is not None:
            self.policy_types.validate()
        if self.relationship_types is not None:
            self.relationship_types.validate()
        if self.capability_types is not None:
            self.capability_types.validate()
        if self.interface_types is not None:
            self.interface_types.validate()
        if self.artifact_types is not None:
            self.artifact_types.validate()

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.meta_data, report_issues)
        utils.coerce_dict_values(self.node_templates, report_issues)
        utils.coerce_dict_values(self.group_templates, report_issues)
        utils.coerce_dict_values(self.policy_templates, report_issues)
        if self.substitution_template is not None:
            self.substitution_template.coerce_values(report_issues)
        utils.coerce_dict_values(self.inputs, report_issues)
        utils.coerce_dict_values(self.outputs, report_issues)
        utils.coerce_dict_values(self.workflow_templates, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        if self.description is not None:
            console.puts(context.style.meta(self.description))
        utils.dump_dict_values(self.meta_data, 'Metadata')
        for node_template in self.node_templates.itervalues():
            node_template.dump()
        for group_template in self.group_templates.itervalues():
            group_template.dump()
        for policy_template in self.policy_templates.itervalues():
            policy_template.dump()
        if self.substitution_template is not None:
            self.substitution_template.dump()
        utils.dump_dict_values(self.inputs, 'Inputs')
        utils.dump_dict_values(self.outputs, 'Outputs')
        utils.dump_dict_values(self.workflow_templates, 'Workflow templates')

    def dump_types(self):
        if self.node_types.children:
            console.puts('Node types:')
            self.node_types.dump()
        if self.group_types.children:
            console.puts('Group types:')
            self.group_types.dump()
        if self.capability_types.children:
            console.puts('Capability types:')
            self.capability_types.dump()
        if self.relationship_types.children:
            console.puts('Relationship types:')
            self.relationship_types.dump()
        if self.policy_types.children:
            console.puts('Policy types:')
            self.policy_types.dump()
        if self.artifact_types.children:
            console.puts('Artifact types:')
            self.artifact_types.dump()
        if self.interface_types.children:
            console.puts('Interface types:')
            self.interface_types.dump()


class NodeTemplateBase(TemplateModelMixin):
    """
    A template for creating zero or more :class:`Node` instances.

    :ivar name: Name (unique for this service template; will usually be used as a prefix for node
                names)
    :vartype name: basestring
    :ivar type: Node type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: basestring
    :ivar default_instances: Default number nodes that will appear in the service
    :vartype default_instances: int
    :ivar min_instances: Minimum number nodes that will appear in the service
    :vartype min_instances: int
    :ivar max_instances: Maximum number nodes that will appear in the service
    :vartype max_instances: int
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar interface_templates: Bundles of operations
    :vartype interface_templates: {basestring: :class:`InterfaceTemplate`}
    :ivar artifact_templates: Associated files
    :vartype artifact_templates: {basestring: :class:`ArtifactTemplate`}
    :ivar capability_templates: Exposed capabilities
    :vartype capability_templates: {basestring: :class:`CapabilityTemplate`}
    :ivar requirement_templates: Potential relationships with other nodes
    :vartype requirement_templates: [:class:`RequirementTemplate`]
    :ivar target_node_template_constraints: Constraints for filtering relationship targets
    :vartype target_node_template_constraints: [:class:`NodeTemplateConstraint`]
    :ivar service_template: Containing service template
    :vartype service_template: :class:`ServiceTemplate`
    :ivar group_templates: We are a member of these groups
    :vartype group_templates: [:class:`GroupTemplate`]
    :ivar policy_templates: Policy templates enacted on this node
    :vartype policy_templates: [:class:`PolicyTemplate`]
    :ivar substitution_template_mapping: Our contribution to service substitution
    :vartype substitution_template_mapping: :class:`SubstitutionTemplateMapping`
    :ivar nodes: Instantiated nodes
    :vartype nodes: [:class:`Node`]
    """

    __tablename__ = 'node_template'

    __private_fields__ = ['type_fk',
                          'service_template_fk']

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

    # region association proxies

    @declared_attr
    def service_template_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('service_template', 'name')

    @declared_attr
    def type_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('type', 'name')

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def nodes(cls):
        return relationship.one_to_many(cls, 'node')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def service_template(cls):
        return relationship.many_to_one(cls, 'service_template')

    # endregion

    # region many_to_many relationships

    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')

    @declared_attr
    def attributes(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='attributes', dict_key='name')

    @declared_attr
    def interface_templates(cls):
        return relationship.one_to_many(cls, 'interface_template', dict_key='name')

    @declared_attr
    def artifact_templates(cls):
        return relationship.one_to_many(cls, 'artifact_template', dict_key='name')

    @declared_attr
    def capability_templates(cls):
        return relationship.one_to_many(cls, 'capability_template', dict_key='name')

    @declared_attr
    def requirement_templates(cls):
        return relationship.one_to_many(cls, 'requirement_template', child_fk='node_template_fk')

    # endregion

    description = Column(Text)
    default_instances = Column(Integer, default=1)
    min_instances = Column(Integer, default=0)
    max_instances = Column(Integer, default=None)
    target_node_template_constraints = Column(PickleType)

    def is_target_node_template_valid(self, target_node_template):
        if self.target_node_template_constraints:
            for node_template_constraint in self.target_node_template_constraints:
                if not node_template_constraint.matches(self, target_node_template):
                    return False
        return True

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('default_instances', self.default_instances),
            ('min_instances', self.min_instances),
            ('max_instances', self.max_instances),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('attributes', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates)),
            ('artifact_templates', formatting.as_raw_list(self.artifact_templates)),
            ('capability_templates', formatting.as_raw_list(self.capability_templates)),
            ('requirement_templates', formatting.as_raw_list(self.requirement_templates))))

    def instantiate(self, container):
        from . import models
        if self.nodes:
            highest_name_suffix = max(int(n.name.rsplit('_', 1)[-1]) for n in self.nodes)
            suffix = highest_name_suffix + 1
        else:
            suffix = 1
        name = '{name}_{index}'.format(name=self.name, index=suffix)
        node = models.Node(name=name,
                           type=self.type,
                           description=deepcopy_with_locators(self.description),
                           state=models.Node.INITIAL,
                           runtime_properties={},
                           node_template=self)
        utils.instantiate_dict(node, node.properties, self.properties)
        utils.instantiate_dict(node, node.attributes, self.attributes)
        utils.instantiate_dict(node, node.interfaces, self.interface_templates)
        utils.instantiate_dict(node, node.artifacts, self.artifact_templates)
        utils.instantiate_dict(node, node.capabilities, self.capability_templates)

        # Default attributes
        if 'tosca_name' in node.attributes:
            node.attributes['tosca_name'].value = self.name
        if 'tosca_id' in node.attributes:
            node.attributes['tosca_id'].value = name

        return node

    def validate(self):
        utils.validate_dict_values(self.properties)
        utils.validate_dict_values(self.attributes)
        utils.validate_dict_values(self.interface_templates)
        utils.validate_dict_values(self.artifact_templates)
        utils.validate_dict_values(self.capability_templates)
        utils.validate_list_values(self.requirement_templates)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)
        utils.coerce_dict_values(self.attributes, report_issues)
        utils.coerce_dict_values(self.interface_templates, report_issues)
        utils.coerce_dict_values(self.artifact_templates, report_issues)
        utils.coerce_dict_values(self.capability_templates, report_issues)
        utils.coerce_list_values(self.requirement_templates, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('Node template: {0}'.format(context.style.node(self.name)))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            console.puts('Instances: {0:d} ({1:d}{2})'.format(
                self.default_instances,
                self.min_instances,
                ' to {0:d}'.format(self.max_instances)
                if self.max_instances is not None
                else ' or more'))
            utils.dump_dict_values(self.properties, 'Properties')
            utils.dump_dict_values(self.attributes, 'Attributes')
            utils.dump_interfaces(self.interface_templates)
            utils.dump_dict_values(self.artifact_templates, 'Artifact templates')
            utils.dump_dict_values(self.capability_templates, 'Capability templates')
            utils.dump_list_values(self.requirement_templates, 'Requirement templates')


class GroupTemplateBase(TemplateModelMixin):
    """
    A template for creating a :class:`Group` instance.

    Groups are logical containers for zero or more nodes.

    :ivar name: Name (unique for this service template)
    :vartype name: basestring
    :ivar type: Group type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: basestring
    :ivar node_templates: All nodes instantiated by these templates will be members of the group
    :vartype node_templates: [:class:`NodeTemplate`]
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar interface_templates: Bundles of operations
    :vartype interface_templates: {basestring: :class:`InterfaceTemplate`}
    :ivar service_template: Containing service template
    :vartype service_template: :class:`ServiceTemplate`
    :ivar policy_templates: Policy templates enacted on this group
    :vartype policy_templates: [:class:`PolicyTemplate`]
    :ivar groups: Instantiated groups
    :vartype groups: [:class:`Group`]
    """

    __tablename__ = 'group_template'

    __private_fields__ = ['type_fk',
                          'service_template_fk']

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

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def groups(cls):
        return relationship.one_to_many(cls, 'group')

    @declared_attr
    def interface_templates(cls):
        return relationship.one_to_many(cls, 'interface_template', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def node_templates(cls):
        return relationship.many_to_many(cls, 'node_template')

    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')

    # endregion

    description = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates))))

    def instantiate(self, container):
        from . import models
        group = models.Group(name=self.name,
                             type=self.type,
                             description=deepcopy_with_locators(self.description),
                             group_template=self)
        utils.instantiate_dict(self, group.properties, self.properties)
        utils.instantiate_dict(self, group.interfaces, self.interface_templates)
        if self.node_templates:
            for node_template in self.node_templates:
                group.nodes += node_template.nodes
        return group

    def validate(self):
        utils.validate_dict_values(self.properties)
        utils.validate_dict_values(self.interface_templates)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)
        utils.coerce_dict_values(self.interface_templates, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('Group template: {0}'.format(context.style.node(self.name)))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_dict_values(self.properties, 'Properties')
            utils.dump_interfaces(self.interface_templates)
            if self.node_templates:
                console.puts('Member node templates: {0}'.format(', '.join(
                    (str(context.style.node(v.name)) for v in self.node_templates))))


class PolicyTemplateBase(TemplateModelMixin):
    """
    Policies can be applied to zero or more :class:`NodeTemplate` or :class:`GroupTemplate`
    instances.

    :ivar name: Name (unique for this service template)
    :vartype name: basestring
    :ivar type: Policy type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: basestring
    :ivar node_templates: Policy will be enacted on all nodes instantiated by these templates
    :vartype node_templates: [:class:`NodeTemplate`]
    :ivar group_templates: Policy will be enacted on all nodes in these groups
    :vartype group_templates: [:class:`GroupTemplate`]
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar service_template: Containing service template
    :vartype service_template: :class:`ServiceTemplate`
    :ivar policies: Instantiated policies
    :vartype policies: [:class:`Policy`]
    """

    __tablename__ = 'policy_template'

    __private_fields__ = ['type_fk', 'service_template_fk']

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

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def policies(cls):
        return relationship.one_to_many(cls, 'policy')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def node_templates(cls):
        return relationship.many_to_many(cls, 'node_template')

    @declared_attr
    def group_templates(cls):
        return relationship.many_to_many(cls, 'group_template')

    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')

    # endregion

    description = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties))))

    def instantiate(self, container):
        from . import models
        policy = models.Policy(name=self.name,
                               type=self.type,
                               description=deepcopy_with_locators(self.description),
                               policy_template=self)
        utils.instantiate_dict(self, policy.properties, self.properties)
        if self.node_templates:
            for node_template in self.node_templates:
                policy.nodes += node_template.nodes
        if self.group_templates:
            for group_template in self.group_templates:
                policy.groups += group_template.groups
        return policy

    def validate(self):
        utils.validate_dict_values(self.properties)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('Policy template: {0}'.format(context.style.node(self.name)))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_dict_values(self.properties, 'Properties')
            if self.node_templates:
                console.puts('Target node templates: {0}'.format(', '.join(
                    (str(context.style.node(v.name)) for v in self.node_templates))))
            if self.group_templates:
                console.puts('Target group templates: {0}'.format(', '.join(
                    (str(context.style.node(v.name)) for v in self.group_templates))))


class SubstitutionTemplateBase(TemplateModelMixin):
    """
    Used to substitute a single node for the entire deployment.

    :ivar node_type: Exposed node type
    :vartype node_type: :class:`Type`
    :ivar mappings: Requirement and capability mappings
    :vartype mappings: {basestring: :class:`SubstitutionTemplateMapping`}
    :ivar service_template: Containing service template
    :vartype service_template: :class:`ServiceTemplate`
    :ivar substitutions: Instantiated substitutions
    :vartype substitutions: [:class:`Substitution`]
    """

    __tablename__ = 'substitution_template'

    __private_fields__ = ['node_type_fk']

    # region foreign keys

    @declared_attr
    def node_type_fk(cls):
        """For SubstitutionTemplate many-to-one to Type"""
        return relationship.foreign_key('type')

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def substitutions(cls):
        return relationship.one_to_many(cls, 'substitution')

    @declared_attr
    def mappings(cls):
        return relationship.one_to_many(cls, 'substitution_template_mapping', dict_key='name')

    # endregion

    # region many_to_one relationships

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

    def instantiate(self, container):
        from . import models
        substitution = models.Substitution(node_type=self.node_type,
                                           substitution_template=self)
        utils.instantiate_dict(container, substitution.mappings, self.mappings)
        return substitution

    def validate(self):
        utils.validate_dict_values(self.mappings)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.mappings, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('Substitution template:')
        with context.style.indent:
            console.puts('Node type: {0}'.format(context.style.type(self.node_type.name)))
            utils.dump_dict_values(self.mappings, 'Mappings')


class SubstitutionTemplateMappingBase(TemplateModelMixin):
    """
    Used by :class:`SubstitutionTemplate` to map a capability or a requirement to a node.

    Only one of `capability_template` and `requirement_template` can be set.

    :ivar name: Exposed capability or requirement name
    :vartype name: basestring
    :ivar node_template: Node template
    :vartype node_template: :class:`NodeTemplate`
    :ivar capability_template: Capability template in the node template
    :vartype capability_template: :class:`CapabilityTemplate`
    :ivar requirement_template: Requirement template in the node template
    :vartype requirement_template: :class:`RequirementTemplate`
    :ivar substitution_template: Containing substitution template
    :vartype substitution_template: :class:`SubstitutionTemplate`
    """

    __tablename__ = 'substitution_template_mapping'

    __private_fields__ = ['substitution_template_fk',
                          'node_template_fk',
                          'capability_template_fk',
                          'requirement_template_fk']

    # region foreign keys

    @declared_attr
    def substitution_template_fk(cls):
        """For SubstitutionTemplate one-to-many to SubstitutionTemplateMapping"""
        return relationship.foreign_key('substitution_template')

    @declared_attr
    def node_template_fk(cls):
        """For SubstitutionTemplate one-to-one to NodeTemplate"""
        return relationship.foreign_key('node_template')

    @declared_attr
    def capability_template_fk(cls):
        """For SubstitutionTemplate one-to-one to CapabilityTemplate"""
        return relationship.foreign_key('capability_template', nullable=True)

    @declared_attr
    def requirement_template_fk(cls):
        """For SubstitutionTemplate one-to-one to RequirementTemplate"""
        return relationship.foreign_key('requirement_template', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    @declared_attr
    def node_template(cls):
        return relationship.one_to_one(
            cls, 'node_template', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def capability_template(cls):
        return relationship.one_to_one(
            cls, 'capability_template', back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def requirement_template(cls):
        return relationship.one_to_one(
            cls, 'requirement_template', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region one_to_many relationships

    # endregion

    # region many_to_one relationships

    @declared_attr
    def substitution_template(cls):
        return relationship.many_to_one(cls, 'substitution_template', back_populates='mappings')

    # endregion

    # region many_to_many relationships

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),))

    def coerce_values(self, report_issues):
        pass

    def instantiate(self, container):
        from . import models
        context = ConsumptionContext.get_thread_local()
        nodes = self.node_template.nodes
        if len(nodes) == 0:
            context.validation.report(
                'mapping "{0}" refers to node template "{1}" but there are no '
                'node instances'.format(self.mapped_name, self.node_template.name),
                level=validation.Issue.BETWEEN_INSTANCES)
            return None
        # The TOSCA spec does not provide a way to choose the node,
        # so we will just pick the first one
        node = nodes[0]
        capability = None
        if self.capability_template:
            for a_capability in node.capabilities.itervalues():
                if a_capability.capability_template.name == self.capability_template.name:
                    capability = a_capability
        return models.SubstitutionMapping(name=self.name,
                                          node=node,
                                          capability=capability,
                                          requirement_template=self.requirement_template)

    def validate(self):
        context = ConsumptionContext.get_thread_local()
        if (self.capability_template is None) and (self.requirement_template is None):
            context.validation.report('mapping "{0}" refers to neither capability nor a requirement'
                                      ' in node template: {1}'.format(
                                          self.name,
                                          formatting.safe_repr(self.node_template.name)),
                                      level=validation.Issue.BETWEEN_TYPES)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('{0} -> {1}.{2}'.format(
            context.style.node(self.name),
            context.style.node(self.node_template.name),
            context.style.node(self.capability_template.name
                               if self.capability_template
                               else self.requirement_template.name)))


class RequirementTemplateBase(TemplateModelMixin):
    """
    A requirement for a :class:`NodeTemplate`. During instantiation will be matched with a
    capability of another node.

    Requirements may optionally contain a :class:`RelationshipTemplate` that will be created between
    the nodes.

    :ivar name: Name (a node template can have multiple requirements with the same name)
    :vartype name: basestring
    :ivar target_node_type: Required node type (optional)
    :vartype target_node_type: :class:`Type`
    :ivar target_node_template: Required node template (optional)
    :vartype target_node_template: :class:`NodeTemplate`
    :ivar target_capability_type: Required capability type (optional)
    :vartype target_capability_type: :class:`Type`
    :ivar target_capability_name: Name of capability in target node (optional)
    :vartype target_capability_name: basestring
    :ivar target_node_template_constraints: Constraints for filtering relationship targets
    :vartype target_node_template_constraints: [:class:`NodeTemplateConstraint`]
    :ivar relationship_template: Template for relationships (optional)
    :vartype relationship_template: :class:`RelationshipTemplate`
    :ivar node_template: Containing node template
    :vartype node_template: :class:`NodeTemplate`
    :ivar substitution_template_mapping: Our contribution to service substitution
    :vartype substitution_template_mapping: :class:`SubstitutionTemplateMapping`
    :ivar substitution_mapping: Our contribution to service substitution
    :vartype substitution_mapping: :class:`SubstitutionMapping`
    """

    __tablename__ = 'requirement_template'

    __private_fields__ = ['target_node_type_fk',
                          'target_node_template_fk',
                          'target_capability_type_fk'
                          'node_template_fk',
                          'relationship_template_fk']

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
        """For RequirementTemplate one-to-one to NodeTemplate"""
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

    # region association proxies

    # endregion

    # region one_to_one relationships

    @declared_attr
    def target_node_template(cls):
        return relationship.one_to_one(cls,
                                       'node_template',
                                       fk='target_node_template_fk',
                                       back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def target_capability_type(cls):
        return relationship.one_to_one(cls,
                                       'type',
                                       fk='target_capability_type_fk',
                                       back_populates=relationship.NO_BACK_POP)

    @declared_attr
    def relationship_template(cls):
        return relationship.one_to_one(cls, 'relationship_template')

    # endregion

    # region one_to_many relationships

    @declared_attr
    def relationships(cls):
        return relationship.one_to_many(cls, 'relationship')

    @declared_attr
    def target_node_type(cls):
        return relationship.many_to_one(
            cls, 'type', fk='target_node_type_fk', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        return relationship.many_to_one(cls, 'node_template', fk='node_template_fk')

    # endregion

    # region many_to_many relationships

    # endregion

    target_capability_name = Column(Text)
    target_node_template_constraints = Column(PickleType)

    def find_target(self, source_node_template):
        context = ConsumptionContext.get_thread_local()

        # We might already have a specific node template, so we'll just verify it
        if self.target_node_template is not None:
            if not source_node_template.is_target_node_template_valid(self.target_node_template):
                context.validation.report('requirement "{0}" of node template "{1}" is for node '
                                          'template "{2}" but it does not match constraints'.format(
                                              self.name,
                                              self.target_node_template.name,
                                              source_node_template.name),
                                          level=validation.Issue.BETWEEN_TYPES)
            if (self.target_capability_type is not None) \
                or (self.target_capability_name is not None):
                target_node_capability = self.find_target_capability(source_node_template,
                                                                     self.target_node_template)
                if target_node_capability is None:
                    return None, None
            else:
                target_node_capability = None

            return self.target_node_template, target_node_capability

        # Find first node that matches the type
        elif self.target_node_type is not None:
            for target_node_template in \
                    self.node_template.service_template.node_templates.values():
                if self.target_node_type.get_descendant(target_node_template.type.name) is None:
                    continue

                if not source_node_template.is_target_node_template_valid(target_node_template):
                    continue

                target_node_capability = self.find_target_capability(source_node_template,
                                                                     target_node_template)
                if target_node_capability is None:
                    continue

                return target_node_template, target_node_capability

        return None, None

    def find_target_capability(self, source_node_template, target_node_template):
        for capability_template in target_node_template.capability_templates.itervalues():
            if capability_template.satisfies_requirement(source_node_template,
                                                         self,
                                                         target_node_template):
                return capability_template
        return None

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

    def validate(self):
        if self.relationship_template:
            self.relationship_template.validate()

    def coerce_values(self, report_issues):
        if self.relationship_template is not None:
            self.relationship_template.coerce_values(report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        if self.name:
            console.puts(context.style.node(self.name))
        else:
            console.puts('Requirement:')
        with context.style.indent:
            if self.target_node_type is not None:
                console.puts('Target node type: {0}'.format(
                    context.style.type(self.target_node_type.name)))
            elif self.target_node_template is not None:
                console.puts('Target node template: {0}'.format(
                    context.style.node(self.target_node_template.name)))
            if self.target_capability_type is not None:
                console.puts('Target capability type: {0}'.format(
                    context.style.type(self.target_capability_type.name)))
            elif self.target_capability_name is not None:
                console.puts('Target capability name: {0}'.format(
                    context.style.node(self.target_capability_name)))
            if self.target_node_template_constraints:
                console.puts('Target node template constraints:')
                with context.style.indent:
                    for constraint in self.target_node_template_constraints:
                        console.puts(context.style.literal(constraint))
            if self.relationship_template:
                console.puts('Relationship:')
                with context.style.indent:
                    self.relationship_template.dump()


class RelationshipTemplateBase(TemplateModelMixin):
    """
    Optional addition to a :class:`RequirementTemplate` in :class:`NodeTemplate` that can be applied
    when the requirement is matched with a capability.

    Note that a relationship template here is not equivalent to a relationship template entity in
    TOSCA. For example, a TOSCA requirement specifying a relationship type instead of a template
    would still be represented here as a relationship template.

    :ivar name: Name (optional; if present is unique for this service template)
    :vartype name: basestring
    :ivar type: Relationship type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: basestring
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar interface_templates: Bundles of operations
    :vartype interface_templates: {basestring: :class:`InterfaceTemplate`}
    :ivar requirement_template: Containing requirement template
    :vartype requirement_template: :class:`RequirementTemplate`
    :ivar relationships: Instantiated relationships
    :vartype relationships: [:class:`Relationship`]
    """

    __tablename__ = 'relationship_template'

    __private_fields__ = ['type_fk']

    # region foreign keys

    @declared_attr
    def type_fk(cls):
        """For RelationshipTemplate many-to-one to Type"""
        return relationship.foreign_key('type', nullable=True)

    # endregion

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def relationships(cls):
        return relationship.one_to_many(cls, 'relationship')

    @declared_attr
    def interface_templates(cls):
        return relationship.one_to_many(cls, 'interface_template', dict_key='name')

    # endregion

    # region many_to_one relationships

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

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('type_name', self.type.name if self.type is not None else None),
            ('name', self.name),
            ('description', self.description),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates))))

    def instantiate(self, container):
        from . import models
        relationship_model = models.Relationship(name=self.name,
                                                 type=self.type,
                                                 relationship_template=self)
        utils.instantiate_dict(container, relationship_model.properties, self.properties)
        utils.instantiate_dict(container, relationship_model.interfaces, self.interface_templates)
        return relationship_model

    def validate(self):
        # TODO: either type or name must be set
        utils.validate_dict_values(self.properties)
        utils.validate_dict_values(self.interface_templates)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.properties, report_issues)
        utils.coerce_dict_values(self.interface_templates, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        if self.type is not None:
            console.puts('Relationship type: {0}'.format(context.style.type(self.type.name)))
        else:
            console.puts('Relationship template: {0}'.format(
                context.style.node(self.name)))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            utils.dump_dict_values(self.properties, 'Properties')
            utils.dump_interfaces(self.interface_templates, 'Interface templates')


class CapabilityTemplateBase(TemplateModelMixin):
    """
    A capability of a :class:`NodeTemplate`. Nodes expose zero or more capabilities that can be
    matched with :class:`Requirement` instances of other nodes.

    :ivar name: Name (unique for the node template)
    :vartype name: basestring
    :ivar type: Capability type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: basestring
    :ivar valid_source_node_types: Reject requirements that are not from these node types (optional)
    :vartype valid_source_node_types: [:class:`Type`]
    :ivar min_occurrences: Minimum number of requirement matches required
    :vartype min_occurrences: int
    :ivar max_occurrences: Maximum number of requirement matches allowed
    :vartype min_occurrences: int
    :ivar properties: Associated parameters
    :vartype properties: {basestring: :class:`Parameter`}
    :ivar node_template: Containing node template
    :vartype node_template: :class:`NodeTemplate`
    :ivar substitution_template_mapping: Our contribution to service substitution
    :vartype substitution_template_mapping: :class:`SubstitutionTemplateMapping`
    :ivar capabilities: Instantiated capabilities
    :vartype capabilities: [:class:`Capability`]
    """

    __tablename__ = 'capability_template'

    __private_fields__ = ['type_fk',
                          'node_template_fk']

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


    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def capabilities(cls):
        return relationship.one_to_many(cls, 'capability')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        return relationship.many_to_one(cls, 'node_template')

    @declared_attr
    def type(cls):
        return relationship.many_to_one(cls, 'type', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region many_to_many relationships

    @declared_attr
    def valid_source_node_types(cls):
        return relationship.many_to_many(cls, 'type', prefix='valid_sources')

    @declared_attr
    def properties(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='properties', dict_key='name')

    # endregion

    description = Column(Text)
    min_occurrences = Column(Integer, default=None)  # optional
    max_occurrences = Column(Integer, default=None)  # optional

    def satisfies_requirement(self,
                              source_node_template,
                              requirement,
                              target_node_template):
        # Do we match the required capability type?
        if requirement.target_capability_type and \
            requirement.target_capability_type.get_descendant(self.type.name) is None:
            return False

        # Are we in valid_source_node_types?
        if self.valid_source_node_types:
            for valid_source_node_type in self.valid_source_node_types:
                if valid_source_node_type.get_descendant(source_node_template.type.name) is None:
                    return False

        # Apply requirement constraints
        if requirement.target_node_template_constraints:
            for node_template_constraint in requirement.target_node_template_constraints:
                if not node_template_constraint.matches(source_node_template, target_node_template):
                    return False

        return True

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

    def instantiate(self, container):
        from . import models
        capability = models.Capability(name=self.name,
                                       type=self.type,
                                       min_occurrences=self.min_occurrences,
                                       max_occurrences=self.max_occurrences,
                                       occurrences=0,
                                       capability_template=self)
        utils.instantiate_dict(container, capability.properties, self.properties)
        return capability

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
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            console.puts(
                'Occurrences: {0:d}{1}'.format(
                    self.min_occurrences or 0,
                    ' to {0:d}'.format(self.max_occurrences)
                    if self.max_occurrences is not None
                    else ' or more'))
            if self.valid_source_node_types:
                console.puts('Valid source node types: {0}'.format(
                    ', '.join((str(context.style.type(v.name))
                               for v in self.valid_source_node_types))))
            utils.dump_dict_values(self.properties, 'Properties')


class InterfaceTemplateBase(TemplateModelMixin):
    """
    A typed set of :class:`OperationTemplate`.

    :ivar name: Name (unique for the node, group, or relationship template)
    :vartype name: basestring
    :ivar type: Interface type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: basestring
    :ivar inputs: Parameters that can be used by all operations in the interface
    :vartype inputs: {basestring: :class:`Parameter`}
    :ivar operation_templates: Operations
    :vartype operation_templates: {basestring: :class:`OperationTemplate`}
    :ivar node_template: Containing node template
    :vartype node_template: :class:`NodeTemplate`
    :ivar group_template: Containing group template
    :vartype group_template: :class:`GroupTemplate`
    :ivar relationship_template: Containing relationship template
    :vartype relationship_template: :class:`RelationshipTemplate`
    :ivar interfaces: Instantiated interfaces
    :vartype interfaces: [:class:`Interface`]
    """

    __tablename__ = 'interface_template'

    __private_fields__ = ['type_fk',
                          'node_template_fk',
                          'group_template_fk',
                          'relationship_template_fk']


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


    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def interfaces(cls):
        return relationship.one_to_many(cls, 'interface')

    @declared_attr
    def operation_templates(cls):
        return relationship.one_to_many(cls, 'operation_template', dict_key='name')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def relationship_template(cls):
        return relationship.many_to_one(cls, 'relationship_template')

    @declared_attr
    def group_template(cls):
        return relationship.many_to_one(cls, 'group_template')

    @declared_attr
    def node_template(cls):
        return relationship.many_to_one(cls, 'node_template')

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

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('inputs', formatting.as_raw_dict(self.inputs)),  # pylint: disable=no-member
            # TODO fix self.properties reference
            ('operation_templates', formatting.as_raw_list(self.operation_templates))))

    def instantiate(self, container):
        from . import models
        interface = models.Interface(name=self.name,
                                     type=self.type,
                                     description=deepcopy_with_locators(self.description),
                                     interface_template=self)
        utils.instantiate_dict(container, interface.inputs, self.inputs)
        utils.instantiate_dict(container, interface.operations, self.operation_templates)
        return interface

    def validate(self):
        utils.validate_dict_values(self.inputs)
        utils.validate_dict_values(self.operation_templates)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.inputs, report_issues)
        utils.coerce_dict_values(self.operation_templates, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Interface type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_dict_values(self.inputs, 'Inputs')
            utils.dump_dict_values(self.operation_templates, 'Operation templates')


class OperationTemplateBase(TemplateModelMixin):
    """
    An operation in a :class:`InterfaceTemplate`.

    Operations are executed by an associated :class:`PluginSpecification` via an executor.

    :ivar name: Name (unique for the interface or service template)
    :vartype name: basestring
    :ivar description: Human-readable description
    :vartype description: basestring
    :ivar plugin_specification: Associated plugin
    :vartype plugin_specification: :class:`PluginSpecification`
    :ivar relationship_edge: When true specified that the operation is on the relationship's
                             target edge instead of its source (only used by relationship
                             operations)
    :vartype relationship_edge: bool
    :ivar implementation: Implementation (interpreted by the plugin)
    :vartype implementation: basestring
    :ivar configuration: Configuration (interpreted by the plugin)
    :vartype configuration: {basestring, object}
    :ivar dependencies: Dependency strings (interpreted by the plugin)
    :vartype dependencies: [basestring]
    :ivar inputs: Parameters that can be used by this operation
    :vartype inputs: {basestring: :class:`Parameter`}
    :ivar executor: Name of executor to run the operation with
    :vartype executor: basestring
    :ivar max_attempts: Maximum number of attempts allowed in case of failure
    :vartype max_attempts: int
    :ivar retry_interval: Interval between retries (in seconds)
    :vartype retry_interval: int
    :ivar interface_template: Containing interface template
    :vartype interface_template: :class:`InterfaceTemplate`
    :ivar service_template: Containing service template
    :vartype service_template: :class:`ServiceTemplate`
    :ivar operations: Instantiated operations
    :vartype operations: [:class:`Operation`]
    """

    __tablename__ = 'operation_template'

    __private_fields__ = ['service_template_fk',
                          'interface_template_fk',
                          'plugin_fk']

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

    # region association proxies

    # endregion

    # region one_to_one relationships

    @declared_attr
    def plugin_specification(cls):
        return relationship.one_to_one(
            cls, 'plugin_specification', back_populates=relationship.NO_BACK_POP)

    # endregion

    # region one_to_many relationships

    @declared_attr
    def operations(cls):
        return relationship.one_to_many(cls, 'operation')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def interface_template(cls):
        return relationship.many_to_one(cls, 'interface_template')

    # endregion

    # region many_to_many relationships

    @declared_attr
    def inputs(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='inputs', dict_key='name')

    # endregion

    description = Column(Text)
    relationship_edge = Column(Boolean)
    implementation = Column(Text)
    configuration = Column(modeling_types.StrictDict(key_cls=basestring))
    dependencies = Column(modeling_types.StrictList(item_cls=basestring))
    executor = Column(Text)
    max_attempts = Column(Integer)
    retry_interval = Column(Integer)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('implementation', self.implementation),
            ('dependencies', self.dependencies),
            ('executor', self.executor),
            ('max_attempts', self.max_attempts),
            ('retry_interval', self.retry_interval),
            ('inputs', formatting.as_raw_dict(self.inputs))))

    def instantiate(self, container):
        from . import models
        if self.plugin_specification:
            if self.plugin_specification.enabled:
                plugin = self.plugin_specification.plugin
                implementation = self.implementation if plugin is not None else None
                # "plugin" would be none if a match was not found. In that case, a validation error
                # should already have been reported in ServiceTemplateBase.instantiate, so we will
                # continue silently here
            else:
                # If the plugin is disabled, the operation should be disabled, too
                plugin = None
                implementation = None
        else:
            # Using the execution plugin
            plugin = None
            implementation = self.implementation

        operation = models.Operation(name=self.name,
                                     description=deepcopy_with_locators(self.description),
                                     relationship_edge=self.relationship_edge,
                                     plugin=plugin,
                                     implementation=implementation,
                                     configuration=self.configuration,
                                     dependencies=self.dependencies,
                                     executor=self.executor,
                                     max_attempts=self.max_attempts,
                                     retry_interval=self.retry_interval,
                                     operation_template=self)
        utils.instantiate_dict(container, operation.inputs, self.inputs)
        return operation

    def validate(self):
        utils.validate_dict_values(self.inputs)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.inputs, report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            if self.plugin_specification is not None:
                console.puts('Plugin specification: {0}'.format(
                    context.style.literal(self.plugin_specification.name)))
            if self.implementation is not None:
                console.puts('Implementation: {0}'.format(
                    context.style.literal(self.implementation)))
            if self.configuration:
                with context.style.indent:
                    for k, v in self.configuration.iteritems():
                        console.puts('{0}: {1}'.format(context.style.property(k),
                                                       context.style.literal(v)))
            if self.dependencies:
                console.puts('Dependencies: {0}'.format(
                    ', '.join((str(context.style.literal(v)) for v in self.dependencies))))
            if self.executor is not None:
                console.puts('Executor: {0}'.format(context.style.literal(self.executor)))
            if self.max_attempts is not None:
                console.puts('Max attempts: {0}'.format(context.style.literal(self.max_attempts)))
            if self.retry_interval is not None:
                console.puts('Retry interval: {0}'.format(
                    context.style.literal(self.retry_interval)))
            utils.dump_dict_values(self.inputs, 'Inputs')


class ArtifactTemplateBase(TemplateModelMixin):
    """
    A file associated with a :class:`NodeTemplate`.

    :ivar name: Name (unique for the node template)
    :vartype name: basestring
    :ivar type: Artifact type
    :vartype type: :class:`Type`
    :ivar description: Human-readable description
    :vartype description: basestring
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
    :ivar node_template: Containing node template
    :vartype node_template: :class:`NodeTemplate`
    :ivar artifacts: Instantiated artifacts
    :vartype artifacts: [:class:`Artifact`]
    """

    __tablename__ = 'artifact_template'

    __private_fields__ = ['type_fk',
                          'node_template_fk']

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

    # region association proxies

    # endregion

    # region one_to_one relationships

    # endregion

    # region one_to_many relationships

    @declared_attr
    def artifacts(cls):
        return relationship.one_to_many(cls, 'artifact')

    # endregion

    # region many_to_one relationships

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

    def instantiate(self, container):
        from . import models
        artifact = models.Artifact(name=self.name,
                                   type=self.type,
                                   description=deepcopy_with_locators(self.description),
                                   source_path=self.source_path,
                                   target_path=self.target_path,
                                   repository_url=self.repository_url,
                                   repository_credential=self.repository_credential,
                                   artifact_template=self)
        utils.instantiate_dict(container, artifact.properties, self.properties)
        return artifact

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


class PluginSpecificationBase(TemplateModelMixin):
    """
    Plugin specification.

    :ivar name: Required plugin name
    :vartype name: basestring
    :ivar version: Minimum plugin version
    :vartype version: basestring
    :ivar enabled: Whether the plugin is enabled
    :vartype enabled: bool
    :ivar plugin: The matching plugin (or None if not matched)
    :vartype plugin: :class:`Plugin`
    """

    __tablename__ = 'plugin_specification'

    __private_fields__ = ['service_template_fk',
                          'plugin_fk']

    version = Column(Text)
    enabled = Column(Boolean, nullable=False, default=True)

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

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def plugin(cls): # pylint: disable=method-hidden
        return relationship.many_to_one(cls, 'plugin', back_populates=relationship.NO_BACK_POP)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('version', self.version),
            ('enabled', self.enabled)))

    def coerce_values(self, report_issues):
        pass

    def resolve(self, model_storage):
        # TODO: we are planning a separate "instantiation" module where this will be called or
        # moved to.
        plugins = model_storage.plugin.list()
        matching_plugins = []
        if plugins:
            for plugin in plugins:
                if (plugin.name == self.name) and \
                    ((self.version is None) or \
                     (VersionString(plugin.package_version) >= self.version)):
                    matching_plugins.append(plugin)
        self.plugin = None
        if matching_plugins:
            # Return highest version of plugin
            key = lambda plugin: VersionString(plugin.package_version).key
            self.plugin = sorted(matching_plugins, key=key)[-1]
        return self.plugin is not None
