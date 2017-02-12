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
from copy import deepcopy
from types import FunctionType

from sqlalchemy import (
    Column,
    Text,
    Integer,
    DateTime,
    Boolean,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

from aria.parser import validation
from aria.utils import collections, formatting, console

from . import (
    utils,
    instance_elements,
    structure,
    type as aria_type
)

# pylint: disable=no-self-argument, no-member, abstract-method


# region Element templates


class ServiceTemplateBase(structure.ModelMixin):

    __tablename__ = 'service_template'

    __private_fields__ = ['substitution_template_fk']

    description = Column(Text)
    metadata = Column(Text)

    # region orchestrator required columns

    created_at = Column(DateTime, nullable=False, index=True)
    main_file_name = Column(Text)
    plan = Column(aria_type.Dict, nullable=False)
    updated_at = Column(DateTime)

    # endregion

    # region foreign keys
    @declared_attr
    def substitution_template_fk(cls):
        return cls.foreign_key('substitution_template', nullable=True)

    # endregion

    # region one-to-one relationships
    @declared_attr
    def substitution_template(cls):
        return cls.one_to_one_relationship('substitution_template')
    # endregion

    # region many-to-many relationships

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs')

    @declared_attr
    def outputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='outputs')

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('description', self.description),
            ('metadata', formatting.as_raw(self.metadata)),
            ('node_templates', formatting.as_raw_list(self.node_templates)),
            ('group_templates', formatting.as_raw_list(self.group_templates)),
            ('policy_templates', formatting.as_raw_list(self.policy_templates)),
            ('substitution_template', formatting.as_raw(self.substitution_template)),
            ('inputs', formatting.as_raw_dict(self.inputs)),
            ('outputs', formatting.as_raw_dict(self.outputs)),
            ('operation_templates', formatting.as_raw_list(self.operation_templates))))

    def instantiate(self, context, container):
        service_instance = instance_elements.ServiceInstanceBase()
        context.modeling.instance = service_instance

        service_instance.description = deepcopy_with_locators(self.description)

        if self.metadata is not None:
            service_instance.metadata = self.metadata.instantiate(context, container)

        for node_template in self.node_templates.itervalues():
            for _ in range(node_template.default_instances):
                node = node_template.instantiate(context, container)
                service_instance.nodes[node.id] = node

        utils.instantiate_dict(context, self, service_instance.groups, self.group_templates)
        utils.instantiate_dict(context, self, service_instance.policies, self.policy_templates)
        utils.instantiate_dict(context, self, service_instance.operations, self.operation_templates)

        if self.substitution_template is not None:
            service_instance.substitution = self.substitution_template.instantiate(context,
                                                                                   container)

        utils.instantiate_dict(context, self, service_instance.inputs, self.inputs)
        utils.instantiate_dict(context, self, service_instance.outputs, self.outputs)

        for name, the_input in context.modeling.inputs.iteritems():
            if name not in service_instance.inputs:
                context.validation.report('input "%s" is not supported' % name)
            else:
                service_instance.inputs[name].value = the_input

        return service_instance

    def validate(self, context):
        if self.metadata is not None:
            self.metadata.validate(context)
        utils.validate_dict_values(context, self.node_templates)
        utils.validate_dict_values(context, self.group_templates)
        utils.validate_dict_values(context, self.policy_templates)
        if self.substitution_template is not None:
            self.substitution_template.validate(context)
        utils.validate_dict_values(context, self.inputs)
        utils.validate_dict_values(context, self.outputs)
        utils.validate_dict_values(context, self.operation_templates)

    def coerce_values(self, context, container, report_issues):
        if self.metadata is not None:
            self.metadata.coerce_values(context, container, report_issues)
        utils.coerce_dict_values(context, container, self.node_templates, report_issues)
        utils.coerce_dict_values(context, container, self.group_templates, report_issues)
        utils.coerce_dict_values(context, container, self.policy_templates, report_issues)
        if self.substitution_template is not None:
            self.substitution_template.coerce_values(context, container, report_issues)
        utils.coerce_dict_values(context, container, self.inputs, report_issues)
        utils.coerce_dict_values(context, container, self.outputs, report_issues)
        utils.coerce_dict_values(context, container, self.operation_templates, report_issues)

    def dump(self, context):
        if self.description is not None:
            console.puts(context.style.meta(self.description))
        if self.metadata is not None:
            self.metadata.dump(context)
        for node_template in self.node_templates.itervalues():
            node_template.dump(context)
        for group_template in self.group_templates.itervalues():
            group_template.dump(context)
        for policy_template in self.policy_templates.itervalues():
            policy_template.dump(context)
        if self.substitution_template is not None:
            self.substitution_template.dump(context)
        dump_parameters(context, self.inputs, 'Inputs')
        dump_parameters(context, self.outputs, 'Outputs')
        utils.dump_dict_values(context, self.operation_templates, 'Operation templates')


