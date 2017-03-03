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

from copy import deepcopy
from types import FunctionType
from datetime import datetime

from sqlalchemy import (
    Column,
    Text,
    Integer,
    DateTime
)
from sqlalchemy.ext.declarative import declared_attr

from ..parser import validation
from ..utils import collections, formatting, console
from .bases import TemplateModelMixin
from . import (
    utils,
    types as modeling_types
)


class ServiceTemplateBase(TemplateModelMixin):
    """
    A service template is a normalized blueprint from which :class:`ServiceInstance` instances can
    be created.

    It is usually created by various DSL parsers, such as ARIA's TOSCA extension. However, it can
    also be created programmatically.

    :ivar description: Human-readable description
    :vartype description: string
    :ivar meta_data: Dict of :class:`Metadata`
    :ivar node_templates: List of :class:`NodeTemplate`
    :ivar group_templates: List of :class:`GroupTemplate`
    :ivar policy_templates: List of :class:`PolicyTemplate`
    :ivar substitution_template: :class:`SubstitutionTemplate`
    :ivar inputs: Dict of :class:`Parameter`
    :ivar outputs: Dict of :class:`Parameter`
    :ivar operation_templates: Dict of :class:`OperationTemplate`
    """

    __tablename__ = 'service_template'

    description = Column(Text)

    @declared_attr
    def meta_data(cls):
        # Warning! We cannot use the attr name "metadata" because it's used by SqlAlchemy!
        return cls.many_to_many_relationship('metadata', dict_key='name')

    @declared_attr
    def node_templates(cls):
        return cls.one_to_many_relationship('node_template')

    @declared_attr
    def group_templates(cls):
        return cls.one_to_many_relationship('group_template')

    @declared_attr
    def policy_templates(cls):
        return cls.one_to_many_relationship('policy_template')

    @declared_attr
    def substitution_template(cls):
        return cls.one_to_one_relationship('substitution_template')

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs',
                                             dict_key='name')

    @declared_attr
    def outputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='outputs',
                                             dict_key='name')

    @declared_attr
    def operation_templates(cls):
        return cls.one_to_many_relationship('operation_template', dict_key='name')

    @declared_attr
    def node_types(cls):
        return cls.one_to_one_relationship('type', key='node_type_fk', backreference='')

    @declared_attr
    def group_types(cls):
        return cls.one_to_one_relationship('type', key='group_type_fk', backreference='')

    @declared_attr
    def capability_types(cls):
        return cls.one_to_one_relationship('type', key='capability_type_fk', backreference='')

    @declared_attr
    def relationship_types(cls):
        return cls.one_to_one_relationship('type', key='relationship_type_fk', backreference='')

    @declared_attr
    def policy_types(cls):
        return cls.one_to_one_relationship('type', key='policy_type_fk', backreference='')

    @declared_attr
    def artifact_types(cls):
        return cls.one_to_one_relationship('type', key='artifact_type_fk', backreference='')

    @declared_attr
    def interface_types(cls):
        return cls.one_to_one_relationship('type', key='interface_type_fk', backreference='')

    # region orchestration

    created_at = Column(DateTime, nullable=False, index=True)
    updated_at = Column(DateTime)
    main_file_name = Column(Text)

    @declared_attr
    def plugins(cls):
        return cls.one_to_many_relationship('plugin', dict_key='name')

    # endregion

    # region foreign keys

    __private_fields__ = ['substitution_template_fk']

    # ServiceTemplate one-to-one to SubstitutionTemplate
    @declared_attr
    def substitution_template_fk(cls):
        return cls.foreign_key('substitution_template', nullable=True)

    # ServiceTemplate one-to-one to Type
    @declared_attr
    def node_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # ServiceTemplate one-to-one to Type
    @declared_attr
    def group_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # ServiceTemplate one-to-one to Type
    @declared_attr
    def capability_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # ServiceTemplate one-to-one to Type
    @declared_attr
    def relationship_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # ServiceTemplate one-to-one to Type
    @declared_attr
    def policy_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # ServiceTemplate one-to-one to Type
    @declared_attr
    def artifact_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # ServiceTemplate one-to-one to Type
    @declared_attr
    def interface_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # endregion

    def get_node_template(self, node_template_name):
        if self.node_templates:
            for node_template in self.node_templates:
                if node_template.name == node_template_name:
                    return node_template
        return None

    def get_group_template(self, group_template_name):
        if self.group_templates:
            for group_template in self.group_templates:
                if group_template.name == group_template_name:
                    return group_template
        return None

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
            ('operation_templates', formatting.as_raw_list(self.operation_templates))))

    @property
    def types_as_raw(self):
        return collections.OrderedDict((
            ('node_types', formatting.as_raw(self.node_types)),
            ('group_types', formatting.as_raw(self.group_types)),
            ('capability_types', formatting.as_raw(self.capability_types)),
            ('relationship_types', formatting.as_raw(self.relationship_types)),
            ('policy_types', formatting.as_raw(self.policy_types)),
            ('artifact_types', formatting.as_raw(self.artifact_types)),
            ('interface_types', formatting.as_raw(self.interface_types))))

    def instantiate(self, context, container):
        from . import models
        now = datetime.now()
        service = models.Service(created_at=now,
                                 updated_at=now,
                                 description=deepcopy_with_locators(self.description),
                                 service_template=self)
        #service.name = '{0}_{1}'.format(self.name, service.id)

        context.modeling.instance = service

        utils.instantiate_dict(context, self, service.meta_data, self.meta_data)

        for node_template in self.node_templates:
            for _ in range(node_template.default_instances):
                node = node_template.instantiate(context, container)
                service.nodes.append(node)

        utils.instantiate_list(context, self, service.groups, self.group_templates)
        utils.instantiate_list(context, self, service.policies, self.policy_templates)
        utils.instantiate_dict(context, self, service.operations, self.operation_templates)

        if self.substitution_template is not None:
            service.substitution = self.substitution_template.instantiate(context, container)

        utils.instantiate_dict(context, self, service.inputs, self.inputs)
        utils.instantiate_dict(context, self, service.outputs, self.outputs)

        for name, the_input in context.modeling.inputs.iteritems():
            if name not in service.inputs:
                context.validation.report('input "{0}" is not supported'.format(name))
            else:
                service.inputs[name].value = the_input

        return service

    def validate(self, context):
        utils.validate_dict_values(context, self.meta_data)
        utils.validate_list_values(context, self.node_templates)
        utils.validate_list_values(context, self.group_templates)
        utils.validate_list_values(context, self.policy_templates)
        if self.substitution_template is not None:
            self.substitution_template.validate(context)
        utils.validate_dict_values(context, self.inputs)
        utils.validate_dict_values(context, self.outputs)
        utils.validate_dict_values(context, self.operation_templates)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.meta_data, report_issues)
        utils.coerce_list_values(context, container, self.node_templates, report_issues)
        utils.coerce_list_values(context, container, self.group_templates, report_issues)
        utils.coerce_list_values(context, container, self.policy_templates, report_issues)
        if self.substitution_template is not None:
            self.substitution_template.coerce_values(context, container, report_issues)
        utils.coerce_dict_values(context, container, self.inputs, report_issues)
        utils.coerce_dict_values(context, container, self.outputs, report_issues)
        utils.coerce_dict_values(context, container, self.operation_templates, report_issues)

    def dump(self, context):
        if self.description is not None:
            console.puts(context.style.meta(self.description))
        utils.dump_dict_values(context, self.meta_data, 'Metadata')

        for node_template in self.node_templates:
            node_template.dump(context)
        for group_template in self.group_templates:
            group_template.dump(context)
        for policy_template in self.policy_templates:
            policy_template.dump(context)
        if self.substitution_template is not None:
            self.substitution_template.dump(context)
        utils.dump_dict_values(context, self.inputs, 'Inputs')
        utils.dump_dict_values(context, self.outputs, 'Outputs')
        utils.dump_dict_values(context, self.operation_templates, 'Operation templates')

    def dump_types(self, context):
        if self.node_types.children:
            console.puts('Node types:')
            self.node_types.dump(context)
        if self.group_types.children:
            console.puts('Group types:')
            self.group_types.dump(context)
        if self.capability_types.children:
            console.puts('Capability types:')
            self.capability_types.dump(context)
        if self.relationship_types.children:
            console.puts('Relationship types:')
            self.relationship_types.dump(context)
        if self.policy_types.children:
            console.puts('Policy types:')
            self.policy_types.dump(context)
        if self.policy_trigger_types.children:
            console.puts('Policy trigger types:')
            self.policy_trigger_types.dump(context)
        if self.artifact_types.children:
            console.puts('Artifact types:')
            self.artifact_types.dump(context)
        if self.interface_types.children:
            console.puts('Interface types:')
            self.interface_types.dump(context)


