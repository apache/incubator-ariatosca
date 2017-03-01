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

# pylint: disable=too-many-lines

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

from ..storage import exceptions
from ..parser import validation
from ..parser.modeling import utils as parser_utils
from ..utils import collections, formatting, console
from .service import _InstanceModelMixin
from . import (
    utils,
    types as modeling_types
)

# pylint: disable=no-self-argument, no-member, abstract-method



class _TemplateModelMixin(_InstanceModelMixin):
    """
    Mixin for :class:`ServiceTemplate` models.

    All model models can be instantiated into :class:`ServiceInstance` models.
    """

    def instantiate(self, context, container):
        raise NotImplementedError


class ServiceTemplateBase(_TemplateModelMixin):
    """
    A service template is a normalized blueprint from which :class:`ServiceInstance` instances can
    be created.

    It is usually created by various DSL parsers, such as ARIA's TOSCA extension. However, it can
    also be created programmatically.

    :ivar description: Human-readable description
    :ivar meta_data: Dict of :class:`Metadata`
    :ivar node_templates: List of :class:`NodeTemplate`
    :ivar group_templates: List of :class:`GroupTemplate`
    :ivar policy_templates: List of :class:`PolicyTemplate`
    :ivar substitution_template: :class:`SubstitutionTemplate`
    :ivar inputs: Dict of :class:`Parameter`
    :ivar outputs: Dict of :class:`Parameter`
    :ivar operation_templates: Dict of :class:`OperationTemplate`
    """

    __tablename__ = 'service_template' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['substitution_template_fk']

    description = Column(Text)

    @declared_attr
    def meta_data(cls):
        # Warning! We cannot use the attr name "metadata" because it's used by SqlAlchemy!
        return cls.many_to_many_relationship('metadata', key_column_name='name')

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
                                             key_column_name='name')

    @declared_attr
    def outputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='outputs',
                                             key_column_name='name')

    @declared_attr
    def operation_templates(cls):
        return cls.one_to_many_relationship('operation_template', key_column_name='name')

    # region orchestrator required columns

    created_at = Column(DateTime, nullable=False, index=True)
    updated_at = Column(DateTime)
    main_file_name = Column(Text)

    @declared_attr
    def plugins(cls):
        return cls.one_to_many_relationship('plugin', key_column_name='name')

    # endregion

    # region foreign keys

    # ServiceTemplate one-to-one to SubstitutionTemplate
    @declared_attr
    def substitution_template_fk(cls):
        return cls.foreign_key('substitution_template', nullable=True)

    # endregion

    def get_node_template(self, node_template_name):
        if self.node_templates:
            for node_template in self.node_templates:
                if node_template.name == node_template_name:
                    return node_template
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
        utils.dump_parameters(context, self.meta_data, 'Metadata')

        for node_template in self.node_templates:
            node_template.dump(context)
        for group_template in self.group_templates:
            group_template.dump(context)
        for policy_template in self.policy_templates:
            policy_template.dump(context)
        if self.substitution_template is not None:
            self.substitution_template.dump(context)
        utils.dump_parameters(context, self.inputs, 'Inputs')
        utils.dump_parameters(context, self.outputs, 'Outputs')
        utils.dump_dict_values(context, self.operation_templates, 'Operation templates')