class InterfaceTemplateBase(structure.ModelMixin):
    __tablename__ = 'interface_template'

    __private_fields__ = ['node_template_fk',
                          'group_template_fk']

    # region foreign keys

    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template', nullable=True)

    @declared_attr
    def group_template_fk(cls):
        return cls.foreign_key('group_template', nullable=True)

    # endregion

    description = Column(Text)
    type_name = Column(Text)

    # region many-to-one relationship
    @declared_attr
    def node_template(cls):
        return cls.many_to_one_relationship('node_template')

    @declared_attr
    def group_template(cls):
        return cls.many_to_one_relationship('group_template')

    # endregion

    # region many-to-many relationships

    @declared_attr
    def inputs(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='inputs')

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
            ('inputs', formatting.as_raw_dict(self.properties)),  # pylint: disable=no-member
            # TODO fix self.properties reference
            ('operation_templates', formatting.as_raw_list(self.operation_templates))))

    def instantiate(self, context, container):
        interface = instance_elements.InterfaceBase(self.name, self.type_name)
        interface.description = deepcopy_with_locators(self.description)
        utils.instantiate_dict(context, container, interface.inputs, self.inputs)
        utils.instantiate_dict(context, container, interface.operations, self.operation_templates)
        return interface

    def validate(self, context):
        if self.type_name:
            if context.modeling.interface_types.get_descendant(self.type_name) is None:
                context.validation.report('interface "%s" has an unknown type: %s'
                                          % (self.name, formatting.safe_repr(self.type_name)),
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
            console.puts('Interface type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.inputs, 'Inputs')
            utils.dump_dict_values(context, self.operation_templates, 'Operation templates')


class OperationTemplateBase(structure.ModelMixin):
    __tablename__ = 'operation_template'

    __private_fields__ = ['service_template_fk',
                          'interface_template_fk']

    # region foreign keys

    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template', nullable=True)

    @declared_attr
    def interface_template_fk(cls):
        return cls.foreign_key('interface_template', nullable=True)

    # endregion

    description = Column(Text)
    implementation = Column(Text)
    dependencies = Column(aria_type.StrictList(item_cls=basestring))
    executor = Column(Text)
    max_retries = Column(Integer)
    retry_interval = Column(Integer)

    # region orchestrator required columns
    plugin = Column(Text)
    operation = Column(Boolean)

    # region many-to-one relationships
    @declared_attr
    def service_template(cls):
        return cls.many_to_one_relationship('service_template')

    @declared_attr
    def interface_template(cls):
        return cls.many_to_one_relationship('interface_template')
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
            ('implementation', self.implementation),
            ('dependencies', self.dependencies),
            ('executor', self.executor),
            ('max_retries', self.max_retries),
            ('retry_interval', self.retry_interval),
            ('inputs', formatting.as_raw_dict(self.inputs))))

    def instantiate(self, context, container):
        operation = instance_elements.OperationBase(self.name)
        operation.description = deepcopy_with_locators(self.description)
        operation.implementation = self.implementation
        operation.dependencies = self.dependencies
        operation.executor = self.executor
        operation.max_retries = self.max_retries
        operation.retry_interval = self.retry_interval
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
                console.puts('Implementation: %s' % context.style.literal(self.implementation))
            if self.dependencies:
                console.puts('Dependencies: %s' % ', '.join(
                    (str(context.style.literal(v)) for v in self.dependencies)))
            if self.executor is not None:
                console.puts('Executor: %s' % context.style.literal(self.executor))
            if self.max_retries is not None:
                console.puts('Max retries: %s' % context.style.literal(self.max_retries))
            if self.retry_interval is not None:
                console.puts('Retry interval: %s' % context.style.literal(self.retry_interval))
            dump_parameters(context, self.inputs, 'Inputs')