class NodeTemplateBase(TemplateModelMixin):
    """
    A template for creating zero or more :class:`Node` instances.

    :ivar name: Name (will be used as a prefix for node IDs)
    :ivar description: Description
    :ivar default_instances: Default number nodes that will appear in the deployment plan
    :ivar min_instances: Minimum number nodes that will appear in the deployment plan
    :ivar max_instances: Maximum number nodes that will appear in the deployment plan
    :ivar properties: Dict of :class:`Parameter`
    :ivar interface_templates: Dict of :class:`InterfaceTemplate`
    :ivar artifact_templates: Dict of :class:`ArtifactTemplate`
    :ivar capability_templates: Dict of :class:`CapabilityTemplate`
    :ivar requirement_templates: List of :class:`RequirementTemplate`
    :ivar target_node_template_constraints: List of :class:`FunctionType`
    """

    __tablename__ = 'node_template'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    description = Column(Text)
    default_instances = Column(Integer, default=1)
    min_instances = Column(Integer, default=0)
    max_instances = Column(Integer, default=None)
    target_node_template_constraints = Column(modeling_types.StrictList(FunctionType))

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def interface_templates(cls):
        return cls.one_to_many_relationship('interface_template', dict_key='name')

    @declared_attr
    def artifact_templates(cls):
        return cls.one_to_many_relationship('artifact_template', dict_key='name')

    @declared_attr
    def capability_templates(cls):
        return cls.one_to_many_relationship('capability_template', dict_key='name')

    @declared_attr
    def requirement_templates(cls):
        return cls.one_to_many_relationship('requirement_template',
                                            foreign_key='node_template_fk')

    # region orchestration

    @declared_attr
    def plugins(cls):
        return cls.many_to_many_relationship('plugin', dict_key='name')

    # endregion

    # region foreign_keys

    __private_fields__ = ['type_fk',
                          'service_template_fk']

    # NodeTemplate many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # ServiceTemplate one-to-many to NodeTemplate
    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template')

    # endregion

    def is_target_node_valid(self, target_node_template):
        if self.target_node_template_constraints:
            for node_type_constraint in self.target_node_template_constraints:
                if not node_type_constraint(target_node_template, self):
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
            ('interface_templates', formatting.as_raw_list(self.interface_templates)),
            ('artifact_templates', formatting.as_raw_list(self.artifact_templates)),
            ('capability_templates', formatting.as_raw_list(self.capability_templates)),
            ('requirement_templates', formatting.as_raw_list(self.requirement_templates))))

    def instantiate(self, context, *args, **kwargs):
        from . import models
        name = context.modeling.generate_node_id(self.name)
        node = models.Node(name=name,
                           type=self.type,
                           state='',
                           node_template=self)
        utils.instantiate_dict(context, node, node.properties, self.properties)
        utils.instantiate_dict(context, node, node.interfaces, self.interface_templates)
        utils.instantiate_dict(context, node, node.artifacts, self.artifact_templates)
        utils.instantiate_dict(context, node, node.capabilities, self.capability_templates)
        return node

    def validate(self, context):
        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interface_templates)
        utils.validate_dict_values(context, self.artifact_templates)
        utils.validate_dict_values(context, self.capability_templates)
        utils.validate_list_values(context, self.requirement_templates)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)
        utils.coerce_dict_values(context, self, self.interface_templates, report_issues)
        utils.coerce_dict_values(context, self, self.artifact_templates, report_issues)
        utils.coerce_dict_values(context, self, self.capability_templates, report_issues)
        utils.coerce_list_values(context, self, self.requirement_templates, report_issues)

    def dump(self, context):
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
            utils.dump_dict_values(context, self.properties, 'Properties')
            utils.dump_interfaces(context, self.interface_templates)
            utils.dump_dict_values(context, self.artifact_templates, 'Artifact templates')
            utils.dump_dict_values(context, self.capability_templates, 'Capability templates')
            utils.dump_list_values(context, self.requirement_templates, 'Requirement templates')