class NodeTemplateBase(_TemplateModelMixin):
    """
    A template for creating zero or more :class:`Node` instances.

    :ivar name: Name (will be used as a prefix for node IDs)
    :ivar description: Description
    :ivar type_name: Must be represented in the :class:`ModelingContext`
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

    __tablename__ = 'node_template' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['service_template_fk']

    description = Column(Text)
    type_name = Column(Text)
    default_instances = Column(Integer, default=1)
    min_instances = Column(Integer, default=0)
    max_instances = Column(Integer, default=None)
    target_node_template_constraints = Column(modeling_types.StrictList(FunctionType))

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    @declared_attr
    def interface_templates(cls):
        return cls.one_to_many_relationship('interface_template', key_column_name='name')

    @declared_attr
    def artifact_templates(cls):
        return cls.one_to_many_relationship('artifact_template', key_column_name='name')

    @declared_attr
    def capability_templates(cls):
        return cls.one_to_many_relationship('capability_template', key_column_name='name')

    @declared_attr
    def requirement_templates(cls):
        return cls.one_to_many_relationship('requirement_template')

    # region orchestrator required columns

    @declared_attr
    def plugins(cls):
        return cls.many_to_many_relationship('plugin', key_column_name='name')

    # endregion

    # region foreign_keys

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
            ('type_name', self.type_name),
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
                           type_name=self.type_name,
                           state='',
                           node_template=self)
        utils.instantiate_dict(context, node, node.properties, self.properties)
        utils.instantiate_dict(context, node, node.interfaces, self.interface_templates)
        utils.instantiate_dict(context, node, node.artifacts, self.artifact_templates)
        utils.instantiate_dict(context, node, node.capabilities, self.capability_templates)
        return node

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.type_name) is None:
            context.validation.report('node template "{0}" has an unknown type: {1}'.format(
                self.name,
                formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

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
            console.puts('Type: {0}'.format(context.style.type(self.type_name)))
            console.puts('Instances: {0:d} ({1:d}{2})'.format(
                self.default_instances,
                self.min_instances,
                ' to {0:d}'.format(self.max_instances)
                if self.max_instances is not None
                else ' or more'))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interface_templates)
            utils.dump_dict_values(context, self.artifact_templates, 'Artifact templates')
            utils.dump_dict_values(context, self.capability_templates, 'Capability templates')
            utils.dump_list_values(context, self.requirement_templates, 'Requirement templates')


class GroupTemplateBase(_TemplateModelMixin):
    """
    A template for creating zero or more :class:`Group` instances.

    Groups are logical containers for zero or more nodes that allow applying zero or more
    :class:`GroupPolicy` instances to the nodes together.

    :ivar name: Name (will be used as a prefix for group IDs)
    :ivar description: Description
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar properties: Dict of :class:`Parameter`
    :ivar interface_templates: Dict of :class:`InterfaceTemplate`
    :ivar member_node_template_names: Must be represented in the :class:`ServiceTemplate`
    :ivar member_group_template_names: Must be represented in the :class:`ServiceTemplate`
    """

    __tablename__ = 'group_template' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['service_template_fk']

    description = Column(Text)
    type_name = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    @declared_attr
    def interface_templates(cls):
        return cls.one_to_many_relationship('interface_template', key_column_name='name')

    member_node_template_names = Column(modeling_types.StrictList(basestring))
    member_group_template_names = Column(modeling_types.StrictList(basestring))

    # region foreign keys

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
            ('type_name', self.type_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates)),
            ('member_node_template_names', self.member_node_template_names),
            ('member_group_template_names', self.member_group_template_names1)))

    def instantiate(self, context, *args, **kwargs):
        from . import models
        group = models.Group(name=self.name,
                             type_name=self.type_name,
                             group_template=self)
        utils.instantiate_dict(context, self, group.properties, self.properties)
        utils.instantiate_dict(context, self, group.interfaces, self.interface_templates)
        if self.member_node_template_names:
            group.member_node_ids = []
            for member_node_template_name in self.member_node_template_names:
                group.member_node_ids += \
                    context.modeling.instance.get_node_ids(member_node_template_name)
        if self.member_group_template_names:
            group.member_group_ids = []
            for member_group_template_name in self.member_group_template_names:
                group.member_group_ids += \
                    context.modeling.instance.get_group_ids(member_group_template_name)
        return group

    def validate(self, context):
        if context.modeling.group_types.get_descendant(self.type_name) is None:
            context.validation.report('group template "{0}" has an unknown type: {1}'.format(
                self.name, formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

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
            if self.type_name:
                console.puts('Type: {0}'.format(context.style.type(self.type_name)))
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interface_templates)
            if self.member_node_template_names:
                console.puts('Member node templates: {0}'.format(', '.join(
                    (str(context.style.node(v)) for v in self.member_node_template_names))))


class PolicyTemplateBase(_TemplateModelMixin):
    """
    Policies can be applied to zero or more :class:`NodeTemplate` or :class:`GroupTemplate`
    instances.

    :ivar name: Name
    :ivar description: Description
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar properties: Dict of :class:`Parameter`
    :ivar target_node_template_names: Must be represented in the :class:`ServiceTemplate`
    :ivar target_group_template_names: Must be represented in the :class:`ServiceTemplate`
    """
    __tablename__ = 'policy_template' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['service_template_fk']

    description = Column(Text)
    type_name = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    target_node_template_names = Column(modeling_types.StrictList(basestring))
    target_group_template_names = Column(modeling_types.StrictList(basestring))

    # region foreign keys

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
            ('type_name', self.type_name),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('target_node_template_names', self.target_node_template_names),
            ('target_group_template_names', self.target_group_template_names)))

    def instantiate(self, context, *args, **kwargs):
        from . import models
        policy = models.Policy(name=self.name,
                               type_name=self.type_name,
                               policy_template=self)
        utils.instantiate_dict(context, self, policy.properties, self.properties)
        if self.target_node_template_names:
            policy.target_node_ids = []
            for node_template_name in self.target_node_template_names:
                policy.target_node_ids += \
                    context.modeling.instance.get_node_ids(node_template_name)
        if self.target_group_template_names:
            policy.target_group_ids = []
            for group_template_name in self.target_group_template_names:
                policy.target_group_ids += \
                    context.modeling.instance.get_group_ids(group_template_name)
        return policy

    def validate(self, context):
        if context.modeling.policy_types.get_descendant(self.type_name) is None:
            context.validation.report('policy template "{0}" has an unknown type: {1}'.format(
                self.name, formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)

    def dump(self, context):
        console.puts('Policy template: {0}'.format(context.style.node(self.name)))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type_name)))
            utils.dump_parameters(context, self.properties)
            if self.target_node_template_names:
                console.puts('Target node templates: {0}'.format(', '.join(
                    (str(context.style.node(v)) for v in self.target_node_template_names))))
            if self.target_group_template_names:
                console.puts('Target group templates: {0}'.format(', '.join(
                    (str(context.style.node(v)) for v in self.target_group_template_names))))


class SubstitutionTemplateBase(_TemplateModelMixin):
    """
    Used to substitute a single node for the entire deployment.

    :ivar node_type_name: Must be represented in the :class:`ModelingContext`
    :ivar mappings: Dict of :class:` SubstitutionTemplateMapping`
    """

    __tablename__ = 'substitution_template' # redundancy for PyLint: SqlAlchemy injects this

    node_type_name = Column(Text)

    @declared_attr
    def mappings(cls):
        return cls.one_to_many_relationship('substitution_template_mapping', key_column_name='name')

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('node_type_name', self.node_type_name),
            ('mappings', formatting.as_raw_dict(self.mappings))))

    def instantiate(self, context, container):
        from . import models
        substitution = models.Substitution(node_type_name=self.node_type_name,
                                           substitution_template=self)
        utils.instantiate_dict(context, container, substitution.mappings, self.mappings)
        return substitution

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.node_type_name) is None:
            context.validation.report('substitution template has an unknown type: {0}'.format(
                formatting.safe_repr(self.node_type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.mappings)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.mappings, report_issues)

    def dump(self, context):
        console.puts('Substitution template:')
        with context.style.indent:
            console.puts('Node type: {0}'.format(context.style.type(self.node_type_name)))
            utils.dump_dict_values(context, self.mappings, 'Mappings')


class SubstitutionTemplateMappingBase(_TemplateModelMixin):
    """
    Used by :class:`SubstitutionTemplate` to map a capability or a requirement to a node.

    :ivar name: Exposed capability or requirement name
    """

    __tablename__ = 'substitution_template_mapping' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['substitution_template_fk',
                          'node_template_fk',
                          'capability_template_fk',
                          'requirement_template_fk']

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


class RequirementTemplateBase(_TemplateModelMixin):
    """
    A requirement for a :class:`NodeTemplate`. During instantiation will be matched with a
    capability of another
    node.

    Requirements may optionally contain a :class:`RelationshipTemplate` that will be created between
    the nodes.

    :ivar name: Name
    :ivar target_node_type_name: Must be represented in the :class:`ModelingContext`
    :ivar target_node_template_name: Must be represented in the :class:`ServiceTemplate`
    :ivar target_node_template_constraints: List of :class:`FunctionType`
    :ivar target_capability_type_name: Type of capability in target node
    :ivar target_capability_name: Name of capability in target node
    :ivar relationship_template: :class:`RelationshipTemplate`
    """

    __tablename__ = 'requirement_template' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['node_template_fk',
                          'relationship_template_fk']

    target_node_type_name = Column(Text)
    target_node_template_name = Column(Text)
    target_node_template_constraints = Column(modeling_types.StrictList(FunctionType))
    target_capability_type_name = Column(Text)
    target_capability_name = Column(Text)

    @declared_attr
    def relationship_template(cls):
        return cls.one_to_one_relationship('relationship_template')

    # region foreign keys

    # NodeTemplate one-to-many to RequirementTemplate
    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template', nullable=True)

    # RequirementTemplate one-to-one to RelationshipTemplate
    @declared_attr
    def relationship_template_fk(cls):
        return cls.foreign_key('relationship_template', nullable=True)

    # endregion

    def instantiate(self, context, container):
        raise NotImplementedError

    def find_target(self, context, source_node_template):
        # We might already have a specific node template, so we'll just verify it
        if self.target_node_template_name is not None:
            target_node_template = \
                context.modeling.template.get_node_template(self.target_node_template_name)

            if not source_node_template.is_target_node_valid(target_node_template):
                context.validation.report('requirement "{0}" of node template "{1}" is for node '
                                          'template "{2}" but it does not match constraints'.format(
                                              self.name,
                                              self.target_node_template_name,
                                              source_node_template.name),
                                          level=validation.Issue.BETWEEN_TYPES)
                return None, None

            if (self.target_capability_type_name is not None) \
                or (self.target_capability_name is not None):
                target_node_capability = self.find_target_capability(context,
                                                                     source_node_template,
                                                                     target_node_template)
                if target_node_capability is None:
                    return None, None
            else:
                target_node_capability = None

            return target_node_template, target_node_capability

        # Find first node that matches the type
        elif self.target_node_type_name is not None:
            for target_node_template in context.modeling.template.node_templates:
                if not context.modeling.node_types.is_descendant(self.target_node_type_name,
                                                                 target_node_template.type_name):
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
            ('target_node_type_name', self.target_node_type_name),
            ('target_node_template_name', self.target_node_template_name),
            ('target_capability_type_name', self.target_capability_type_name),
            ('target_capability_name', self.target_capability_name),
            ('relationship_template', formatting.as_raw(self.relationship_template))))

    def validate(self, context):
        node_types = context.modeling.node_types
        capability_types = context.modeling.capability_types
        if self.target_node_type_name \
                and node_types.get_descendant(self.target_node_type_name) is None:
            context.validation.report('requirement "{0}" refers to an unknown node type: {1}' \
                                        .format(
                                            self.name,
                                            formatting.safe_repr(self.target_node_type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)
        if self.target_capability_type_name and \
                capability_types.get_descendant(self.target_capability_type_name is None):
            context.validation.report('requirement "{0}" refers to an unknown capability type: '
                                      '{1}'.format(
                                          self.name,
                                          formatting.safe_repr(self.target_capability_type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)
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
            if self.target_node_type_name is not None:
                console.puts('Target node type: {0}'.format(
                    context.style.type(self.target_node_type_name)))
            elif self.target_node_template_name is not None:
                console.puts('Target node template: {0}'.format(
                    context.style.node(self.target_node_template_name)))
            if self.target_capability_type_name is not None:
                console.puts('Target capability type: {0}'.format(
                    context.style.type(self.target_capability_type_name)))
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


class RelationshipTemplateBase(_TemplateModelMixin):
    """
    Optional addition to a :class:`RequirementTemplate` in :class:`NodeTemplate` that can be applied
    when the requirement is matched with a capability.

    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar template_name: Must be represented in the :class:`ServiceTemplate`
    :ivar description: Description
    :ivar properties: Dict of :class:`Parameter`
    :ivar interface_templates: Dict of :class:`InterfaceTemplate`
    """

    __tablename__ = 'relationship_template' # redundancy for PyLint: SqlAlchemy injects this

    type_name = Column(Text)
    template_name = Column(Text)
    description = Column(Text)

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    @declared_attr
    def interface_templates(cls):
        return cls.one_to_many_relationship('interface_template', key_column_name='name')

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('description', self.description),
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates))))

    def instantiate(self, context, container):
        from . import models
        relationship = models.Relationship(name=self.template_name,
                                           type_name=self.type_name,
                                           relationship_template=self)
        utils.instantiate_dict(context, container,
                               relationship.properties, self.properties)
        utils.instantiate_dict(context, container,
                               relationship.interfaces, self.interface_templates)
        return relationship

    def validate(self, context):
        if context.modeling.relationship_types.get_descendant(self.type_name) is None:
            context.validation.report(
                'relationship template "{0}" has an unknown type: {1}'.format(
                    self.name,
                    formatting.safe_repr(self.type_name)),  # pylint: disable=no-member
                # TODO fix self.name reference
                level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interface_templates)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)
        utils.coerce_dict_values(context, self, self.interface_templates, report_issues)

    def dump(self, context):
        if self.type_name is not None:
            console.puts('Relationship type: {0}'.format(context.style.type(self.type_name)))
        else:
            console.puts('Relationship template: {0}'.format(
                context.style.node(self.template_name)))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            utils.dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interface_templates, 'Interface templates')


class CapabilityTemplateBase(_TemplateModelMixin):
    """
    A capability of a :class:`NodeTemplate`. Nodes expose zero or more capabilities that can be
    matched with :class:`Requirement` instances of other nodes.

    :ivar name: Name
    :ivar description: Description
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar min_occurrences: Minimum number of requirement matches required
    :ivar max_occurrences: Maximum number of requirement matches allowed
    :ivar valid_source_node_type_names: Must be represented in the :class:`ModelingContext`
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'capability_template' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['node_template_fk']

    description = Column(Text)
    type_name = Column(Text)
    min_occurrences = Column(Integer, default=None)  # optional
    max_occurrences = Column(Integer, default=None)  # optional
    valid_source_node_type_names = Column(modeling_types.StrictList(basestring))

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    # region foreign keys

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
        capability_types = context.modeling.capability_types
        if not capability_types.is_descendant(requirement.target_capability_type_name,
                                              self.type_name):
            return False

        # Are we in valid_source_node_type_names?
        if self.valid_source_node_type_names:
            for valid_source_node_type_name in self.valid_source_node_type_names:
                if not context.modeling.node_types.is_descendant(valid_source_node_type_name,
                                                                 source_node_template.type_name):
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
            ('type_name', self.type_name),
            ('min_occurrences', self.min_occurrences),
            ('max_occurrences', self.max_occurrences),
            ('valid_source_node_type_names', self.valid_source_node_type_names),
            ('properties', formatting.as_raw_dict(self.properties))))

    def instantiate(self, context, container):
        from . import models
        capability = models.Capability(name=self.name,
                                       type_name=self.type_name,
                                       min_occurrences=self.min_occurrences,
                                       max_occurrences=self.max_occurrences,
                                       occurrences=0,
                                       capability_template=self)
        utils.instantiate_dict(context, container, capability.properties, self.properties)
        return capability

    def validate(self, context):
        if context.modeling.capability_types.get_descendant(self.type_name) is None:
            context.validation.report('capability "{0}" refers to an unknown type: {1}'.format(
                self.name, formatting.safe_repr(self.type)),  # pylint: disable=no-member
                                      #  TODO fix self.type reference
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)

    def dump(self, context):
        console.puts(context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Type: {0}'.format(context.style.type(self.type_name)))
            console.puts(
                'Occurrences: {0:d}{1}'.format(
                    self.min_occurrences or 0,
                    ' to {0:d}'.format(self.max_occurrences)
                    if self.max_occurrences is not None
                    else ' or more'))
            if self.valid_source_node_type_names:
                console.puts('Valid source node types: {0}'.format(
                    ', '.join((str(context.style.type(v))
                               for v in self.valid_source_node_type_names))))
            utils.dump_parameters(context, self.properties)


class InterfaceTemplateBase(_TemplateModelMixin):
    """
    A typed set of :class:`OperationTemplate`.

    :ivar name: Name
    :ivar description: Description
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar inputs: Dict of :class:`Parameter`
    :ivar operation_templates: Dict of :class:`OperationTemplate`
    """

    __tablename__ = 'interface_template' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['node_template_fk',
                          'group_template_fk',
                          'relationship_template_fk']

    description = Column(Text)
    type_name = Column(Text)

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs',
                                             key_column_name='name')
    @declared_attr
    def operation_templates(cls):
        return cls.one_to_many_relationship('operation_template', key_column_name='name')

    # region foreign keys

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
            ('type_name', self.type_name),
            ('inputs', formatting.as_raw_dict(self.inputs)),  # pylint: disable=no-member
            # TODO fix self.properties reference
            ('operation_templates', formatting.as_raw_list(self.operation_templates))))

    def instantiate(self, context, container):
        from . import models
        interface = models.Interface(name=self.name,
                                     description=deepcopy_with_locators(self.description),
                                     type_name=self.type_name,
                                     interface_template=self)
        utils.instantiate_dict(context, container, interface.inputs, self.inputs)
        utils.instantiate_dict(context, container, interface.operations, self.operation_templates)
        return interface

    def validate(self, context):
        if self.type_name:
            if context.modeling.interface_types.get_descendant(self.type_name) is None:
                context.validation.report('interface "{0}" has an unknown type: {1}'.format(
                    self.name, formatting.safe_repr(self.type_name)),
                                          level=validation.Issue.BETWEEN_TYPES)

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
            console.puts('Interface type: {0}'.format(context.style.type(self.type_name)))
            utils.dump_parameters(context, self.inputs, 'Inputs')
            utils.dump_dict_values(context, self.operation_templates, 'Operation templates')