class ArtifactTemplateBase(structure.ModelMixin):
    """
    A file associated with a :class:`NodeTemplate`.

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
    __tablename__ = 'artifact_template'

    __private_fields__ = ['node_template_fk']

    # region foreign keys

    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template')

    # endregion

    description = Column(Text)
    type_name = Column(Text)
    source_path = Column(Text)
    target_path = Column(Text)
    repository_url = Column(Text)
    repository_credential = Column(aria_type.StrictDict(basestring, basestring))

    # region many-to-one relationship
    @declared_attr
    def node_template(cls):
        return cls.many_to_one_relationship('node_template')
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
            ('properties', formatting.as_raw_dict(self.properties.iteritems()))))

    def instantiate(self, context, container):
        artifact = instance_elements.ArtifactBase(self.name, self.type_name, self.source_path)
        artifact.description = deepcopy_with_locators(self.description)
        artifact.target_path = self.target_path
        artifact.repository_url = self.repository_url
        artifact.repository_credential = self.repository_credential
        utils.instantiate_dict(context, container, artifact.properties, self.properties)
        return artifact

    def validate(self, context):
        if context.modeling.artifact_types.get_descendant(self.type_name) is None:
            context.validation.report('artifact "%s" has an unknown type: %s'
                                      % (self.name, formatting.safe_repr(self.type_name)),
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
            dump_parameters(context, self.properties)


class PolicyTemplateBase(structure.ModelMixin):
    """
    Policies can be applied to zero or more :class:`NodeTemplate` or :class:`GroupTemplate`
    instances.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`target_node_template_names`: Must be represented in the :class:`ServiceModel`
    * :code:`target_group_template_names`: Must be represented in the :class:`ServiceModel`
    """
    __tablename__ = 'policy_template'

    __private_fields__ = ['service_templaet_fk',
                          'group_template_fk']

    # region foreign keys

    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template')

    @declared_attr
    def group_template_fk(cls):
        return cls.foreign_key('group_template')

    # endregion

    description = Column(Text)
    type_name = Column(Text)
    target_node_template_names = Column(aria_type.StrictList(basestring))
    target_group_template_names = Column(aria_type.StrictList(basestring))

    # region many-to-one relationship
    @declared_attr
    def service_template(cls):
        return cls.many_to_one_relationship('service_template')

    @declared_attr
    def group_template(cls):
        return cls.many_to_one_relationship('group_template')

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
            ('properties', formatting.as_raw_dict(self.properties)),
            ('target_node_template_names', self.target_node_template_names),
            ('target_group_template_names', self.target_group_template_names)))

    def instantiate(self, context, *args, **kwargs):
        policy = instance_elements.PolicyBase(self.name, self.type_name)
        utils.instantiate_dict(context, self, policy.properties, self.properties)
        for node_template_name in self.target_node_template_names:
            policy.target_node_ids.extend(
                context.modeling.instance.get_node_ids(node_template_name))
        for group_template_name in self.target_group_template_names:
            policy.target_group_ids.extend(
                context.modeling.instance.get_group_ids(group_template_name))
        return policy

    def validate(self, context):
        if context.modeling.policy_types.get_descendant(self.type_name) is None:
            context.validation.report('policy template "%s" has an unknown type: %s'
                                      % (self.name, formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)

    def dump(self, context):
        console.puts('Policy template: %s' % context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.properties)
            if self.target_node_template_names:
                console.puts('Target node templates: %s' % ', '.join(
                    (str(context.style.node(v)) for v in self.target_node_template_names)))
            if self.target_group_template_names:
                console.puts('Target group templates: %s' % ', '.join(
                    (str(context.style.node(v)) for v in self.target_group_template_names)))


class GroupPolicyTemplateBase(structure.ModelMixin):
    """
    Policies applied to groups.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`triggers`: Dict of :class:`GroupPolicyTrigger`
    """

    __tablename__ = 'group_policy_template'

    __private_fields__ = ['group_template_fk']

    # region foreign keys
    @declared_attr
    def group_template_fk(cls):
        return cls.foreign_key('group_template')

    # endregion

    description = Column(Text)
    type_name = Column(Text)

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

    def instantiate(self, context, container):
        group_policy = instance_elements.GroupPolicyBase(self.name, self.type_name)
        group_policy.description = deepcopy_with_locators(self.description)
        utils.instantiate_dict(context, container, group_policy.properties, self.properties)
        utils.instantiate_dict(context, container, group_policy.triggers, self.triggers)
        return group_policy

    def validate(self, context):
        if context.modeling.policy_types.get_descendant(self.type_name) is None:
            context.validation.report('group policy "%s" has an unknown type: %s'
                                      % (self.name, formatting.safe_repr(self.type_name)),
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
            dump_parameters(context, self.properties)
            utils.dump_dict_values(context, self.triggers, 'Triggers')


class GroupPolicyTriggerTemplateBase(structure.ModelMixin):
    """
    Triggers for :class:`GroupPolicyTemplate`.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`implementation`: Implementation string (interpreted by the orchestrator)
    * :code:`properties`: Dict of :class:`Parameter`
    """
    __tablename__ = 'group_policy_trigger_template'

    __private_fields__ = ['group_policy_template_fk']

    # region foreign keys

    @declared_attr
    def group_policy_template_fk(cls):
        return cls.foreign_key('group_policy_template')

    # endregion

    description = Column(Text)
    implementation = Column(Text)

    # region many-to-one relationship
    @declared_attr
    def group_policy_template(cls):
        return cls.many_to_one_relationship('group_policy_template')

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

    def instantiate(self, context, container):
        group_policy_trigger = instance_elements.GroupPolicyTriggerBase(self.name,
                                                                        self.implementation)
        group_policy_trigger.description = deepcopy_with_locators(self.description)
        utils.instantiate_dict(context, container, group_policy_trigger.properties,
                               self.properties)
        return group_policy_trigger

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
            dump_parameters(context, self.properties)


class MappingTemplateBase(structure.ModelMixin):
    """
    Used by :class:`SubstitutionTemplate` to map a capability or a requirement to a node.

    Properties:

    * :code:`mapped_name`: Exposed capability or requirement name
    * :code:`node_template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`name`: Name of capability or requirement at the node template
    """
    __tablename__ = 'mapping_template'

    mapped_name = Column(Text)
    node_template_name = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('mapped_name', self.mapped_name),
            ('node_template_name', self.node_template_name),
            ('name', self.name)))

    def instantiate(self, context, *args, **kwargs):
        nodes = context.modeling.instance.find_nodes(self.node_template_name)
        if len(nodes) == 0:
            context.validation.report(
                'mapping "%s" refer to node template "%s" but there are no '
                'node instances' % (self.mapped_name,
                                    self.node_template_name),
                level=validation.Issue.BETWEEN_INSTANCES)
            return None
        return instance_elements.MappingBase(self.mapped_name, nodes[0].id, self.name)

    def validate(self, context):
        if self.node_template_name not in context.modeling.model.node_templates:
            context.validation.report('mapping "%s" refers to an unknown node template: %s'
                                      % (
                                          self.mapped_name,
                                          formatting.safe_repr(self.node_template_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

    def dump(self, context):
        console.puts('%s -> %s.%s' % (context.style.node(self.mapped_name),
                                      context.style.node(self.node_template_name),
                                      context.style.node(self.name)))


class SubstitutionTemplateBase(structure.ModelMixin):
    """
    Used to substitute a single node for the entire deployment.

    Properties:

    * :code:`node_type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`capability_templates`: Dict of :class:`MappingTemplate`
    * :code:`requirement_templates`: Dict of :class:`MappingTemplate`
    """
    __tablename__ = 'substitution_template'
    node_type_name = Column(Text)

    # region many-to-many relationships

    @declared_attr
    def capability_templates(cls):
        return cls.many_to_many_relationship('mapping_template',
                                             table_prefix='capability_templates',
                                             relationship_kwargs=dict(lazy='dynamic'))

    @declared_attr
    def requirement_templates(cls):
        return cls.many_to_many_relationship('mapping_template',
                                             table_prefix='requirement_templates',
                                             relationship_kwargs=dict(lazy='dynamic'))

    # endregion

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('node_type_name', self.node_type_name),
            ('capability_templates', formatting.as_raw_list(self.capability_templates)),
            ('requirement_templates', formatting.as_raw_list(self.requirement_templates))))

    def instantiate(self, context, container):
        substitution = instance_elements.SubstitutionBase(self.node_type_name)
        utils.instantiate_dict(context, container, substitution.capabilities,
                               self.capability_templates)
        utils.instantiate_dict(context, container, substitution.requirements,
                               self.requirement_templates)
        return substitution

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.node_type_name) is None:
            context.validation.report('substitution template has an unknown type: %s'
                                      % formatting.safe_repr(self.node_type_name),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.capability_templates)
        utils.validate_dict_values(context, self.requirement_templates)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.capability_templates, report_issues)
        utils.coerce_dict_values(context, self, self.requirement_templates, report_issues)

    def dump(self, context):
        console.puts('Substitution template:')
        with context.style.indent:
            console.puts('Node type: %s' % context.style.type(self.node_type_name))
            utils.dump_dict_values(context, self.capability_templates,
                                   'Capability template mappings')
            utils.dump_dict_values(context, self.requirement_templates,
                                   'Requirement template mappings')


# endregion

# region Node templates

class NodeTemplateBase(structure.ModelMixin):
    __tablename__ = 'node_template'

    __private_fields__ = ['service_template_fk',
                          'host_fk']

    # region foreign_keys

    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template')

    @declared_attr
    def host_fk(cls):
        return cls.foreign_key('node_template', nullable=True)

    # endregion

    description = Column(Text)
    type_name = Column(Text)
    default_instances = Column(Integer, default=1)
    min_instances = Column(Integer, default=0)
    max_instances = Column(Integer, default=None)
    target_node_template_constraints = Column(aria_type.StrictList(FunctionType))

    # region orchestrator required columns

    plugins = Column(aria_type.List)
    type_hierarchy = Column(aria_type.List)

    @declared_attr
    def host(cls):
        return cls.relationship_to_self('host_fk')

    @declared_attr
    def service_template_name(cls):
        return association_proxy('service_template', cls.name_column_name())

    # endregion

    # region many-to-one relationship
    @declared_attr
    def service_template(cls):
        return cls.many_to_one_relationship('service_template')

    # endregion

    # region many-to-many relationships

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

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
        node = instance_elements.NodeBase(context, self.type_name, self.name)
        utils.instantiate_dict(context, node, node.properties, self.properties)
        utils.instantiate_dict(context, node, node.interfaces, self.interface_templates)
        utils.instantiate_dict(context, node, node.artifacts, self.artifact_templates)
        utils.instantiate_dict(context, node, node.capabilities, self.capability_templates)
        return node

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.type_name) is None:
            context.validation.report('node template "%s" has an unknown type: %s'
                                      % (self.name,
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
        console.puts('Node template: %s' % context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            console.puts('Type: %s' % context.style.type(self.type_name))
            console.puts('Instances: %d (%d%s)'
                         % (self.default_instances,
                            self.min_instances,
                            (' to %d' % self.max_instances
                             if self.max_instances is not None
                             else ' or more')))
            dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interface_templates)
            utils.dump_dict_values(context, self.artifact_templates, 'Artifact tempaltes')
            utils.dump_dict_values(context, self.capability_templates, 'Capability templates')
            utils.dump_list_values(context, self.requirement_templates, 'Requirement templates')


class GroupTemplateBase(structure.ModelMixin):
    """
    A template for creating zero or more :class:`Group` instances.

    Groups are logical containers for zero or more nodes that allow applying zero or more
    :class:`GroupPolicy` instances to the nodes together.

    Properties:

    * :code:`name`: Name (will be used as a prefix for group IDs)
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`interface_templates`: Dict of :class:`InterfaceTemplate`
    * :code:`policy_templates`: Dict of :class:`GroupPolicyTemplate`
    * :code:`member_node_template_names`: Must be represented in the :class:`ServiceModel`
    * :code:`member_group_template_names`: Must be represented in the :class:`ServiceModel`
    """
    __tablename__ = 'group_template'

    __private_fields__ = ['service_template_fk']

    # region foreign keys

    @declared_attr
    def service_template_fk(cls):
        return cls.foreign_key('service_template')

    # endregion

    description = Column(Text)
    type_name = Column(Text)
    member_node_template_names = Column(aria_type.StrictList(basestring))
    member_group_template_names = Column(aria_type.StrictList(basestring))

    # region many-to-one relationship
    @declared_attr
    def service_template(cls):
        return cls.many_to_one_relationship('service_template')

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
            ('properties', formatting.as_raw_dict(self.properties)),
            ('interface_templates', formatting.as_raw_list(self.interface_templates)),
            ('policy_templates', formatting.as_raw_list(self.policy_templates)),
            ('member_node_template_names', self.member_node_template_names),
            ('member_group_template_names', self.member_group_template_names1)))

    def instantiate(self, context, *args, **kwargs):
        group = instance_elements.GroupBase(context, self.type_name, self.name)
        utils.instantiate_dict(context, self, group.properties, self.properties)
        utils.instantiate_dict(context, self, group.interfaces, self.interface_templates)
        utils.instantiate_dict(context, self, group.policies, self.policy_templates)
        for member_node_template_name in self.member_node_template_names:
            group.member_node_ids += \
                context.modeling.instance.get_node_ids(member_node_template_name)
        for member_group_template_name in self.member_group_template_names:
            group.member_group_ids += \
                context.modeling.instance.get_group_ids(member_group_template_name)
        return group

    def validate(self, context):
        if context.modeling.group_types.get_descendant(self.type_name) is None:
            context.validation.report('group template "%s" has an unknown type: %s'
                                      % (self.name, formatting.safe_repr(self.type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)

        utils.validate_dict_values(context, self.properties)
        utils.validate_dict_values(context, self.interface_templates)
        utils.validate_dict_values(context, self.policy_templates)

    def coerce_values(self, context, container, report_issues):
        utils.coerce_dict_values(context, self, self.properties, report_issues)
        utils.coerce_dict_values(context, self, self.interface_templates, report_issues)
        utils.coerce_dict_values(context, self, self.policy_templates, report_issues)

    def dump(self, context):
        console.puts('Group template: %s' % context.style.node(self.name))
        if self.description:
            console.puts(context.style.meta(self.description))
        with context.style.indent:
            if self.type_name:
                console.puts('Type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.properties)
            utils.dump_interfaces(context, self.interface_templates)
            utils.dump_dict_values(context, self.policy_templates, 'Policy templates')
            if self.member_node_template_names:
                console.puts('Member node templates: %s' % ', '.join(
                    (str(context.style.node(v)) for v in self.member_node_template_names)))


# endregion

# region Relationship templates

class RequirementTemplateBase(structure.ModelMixin):
    """
    A requirement for a :class:`NodeTemplate`. During instantiation will be matched with a
    capability of another
    node.

    Requirements may optionally contain a :class:`RelationshipTemplate` that will be created between
    the nodes.

    Properties:

    * :code:`name`: Name
    * :code:`target_node_type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`target_node_template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`target_node_template_constraints`: List of :class:`FunctionType`
    * :code:`target_capability_type_name`: Type of capability in target node
    * :code:`target_capability_name`: Name of capability in target node
    * :code:`relationship_template`: :class:`RelationshipTemplate`
    """
    __tablename__ = 'requirement_template'

    __private_fields__ = ['node_template_fk']

    # region foreign keys

    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template', nullable=True)

    # endregion


    target_node_type_name = Column(Text)
    target_node_template_name = Column(Text)
    target_node_template_constraints = Column(aria_type.StrictList(FunctionType))
    target_capability_type_name = Column(Text)
    target_capability_name = Column(Text)
    # CHECK: ???
    relationship_template = Column(Text)  # optional

    # region many-to-one relationship
    @declared_attr
    def node_template(cls):
        return cls.many_to_one_relationship('node_template')
    # endregion

    def instantiate(self, context, container):
        raise NotImplementedError

    def find_target(self, context, source_node_template):
        # We might already have a specific node template, so we'll just verify it
        if self.target_node_template_name is not None:
            target_node_template = \
                context.modeling.model.node_templates.get(self.target_node_template_name)

            if not source_node_template.is_target_node_valid(target_node_template):
                context.validation.report('requirement "%s" of node template "%s" is for node '
                                          'template "%s" but it does not match constraints'
                                          % (self.name,
                                             self.target_node_template_name,
                                             source_node_template.name),
                                          level=validation.Issue.BETWEEN_TYPES)
                return None, None

            if self.target_capability_type_name is not None \
                    or self.target_capability_name is not None:
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
            for target_node_template in context.modeling.model.node_templates.itervalues():
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
            context.validation.report('requirement "%s" refers to an unknown node type: %s'
                                      % (self.name,
                                         formatting.safe_repr(self.target_node_type_name)),
                                      level=validation.Issue.BETWEEN_TYPES)
        if self.target_capability_type_name and \
                capability_types.get_descendant(self.target_capability_type_name is None):
            context.validation.report('requirement "%s" refers to an unknown capability type: %s'
                                      % (self.name,
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
                console.puts('Target node type: %s'
                             % context.style.type(self.target_node_type_name))
            elif self.target_node_template_name is not None:
                console.puts('Target node template: %s'
                             % context.style.node(self.target_node_template_name))
            if self.target_capability_type_name is not None:
                console.puts('Target capability type: %s'
                             % context.style.type(self.target_capability_type_name))
            elif self.target_capability_name is not None:
                console.puts('Target capability name: %s'
                             % context.style.node(self.target_capability_name))
            if self.target_node_template_constraints:
                console.puts('Target node template constraints:')
                with context.style.indent:
                    for constraint in self.target_node_template_constraints:
                        console.puts(context.style.literal(constraint))
            if self.relationship_template:
                console.puts('Relationship:')
                with context.style.indent:
                    self.relationship_template.dump(context)


class CapabilityTemplateBase(structure.ModelMixin):
    """
    A capability of a :class:`NodeTemplate`. Nodes expose zero or more capabilities that can be
    matched with :class:`Requirement` instances of other nodes.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`min_occurrences`: Minimum number of requirement matches required
    * :code:`max_occurrences`: Maximum number of requirement matches allowed
    * :code:`valid_source_node_type_names`: Must be represented in the :class:`ModelingContext`
    * :code:`properties`: Dict of :class:`Parameter`
    """
    __tablename__ = 'capability_template'

    __private_fields__ = ['node_template_fk']

    # region foreign keys

    @declared_attr
    def node_template_fk(cls):
        return cls.foreign_key('node_template', nullable=True)

    # endregion

    description = Column(Text)
    type_name = Column(Text)
    min_occurrences = Column(Integer, default=None)  # optional
    max_occurrences = Column(Integer, default=None)  # optional
    # CHECK: type?
    valid_source_node_type_names = Column(Text)

    # region many-to-one relationship
    @declared_attr
    def node_template(cls):
        return cls.many_to_one_relationship('node_template')
    # endregion

    # region many-to-many relationships

    @declared_attr
    def properties(cls):
        return cls.many_to_many_relationship('parameter', table_prefix='properties')

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
        capability = instance_elements.CapabilityBase(self.name, self.type_name)
        capability.min_occurrences = self.min_occurrences
        capability.max_occurrences = self.max_occurrences
        utils.instantiate_dict(context, container, capability.properties, self.properties)
        return capability

    def validate(self, context):
        if context.modeling.capability_types.get_descendant(self.type_name) is None:
            context.validation.report('capability "%s" refers to an unknown type: %s'
                                      % (self.name, formatting.safe_repr(self.type)),  # pylint: disable=no-member
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
            console.puts('Type: %s' % context.style.type(self.type_name))
            console.puts(
                'Occurrences: %d%s'
                % (self.min_occurrences or 0, (' to %d' % self.max_occurrences)
                   if self.max_occurrences is not None else ' or more'))
            if self.valid_source_node_type_names:
                console.puts('Valid source node types: %s'
                             % ', '.join((str(context.style.type(v))
                                          for v in self.valid_source_node_type_names)))
            dump_parameters(context, self.properties)

# endregion


def dump_parameters(context, parameters, name='Properties'):
    if not parameters:
        return
    console.puts('%s:' % name)
    with context.style.indent:
        for parameter_name, parameter in parameters.items():
            if parameter.type_name is not None:
                console.puts('%s = %s (%s)' % (context.style.property(parameter_name),
                                               context.style.literal(parameter.value),
                                               context.style.type(parameter.type_name)))
            else:
                console.puts('%s = %s' % (context.style.property(parameter_name),
                                          context.style.literal(parameter.value)))
            if parameter.description:
                console.puts(context.style.meta(parameter.description))


# TODO (left for tal): Move following two methods to some place parser specific
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