class GroupTemplateBase(TemplateModelMixin):
    """
    A template for creating zero or more :class:`Group` instances.

    Groups are logical containers for zero or more nodes that allow applying zero or more
    :class:`GroupPolicy` instances to the nodes together.

    :ivar name: Name (will be used as a prefix for group IDs)
    :ivar description: Description
    :ivar properties: Dict of :class:`Parameter`
    :ivar interface_templates: Dict of :class:`InterfaceTemplate`
    """

    __tablename__ = 'group_template'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    description = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def interface_templates(cls):
        return cls.one_to_many_relationship('interface_template', dict_key='name')

    @declared_attr
    def node_templates(cls):
        return cls.many_to_many_relationship('node_template')

    # region foreign keys

    __private_fields__ = ['type_fk',
                          'service_template_fk']

    # GroupTemplate many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # ServiceTemplate one-to-many to GroupTemplate
    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates))))

    def instantiate(self, context, *args, **kwargs):
        from . import models
        group = models.Group(name=self.name,
                             type=self.type,
                             group_template=self)
        utils.instantiate_dict(context, self, group.properties, self.properties)
        utils.instantiate_dict(context, self, group.interfaces, self.interface_templates)
        if self.node_templates:
            for node_template in self.node_templates:
                group.nodes += node_template.nodes.all()
        return group

    def validate(self, context):
        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interface_templates)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)
        utils.coerce_dict_values(context, self, self.interface_templates, report_issues)

    def dump(self, context):
        console.puts('Group template: {0}'.format(context.style.node(self.name)))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_dict_values(context, self.properties, 'Properties')
            utils.dump_interfaces(context, self.interface_templates)
            if self.node_templates:
                console.puts('Member node templates: {0}'.format(', '.join(
                    (str(context.style.node(v.name)) for v in self.node_templates))))


