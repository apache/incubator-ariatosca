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

    def instantiate(self, container, model_storage, inputs=None):  # pylint: disable=arguments-differ
        from . import models
        now = datetime.now()
        service = models.Service(created_at=now,
                                 updated_at=now,
                                 description=deepcopy_with_locators(self.description),
                                 service_template=self)

        # TODO: we want to remove this use of the context
        context = ConsumptionContext.get_thread_local()
        context.modeling.instance = service

        utils.validate_no_undeclared_inputs(declared_inputs=self.inputs,
                                            supplied_inputs=inputs or {})
        utils.validate_required_inputs_are_supplied(declared_inputs=self.inputs,
                                                    supplied_inputs=inputs or {})

        service.inputs = utils.merge_parameter_values(inputs, self.inputs, model_cls=models.Input)
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
            for _ in range(node_template.scaling['default_instances']):
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

    def instantiate(self, container):
        from . import models
        node = models.Node(name=self._next_name,
                           type=self.type,
                           description=deepcopy_with_locators(self.description),
                           state=models.Node.INITIAL,
                           node_template=self)
        utils.instantiate_dict(node, node.properties, self.properties)
        utils.instantiate_dict(node, node.attributes, self.attributes)
        utils.instantiate_dict(node, node.interfaces, self.interface_templates)
        utils.instantiate_dict(node, node.artifacts, self.artifact_templates)
        utils.instantiate_dict(node, node.capabilities, self.capability_templates)

        # Default attributes
        if ('tosca_name' in node.attributes) \
            and (node.attributes['tosca_name'].type_name == 'string'):
            node.attributes['tosca_name'].value = self.name
        if 'tosca_id' in node.attributes \
            and (node.attributes['tosca_id'].type_name == 'string'):
            node.attributes['tosca_id'].value = node.name

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
            utils.dump_dict_values(self.properties, 'Properties')
            utils.dump_dict_values(self.attributes, 'Attributes')
            utils.dump_interfaces(self.interface_templates)
            utils.dump_dict_values(self.artifact_templates, 'Artifact templates')
            utils.dump_dict_values(self.capability_templates, 'Capability templates')
            utils.dump_list_values(self.requirement_templates, 'Requirement templates')

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

        def default_property(name, value):
            if name not in scaling:
                scaling[name] = value

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
        default_property('min_instances', 0)
        default_property('max_instances', 1)
        default_property('default_instances', 1)

        # Validate
        # pylint: disable=too-many-boolean-expressions
        if ((scaling['min_instances'] < 0) or
                (scaling['max_instances'] < 0) or
                (scaling['default_instances'] < 0) or
                (scaling['max_instances'] < scaling['min_instances']) or
                (scaling['default_instances'] < scaling['min_instances']) or
                (scaling['default_instances'] > scaling['max_instances'])):
            context = ConsumptionContext.get_thread_local()
            context.validation.report('invalid scaling parameters for node template "{0}": '
                                      'min={1}, max={2}, default={3}'.format(
                                          self.name,
                                          scaling['min_instances'],
                                          scaling['max_instances'],
                                          scaling['default_instances']),
                                      level=validation.Issue.BETWEEN_TYPES)

        return scaling

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

    def coerce_values(self, report_issues):
        pass

    def instantiate(self, container):
        from . import models
        context = ConsumptionContext.get_thread_local()
        if self.capability_template is not None:
            node_template = self.capability_template.node_template
        else:
            node_template = self.requirement_template.node_template
        nodes = node_template.nodes
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
                                          capability=capability,
                                          requirement_template=self.requirement_template,
                                          node=node)


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
        if self.capability_template is not None:
            node_template = self.capability_template.node_template
        else:
            node_template = self.requirement_template.node_template
        console.puts('{0} -> {1}.{2}'.format(
            context.style.node(self.name),
            context.style.node(node_template.name),
            context.style.node(self.capability_template.name
                               if self.capability_template
                               else self.requirement_template.name)))


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
                    self.node_template.service_template.node_templates.itervalues():
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

    def instantiate(self, container):
        from . import models

        plugin = self.plugin_specification.plugin \
            if (self.plugin_specification is not None) and self.plugin_specification.enabled \
            else None

        operation = models.Operation(name=self.name,
                                     description=deepcopy_with_locators(self.description),
                                     relationship_edge=self.relationship_edge,
                                     implementation=self.implementation,
                                     dependencies=self.dependencies,
                                     executor=self.executor,
                                     plugin=plugin,
                                     function=self.function,
                                     max_attempts=self.max_attempts,
                                     retry_interval=self.retry_interval,
                                     operation_template=self)

        utils.instantiate_dict(container, operation.inputs, self.inputs)
        utils.instantiate_dict(container, operation.configurations, self.configurations)

        return operation

    def validate(self):
        utils.validate_dict_values(self.inputs)
        utils.validate_dict_values(self.configurations)

    def coerce_values(self, report_issues):
        utils.coerce_dict_values(self.inputs, report_issues)
        utils.coerce_dict_values(self.configurations, report_issues)

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
                console.puts('Dependencies: {0}'.format(
                    ', '.join((str(context.style.literal(v)) for v in self.dependencies))))
            utils.dump_dict_values(self.inputs, 'Inputs')
            if self.executor is not None:
                console.puts('Executor: {0}'.format(context.style.literal(self.executor)))
            if self.max_attempts is not None:
                console.puts('Max attempts: {0}'.format(context.style.literal(self.max_attempts)))
            if self.retry_interval is not None:
                console.puts('Retry interval: {0}'.format(
                    context.style.literal(self.retry_interval)))
            if self.plugin_specification is not None:
                console.puts('Plugin specification: {0}'.format(
                    context.style.literal(self.plugin_specification.name)))
            utils.dump_dict_values(self.configurations, 'Configuration')
            if self.function is not None:
                console.puts('Function: {0}'.format(context.style.literal(self.function)))


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
    def plugin(cls): # pylint: disable=method-hidden
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