class OperationTemplateBase(_TemplateModelMixin):
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

    __tablename__ = 'operation_template' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['service_template_fk',
                          'interface_template_fk',
                          'plugin_fk']

    description = Column(Text)
    implementation = Column(Text)
    dependencies = Column(modeling_types.StrictList(item_cls=basestring))
    executor = Column(Text)
    max_retries = Column(Integer)
    retry_interval = Column(Integer)

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs',
                                             key_column_name='name')

    @declared_attr
    def plugin(cls):
        return cls.one_to_one_relationship('plugin')

    executor = Column(Text)
    max_retries = Column(Integer)
    retry_interval = Column(Integer)

    # region foreign keys

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
            utils.dump_parameters(context, self.inputs, 'Inputs')


class ArtifactTemplateBase(_TemplateModelMixin):
    """
    A file associated with a :class:`NodeTemplate`.

    :ivar name: Name
    :ivar description: Description
    :ivar type_name: Must be represented in the :class:`ModelingContext`
    :ivar source_path: Source path (CSAR or repository)
    :ivar target_path: Path at destination machine
    :ivar repository_url: Repository URL
    :ivar repository_credential: Dict of string
    :ivar properties: Dict of :class:`Parameter`
    """

    __tablename__ = 'artifact_template' # redundancy for PyLint: SqlAlchemy injects this

    __private_fields__ = ['node_template_fk']

    description = Column(Text)
    type_name = Column(Text)
    source_path = Column(Text)
    target_path = Column(Text)
    repository_url = Column(Text)
    repository_credential = Column(modeling_types.StrictDict(basestring, basestring))

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties',
                                             key_column_name='name')

    # region foreign keys

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
            ('type_name', self.type_name),
            ('source_path', self.source_path),
            ('target_path', self.target_path),
            ('repository_url', self.repository_url),
            ('repository_credential', formatting.as_agnostic(self.repository_credential)),
            ('properties', formatting.as_raw_dict(self.properties))))

    def instantiate(self, context, container):
        from . import models
        artifact = models.Artifact(name=self.name,
                                   type_name=self.type_name,
                                   source_path=self.source_path,
                                   description=deepcopy_with_locators(self.description),
                                   target_path=self.target_path,
                                   repository_url=self.repository_url,
                                   repository_credential=self.repository_credential,
                                   artifact_template=self)
        utils.instantiate_dict(context, container, artifact.properties, self.properties)
        return artifact

    def validate(self, context):
        if context.modeling.artifact_types.get_descendant(self.type_name) is None:
            context.validation.report('artifact "{0}" has an unknown type: {1}'.format(
                self.name, formatting.safe_repr(self.type_name)),
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



class ParameterBase(_TemplateModelMixin):
    """
    Represents a typed value.

    This class is used by both service template and service instance elements.

    :ivar name: Name
    :ivar type_name: Type name
    :ivar value: Value
    :ivar description: Description
    """

    __tablename__ = 'parameter' # redundancy for PyLint: SqlAlchemy injects this

    name = Column(Text, nullable=False)
    type_name = Column(Text, nullable=False)

    # Check: value type
    str_value = Column(Text)
    description = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('value', self.value),
            ('description', self.description)))

    @property
    def value(self):
        if self.str_value is None:
            return None
        if self.type_name is None:
            return self.str_value
        try:
            type_name = self.type_name.lower()
            if type_name in ('str', 'unicode'):
                return self.str_value.decode('utf-8')
            elif type_name == 'int':
                return int(self.str_value)
            elif type_name == 'bool':
                return bool(self.str_value)
            elif type_name == 'float':
                return float(self.str_value)
            else:
                return self.str_value
        except ValueError:
            raise exceptions.StorageError('Trying to cast {0} to {1} failed'.format(self.str_value,
                                                                                    self.type))

    @value.setter
    def value(self, value):
        self.str_value = unicode(value)

    def instantiate(self, context, container):
        from . import models
        return models.Parameter(name=self.name,
                                type_name=self.type_name,
                                str_value=self.str_value,
                                description=self.description)

    def coerce_values(self, context, container, report_issues):
        if self.str_value is not None:
            self.str_value = parser_utils.coerce_value(context, container, self.str_value,
                                                       report_issues)


class MetadataBase(_TemplateModelMixin):
    """
    Custom values associated with the service.

    This class is used by both service template and service instance elements.

    :ivar name: Name
    :ivar value: Value
    """

    __tablename__ = 'metadata' # redundancy for PyLint: SqlAlchemy injects this

    name = Column(Text, nullable=False)
    value = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('value', self.value)))

    def instantiate(self, context, container):
        from . import models
        return models.Metadata(name=self.name,
                               value=self.value)


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