class PolicyTemplateBase(TemplateModelMixin):
    """
    Policies can be applied to zero or more :class:`NodeTemplate` or :class:`GroupTemplate`
    instances.

    :ivar name: Name
    :ivar description: Description
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'policy_template'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    description = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def node_templates(cls):
        return cls.many_to_many_relationship('node_template')

    @declared_attr
    def group_templates(cls):
        return cls.many_to_many_relationship('group_template')

    # region foreign keys

    __private_fields__ = ['type_fk',
                          'service_template_fk']

    # PolicyTemplate many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # ServiceTemplate one-to-many to PolicyTemplate
    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('properties', formatting.as_raw_dict(self.properties))))

    def instantiate(self, context, *args, **kwargs):
        from . import models
        policy = models.Policy(name=self.name,
                               type=self.type,
                               policy_template=self)
        utils.instantiate_dict(context, self, policy.properties, self.properties)
        if self.node_templates:
            for node_template in self.node_templates:
                policy.nodes += node_template.nodes.all()
        if self.group_templates:
            for group_template in self.group_templates:
                policy.groups += group_template.groups.all()
        return policy

    def validate(self, context):
        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)

    def dump(self, context):
        console.puts('Policy template: {0}'.format(context.style.node(self.name)))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_dict_values(context, self.properties, 'Properties')
            if self.node_templates:
                console.puts('Target node templates: {0}'.format(', '.join(
                    (str(context.style.node(v.name)) for v in self.node_templates))))
            if self.group_templates:
                console.puts('Target group templates: {0}'.format(', '.join(
                    (str(context.style.node(v.name)) for v in self.group_templates))))


class SubstitutionTemplateBase(TemplateModelMixin):
    """
    Used to substitute a single node for the entire deployment.

    :ivar mappings: Dict of :class:` SubstitutionTemplateMapping`
    """

    __tablename__ = 'substitution_template'

    @declared_attr
    def node_type(cls):
        return cls.many_to_one_relationship('type')

    @declared_attr
    def mappings(cls):
        return cls.one_to_many_relationship('substitution_template_mapping', dict_key='name')

    # region foreign keys

    __private_fields__ = ['node_type_fk']

    # SubstitutionTemplate many-to-one to Type
    @declared_attr
    def node_type_fk(cls):
        return cls.foreign_key('type')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('node_type_name', self.node_type.name),
            ('mappings', formatting.as_raw_dict(self.mappings))))

    def instantiate(self, context, container):
        from . import models
        substitution = models.Substitution(node_type=self.node_type,
                                           substitution_template=self)
        utils.instantiate_dict(context, container, substitution.mappings, self.mappings)
        return substitution

    def validate(self, context):
        utils.validate_dict_values(context, self.mappings)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.mappings, report_issues)

    def dump(self, context):
        console.puts('Substitution template:')
        with context.style.indent:
            console.puts('Node type: {0}'.format(context.style.type(self.node_type.name)))
            utils.dump_dict_values(context, self.mappings, 'Mappings')


class SubstitutionTemplateMappingBase(TemplateModelMixin):
    """
    Used by :class:`SubstitutionTemplate` to map a capability or a requirement to a node.

    :ivar name: Exposed capability or requirement name
    """

    __tablename__ = 'substitution_template_mapping'

    @declared_attr
    def node_template(cls):
        return cls.one_to_one_relationship('node_template')

    @declared_attr
    def capability_template(cls):
        return cls.one_to_one_relationship('capability_template')

    @declared_attr
    def requirement_template(cls):
        return cls.one_to_one_relationship('requirement_template')

    # region foreign keys

    __private_fields__ = ['substitution_template_fk',
                          'node_template_fk',
                          'capability_template_fk',
                          'requirement_template_fk']

    # SubstitutionTemplate one-to-many to SubstitutionTemplateMapping
    @declared_attr
    def substitution_template_fk(cls):
        return cls.foreign_key('substitution_template')

    # SubstitutionTemplate one-to-one to NodeTemplate
    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template')

    # SubstitutionTemplate one-to-one to CapabilityTemplate
    @declared_attr
    def capability_template_fk(cls):
        return cls.foreign_key('capability_template', nullable=True)

    # SubstitutionTemplate one-to-one to RequirementTemplate
    @declared_attr
    def requirement_template_fk(cls):
        return cls.foreign_key('requirement_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name)))

    def instantiate(self, context, *args, **kwargs):
        from . import models
        nodes = context.modeling.instance.find_nodes(self.node_template.name)
        if len(nodes) == 0:
            context.validation.report(
                'mapping "{0}" refers to node template "{1}" but there are no '
                'node instances'.format(self.mapped_name, self.node_template.name),
                level=validation.Issue.BETWEEN_INSTANCES)
            return None
        # The TOSCA spec does not provide a way to choose the node, so we will just pick the first
        # one
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

    def validate(self, context):
        if (self.capability_template is None) and (self.requirement_template is None):
            context.validation.report('mapping "{0}" refers to neither capability nor a requirement'
                                      ' in node template: {1}'.format(
                                          self.name,
                                          formatting.safe_repr(self.node_template.name)),
                                      level=validation.Issue.BETWEEN_TYPES)

    def dump(self, context):
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

    :ivar name: Name
    :ivar target_node_template_constraints: List of :class:`FunctionType`
    :ivar target_capability_name: Name of capability in target node
    :ivar relationship_template: :class:`RelationshipTemplate`
    """

    __tablename__ = 'requirement_template'

    @declared_attr
    def target_node_type(cls):
        return cls.many_to_one_relationship('type', key='target_node_type_fk', backreference='')

    @declared_attr
    def target_node_template(cls):
        return cls.one_to_one_relationship('node_template', key='target_node_template_fk',
                                           backreference='')

    @declared_attr
    def target_capability_type(cls):
        return cls.one_to_one_relationship('type', key='target_capability_type_fk',
                                           backreference='')

    target_node_template_constraints = Column(modeling_types.StrictList(FunctionType))
    target_capability_name = Column(Text)

    @declared_attr
    def relationship_template(cls):
        return cls.one_to_one_relationship('relationship_template')

    # region foreign keys

    __private_fields__ = ['target_node_type_fk',
                          'target_node_template_fk',
                          'target_capability_type_fk'
                          'node_template_fk',
                          'relationship_template_fk']

    # RequirementTemplate many-to-one to Type
    @declared_attr
    def target_node_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # RequirementTemplate one-to-one to NodeTemplate
    @declared_attr
    def target_node_template_fk(cls):
        return cls.foreign_key('node_template', nullable=True)

    # RequirementTemplate one-to-one to NodeTemplate
    @declared_attr
    def target_capability_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # NodeTemplate one-to-many to RequirementTemplate
    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template')

    # RequirementTemplate one-to-one to RelationshipTemplate
    @declared_attr
    def relationship_template_fk(cls):
        return cls.foreign_key('relationship_template', nullable=True)

    # endregion

    def find_target(self, context, source_node_template):
        # We might already have a specific node template, so we'll just verify it
        if self.target_node_template is not None:
            if not source_node_template.is_target_node_valid(self.target_node_template):
                context.validation.report('requirement "{0}" of node template "{1}" is for node '
                                          'template "{2}" but it does not match constraints'.format(
                                              self.name,
                                              self.target_node_template_name,
                                              source_node_template.name),
                                          level=validation.Issue.BETWEEN_TYPES)
            if (self.target_capability_type is not None) \
                or (self.target_capability_name is not None):
                target_node_capability = self.find_target_capability(context,
                                                                     source_node_template,
                                                                     self.target_node_template)
                if target_node_capability is None:
                    return None, None
            else:
                target_node_capability = None

            return self.target_node_template, target_node_capability

        # Find first node that matches the type
        elif self.target_node_type is not None:
            for target_node_template in context.modeling.template.node_templates:
                if self.target_node_type.get_descendant(target_node_template.type.name) is None:
                    continue

                if not source_node_template.is_target_node_valid(target_node_template):
                    continue

                target_node_capability = self.find_target_capability(context,
                                                                     source_node_template,
                                                                     target_node_template)
                if target_node_capability is None:
                    continue

                return target_node_template, target_node_capability

        return None, None

    def find_target_capability(self, context, source_node_template, target_node_template):
        for capability_template in target_node_template.capability_templates.itervalues():
            if capability_template.satisfies_requirement(context,
                                                         source_node_template,
                                                         self,
                                                         target_node_template):
                return capability_template
        return None

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('target_node_type_name', self.target_node_type.name),
            ('target_node_template_name', self.target_node_template_name),
            ('target_capability_type_name', self.target_capability_type_name),
            ('target_capability_name', self.target_capability_name),
            ('relationship_template', formatting.as_raw(self.relationship_template))))

    def validate(self, context):
        if self.relationship_template:
            self.relationship_template.validate(context)

    def coerce_values(self, context, container, report_issues):
        if self.relationship_template is not None:
            self.relationship_template.coerce_values(context, container, report_issues)

    def dump(self, context):
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
                    self.relationship_template.dump(context)


class RelationshipTemplateBase(TemplateModelMixin):
    """
    Optional addition to a :class:`RequirementTemplate` in :class:`NodeTemplate` that can be applied
    when the requirement is matched with a capability.

    :ivar description: Description
    :ivar properties: Dict of :class:`Parameter`
    :ivar interface_templates: Dict of :class:`InterfaceTemplate`
    """

    __tablename__ = 'relationship_template'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    description = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    @declared_attr
    def interface_templates(cls):
        return cls.one_to_many_relationship('interface_template', dict_key='name')

    # region foreign keys

    __private_fields__ = ['type_fk']

    # RelationshipTemplate many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('type_name', self.type.name if self.type is not None else None),
            ('name', self.name),
            ('description', self.description),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates))))

    def instantiate(self, context, container):
        from . import models
        relationship = models.Relationship(type=self.type,
                                           relationship_template=self)
        utils.instantiate_dict(context, container,
                               relationship.properties, self.properties)
        utils.instantiate_dict(context, container,
                               relationship.interfaces, self.interface_templates)
        return relationship

    def validate(self, context):
        # TODO: either type or name must be set
        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interface_templates)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)
        utils.coerce_dict_values(context, self, self.interface_templates, report_issues)

    def dump(self, context):
        if self.type is not None:
            console.puts('Relationship type: {0}'.format(context.style.type(self.type.name)))
        else:
            console.puts('Relationship template: {0}'.format(
                context.style.node(self.name)))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            utils.dump_dict_values(context, self.properties, 'Properties')
            utils.dump_interfaces(context, self.interface_templates, 'Interface templates')


class CapabilityTemplateBase(TemplateModelMixin):
    """
    A capability of a :class:`NodeTemplate`. Nodes expose zero or more capabilities that can be
    matched with :class:`Requirement` instances of other nodes.

    :ivar name: Name
    :ivar description: Description
    :ivar min_occurrences: Minimum number of requirement matches required
    :ivar max_occurrences: Maximum number of requirement matches allowed
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'capability_template'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    description = Column(Text)
    min_occurrences = Column(Integer, default=None)  # optional
    max_occurrences = Column(Integer, default=None)  # optional

    @declared_attr
    def valid_source_node_types(cls):
        return cls.many_to_many_relationship('type', table_prefix='valid_sources')

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    # region foreign keys

    __private_fields__ = ['type_fk',
                          'node_template_fk']

    # CapabilityTemplate many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # NodeTemplate one-to-many to CapabilityTemplate
    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template')

    # endregion

    def satisfies_requirement(self,
                              context,
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
            for node_type_constraint in requirement.target_node_template_constraints:
                if not node_type_constraint(target_node_template, source_node_template):
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
            ('valid_source_node_type_names', self.valid_source_node_type_names),
            ('properties', formatting.as_raw_dict(self.properties))))

    def instantiate(self, context, container):
        from . import models
        capability = models.Capability(name=self.name,
                                       type=self.type,
                                       min_occurrences=self.min_occurrences,
                                       max_occurrences=self.max_occurrences,
                                       occurrences=0,
                                       capability_template=self)
        utils.instantiate_dict(context, container, capability.properties, self.properties)
        return capability

    def validate(self, context):
        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)

    def dump(self, context):
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
            utils.dump_dict_values(context, self.properties, 'Properties')


class InterfaceTemplateBase(TemplateModelMixin):
    """
    A typed set of :class:`OperationTemplate`.

    :ivar name: Name
    :ivar description: Description
    :ivar inputs: Dict of :class:`Parameter`
    :ivar operation_templates: Dict of :class:`OperationTemplate`
    """

    __tablename__ = 'interface_template'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    description = Column(Text)

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs',
                                             dict_key='name')
    @declared_attr
    def operation_templates(cls):
        return cls.one_to_many_relationship('operation_template', dict_key='name')

    # region foreign keys

    __private_fields__ = ['type_fk',
                          'node_template_fk',
                          'group_template_fk',
                          'relationship_template_fk']

    # InterfaceTemplate many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # NodeTemplate one-to-many to InterfaceTemplate
    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template', nullable=True)

    # GroupTemplate one-to-many to InterfaceTemplate
    @declared_attr
    def group_template_fk(cls):
        return cls.foreign_key('group_template', nullable=True)

    # RelationshipTemplate one-to-many to InterfaceTemplate
    @declared_attr
    def relationship_template_fk(cls):
        return cls.foreign_key('relationship_template', nullable=True)

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type.name),
            ('inputs', formatting.as_raw_dict(self.inputs)),  # pylint: disable=no-member
            # TODO fix self.properties reference
            ('operation_templates', formatting.as_raw_list(self.operation_templates))))

    def instantiate(self, context, container):
        from . import models
        interface = models.Interface(name=self.name,
                                     description=deepcopy_with_locators(self.description),
                                     type=self.type,
                                     interface_template=self)
        utils.instantiate_dict(context, container, interface.inputs, self.inputs)
        utils.instantiate_dict(context, container, interface.operations, self.operation_templates)
        return interface

    def validate(self, context):
        utils.validate_dict_values(context, self.inputs)
        utils.validate_dict_values(context, self.operation_templates)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, container, self.inputs, report_issues)
        utils.coerce_dict_values(context, container, self.operation_templates, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Interface type: {0}'.format(context.style.type(self.type.name)))
            utils.dump_dict_values(context, self.inputs, 'Inputs')
            utils.dump_dict_values(context, self.operation_templates, 'Operation templates')


class OperationTemplateBase(TemplateModelMixin):
    """
    An operation in a :class:`InterfaceTemplate`.

    :ivar name: Name
    :ivar description: Description
    :ivar implementation: Implementation string (interpreted by the orchestrator)
    :ivar dependencies: List of strings (interpreted by the orchestrator)
    :ivar executor: Executor string (interpreted by the orchestrator)
    :ivar max_retries: Maximum number of retries allowed in case of failure
    :ivar retry_interval: Interval between retries
    :ivar inputs: Dict of :class:`Parameter`
    """

    __tablename__ = 'operation_template'

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

    executor = Column(Text)
    max_retries = Column(Integer)
    retry_interval = Column(Integer)

    # region foreign keys

    __private_fields__ = ['service_template_fk',
                          'interface_template_fk',
                          'plugin_fk']

    # ServiceTemplate one-to-many to OperationTemplate
    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template', nullable=True)

    # InterfaceTemplate one-to-many to OperationTemplate
    @declared_attr
    def interface_template_fk(cls):
        return cls.foreign_key('interface_template', nullable=True)

    # OperationTemplate one-to-one to Plugin
    @declared_attr
    def plugin_fk(cls):
        return cls.foreign_key('plugin', nullable=True)

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

    def instantiate(self, context, container):
        from . import models
        operation = models.Operation(name=self.name,
                                     description=deepcopy_with_locators(self.description),
                                     implementation=self.implementation,
                                     dependencies=self.dependencies,
                                     plugin=self.plugin,
                                     executor=self.executor,
                                     max_retries=self.max_retries,
                                     retry_interval=self.retry_interval,
                                     operation_template=self)
        utils.instantiate_dict(context, container, operation.inputs, self.inputs)
        return operation

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
                console.puts('Dependencies: {0}'.format(
                    ', '.join((str(context.style.literal(v)) for v in self.dependencies))))
            if self.executor is not None:
                console.puts('Executor: {0}'.format(context.style.literal(self.executor)))
            if self.max_retries is not None:
                console.puts('Max retries: {0}'.format(context.style.literal(self.max_retries)))
            if self.retry_interval is not None:
                console.puts('Retry interval: {0}'.format(
                    context.style.literal(self.retry_interval)))
            utils.dump_dict_values(context, self.inputs, 'Inputs')


class ArtifactTemplateBase(TemplateModelMixin):
    """
    A file associated with a :class:`NodeTemplate`.

    :ivar name: Name
    :ivar description: Description
    :ivar source_path: Source path (CSAR or repository)
    :ivar target_path: Path at destination machine
    :ivar repository_url: Repository URL
    :ivar repository_credential: Dict of string
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'artifact_template'

    @declared_attr
    def type(cls):
        return cls.many_to_one_relationship('type')

    description = Column(Text)
    source_path = Column(Text)
    target_path = Column(Text)
    repository_url = Column(Text)
    repository_credential = Column(modeling_types.StrictDict(basestring, basestring))

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             dict_key='name')

    # region foreign keys

    __private_fields__ = ['type_fk',
                          'node_template_fk']

    # ArtifactTemplate many-to-one to Type
    @declared_attr
    def type_fk(cls):
        return cls.foreign_key('type')

    # NodeTemplate one-to-many to ArtifactTemplate
    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template')

    # endregion

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

    def instantiate(self, context, container):
        from . import models
        artifact = models.Artifact(name=self.name,
                                   type=self.type,
                                   source_path=self.source_path,
                                   description=deepcopy_with_locators(self.description),
                                   target_path=self.target_path,
                                   repository_url=self.repository_url,
                                   repository_credential=self.repository_credential,
                                   artifact_template=self)
        utils.instantiate_dict(context, container, artifact.properties, self.properties)
        return artifact

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
            utils.dump_dict_values(context, self.properties, 'Properties')


def deepcopy_with_locators(value):
    """
    Like :code:`deepcopy`, but also copies over locators.
    """

    res = deepcopy(value)
    copy_locators(res, value)
    return res


def copy_locators(target, source):
    """
    Copies over :code:`_locator` for all elements, recursively.

    Assumes that target and source have exactly the same list/dict structure.
    """

    locator = getattr(source, '_locator', None)
    if locator is not None:
        try:
            setattr(target, '_locator', locator)
        except AttributeError:
            pass

    if isinstance(target, list) and isinstance(source, list):
        for i, _ in enumerate(target):
            copy_locators(target[i], source[i])
    elif isinstance(target, dict) and isinstance(source, dict):
        for k, v in target.items():
            copy_locators(v, source[k])
