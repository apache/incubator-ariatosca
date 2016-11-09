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

from __future__ import absolute_import  # so we can import standard 'types'

from collections import OrderedDict
from types import FunctionType

from ..validation import Issue
from ..utils import (StrictList, StrictDict, puts, safe_repr, as_raw, as_raw_list, as_raw_dict,
                     as_agnostic, deepcopy_with_locators)
from .elements import ModelElement, Parameter
from .instance_elements import (ServiceInstance, Node, Capability, Relationship, Artifact, Group,
                                Policy, GroupPolicy, GroupPolicyTrigger, Mapping, Substitution,
                                Interface, Operation)
from .utils import (validate_dict_values, validate_list_values, coerce_dict_values,
                    coerce_list_values, instantiate_dict, dump_list_values, dump_dict_values,
                    dump_parameters, dump_interfaces)


class ServiceModel(ModelElement):
    """
    A service model is a normalized blueprint from which :class:`ServiceInstance` instances
    can be created.

    It is usually created by various DSL parsers, such as ARIA's TOSCA extension. However, it
    can also be created programmatically.

    Properties:

    * :code:`description`: Human-readable description
    * :code:`metadata`: :class:`Metadata`
    * :code:`node_templates`: Dict of :class:`NodeTemplate`
    * :code:`group_templates`: Dict of :class:`GroupTemplate`
    * :code:`policy_templates`: Dict of :class:`PolicyTemplate`
    * :code:`substitution_template`: :class:`SubstituionTemplate`
    * :code:`inputs`: Dict of :class:`Parameter`
    * :code:`outputs`: Dict of :class:`Parameter`
    * :code:`operation_templates`: Dict of :class:`Operation`
    """

    def __init__(self):
        self.description = None
        self.metadata = None
        self.node_templates = StrictDict(key_class=basestring, value_class=NodeTemplate)
        self.group_templates = StrictDict(key_class=basestring, value_class=GroupTemplate)
        self.policy_templates = StrictDict(key_class=basestring, value_class=PolicyTemplate)
        self.substitution_template = None
        self.inputs = StrictDict(key_class=basestring, value_class=Parameter)
        self.outputs = StrictDict(key_class=basestring, value_class=Parameter)
        self.operation_templates = StrictDict(key_class=basestring, value_class=OperationTemplate)

    @property
    def as_raw(self):
        return OrderedDict((
            ('description', self.description),
            ('metadata', as_raw(self.metadata)),
            ('node_templates', as_raw_list(self.node_templates)),
            ('group_templates', as_raw_list(self.group_templates)),
            ('policy_templates', as_raw_list(self.policy_templates)),
            ('substitution_template', as_raw(self.substitution_template)),
            ('inputs', as_raw_dict(self.inputs)),
            ('outputs', as_raw_dict(self.outputs)),
            ('operation_templates', as_raw_list(self.operation_templates))))

    def instantiate(self, context, container):
        service_instance = ServiceInstance()
        context.modeling.instance = service_instance

        service_instance.description = deepcopy_with_locators(self.description)

        if self.metadata is not None:
            service_instance.metadata = self.metadata.instantiate(context, container)

        for node_template in self.node_templates.itervalues():
            for _ in range(node_template.default_instances):
                node = node_template.instantiate(context, container)
                service_instance.nodes[node.id] = node

        instantiate_dict(context, self, service_instance.groups, self.group_templates)
        instantiate_dict(context, self, service_instance.policies, self.policy_templates)
        instantiate_dict(context, self, service_instance.operations, self.operation_templates)

        if self.substitution_template is not None:
            service_instance.substitution = self.substitution_template.instantiate(context,
                                                                                   container)

        instantiate_dict(context, self, service_instance.inputs, self.inputs)
        instantiate_dict(context, self, service_instance.outputs, self.outputs)

        for name, the_input in context.modeling.inputs.iteritems():
            if name not in service_instance.inputs:
                context.validation.report('input "%s" is not supported' % name)
            else:
                service_instance.inputs[name].value = the_input

        return service_instance

    def validate(self, context):
        if self.metadata is not None:
            self.metadata.validate(context)
        validate_dict_values(context, self.node_templates)
        validate_dict_values(context, self.group_templates)
        validate_dict_values(context, self.policy_templates)
        if self.substitution_template is not None:
            self.substitution_template.validate(context)
        validate_dict_values(context, self.inputs)
        validate_dict_values(context, self.outputs)
        validate_dict_values(context, self.operation_templates)

    def coerce_values(self, context, container, report_issues):
        if self.metadata is not None:
            self.metadata.coerce_values(context, container, report_issues)
        coerce_dict_values(context, container, self.node_templates, report_issues)
        coerce_dict_values(context, container, self.group_templates, report_issues)
        coerce_dict_values(context, container, self.policy_templates, report_issues)
        if self.substitution_template is not None:
            self.substitution_template.coerce_values(context, container, report_issues)
        coerce_dict_values(context, container, self.inputs, report_issues)
        coerce_dict_values(context, container, self.outputs, report_issues)
        coerce_dict_values(context, container, self.operation_templates, report_issues)

    def dump(self, context):
        if self.description is not None:
            puts(context.style.meta(self.description))
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
        dump_dict_values(context, self.operation_templates, 'Operation templates')


class NodeTemplate(ModelElement):
    """
    A template for creating zero or more :class:`Node` instances.

    Properties:

    * :code:`name`: Name (will be used as a prefix for node IDs)
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`default_instances`: Default number nodes that will appear in the deployment plan
    * :code:`min_instances`: Minimum number nodes that will appear in the deployment plan
    * :code:`max_instances`: Maximum number nodes that will appear in the deployment plan
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`interface_templates`: Dict of :class:`InterfaceTemplate`
    * :code:`artifact_templates`: Dict of :class:`ArtifactTemplate`
    * :code:`capability_templates`: Dict of :class:`CapabilityTemplate`
    * :code:`requirement_templates`: List of :class:`RequirementTemplate`
    * :code:`target_node_template_constraints`: List of :class:`FunctionType`
    """

    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')

        self.name = name
        self.description = None
        self.type_name = type_name
        self.default_instances = 1
        self.min_instances = 0
        self.max_instances = None
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.interface_templates = StrictDict(key_class=basestring, value_class=InterfaceTemplate)
        self.artifact_templates = StrictDict(key_class=basestring, value_class=ArtifactTemplate)
        self.capability_templates = StrictDict(key_class=basestring, value_class=CapabilityTemplate)
        self.requirement_templates = StrictList(value_class=RequirementTemplate)
        self.target_node_template_constraints = StrictList(value_class=FunctionType)

    def is_target_node_valid(self, target_node_template):
        if self.target_node_template_constraints:
            for node_type_constraint in self.target_node_template_constraints:
                if not node_type_constraint(target_node_template, self):
                    return False
        return True

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('default_instances', self.default_instances),
            ('min_instances', self.min_instances),
            ('max_instances', self.max_instances),
            ('properties', as_raw_dict(self.properties)),
            ('interface_templates', as_raw_list(self.interface_templates)),
            ('artifact_templates', as_raw_list(self.artifact_templates)),
            ('capability_templates', as_raw_list(self.capability_templates)),
            ('requirement_templates', as_raw_list(self.requirement_templates))))

    def instantiate(self, context, container):
        node = Node(context, self.type_name, self.name)
        instantiate_dict(context, node, node.properties, self.properties)
        instantiate_dict(context, node, node.interfaces, self.interface_templates)
        instantiate_dict(context, node, node.artifacts, self.artifact_templates)
        instantiate_dict(context, node, node.capabilities, self.capability_templates)
        return node

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.type_name) is None:
            context.validation.report('node template "%s" has an unknown type: %s'
                                      % (self.name,
                                         safe_repr(self.type_name)),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.interface_templates)
        validate_dict_values(context, self.artifact_templates)
        validate_dict_values(context, self.capability_templates)
        validate_list_values(context, self.requirement_templates)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, self, self.properties, report_issues)
        coerce_dict_values(context, self, self.interface_templates, report_issues)
        coerce_dict_values(context, self, self.artifact_templates, report_issues)
        coerce_dict_values(context, self, self.capability_templates, report_issues)
        coerce_list_values(context, self, self.requirement_templates, report_issues)

    def dump(self, context):
        puts('Node template: %s' % context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            puts('Type: %s' % context.style.type(self.type_name))
            puts('Instances: %d (%d%s)'
                 % (self.default_instances,
                    self.min_instances,
                    (' to %d' % self.max_instances
                     if self.max_instances is not None
                     else ' or more')))
            dump_parameters(context, self.properties)
            dump_interfaces(context, self.interface_templates)
            dump_dict_values(context, self.artifact_templates, 'Artifact tempaltes')
            dump_dict_values(context, self.capability_templates, 'Capability templates')
            dump_list_values(context, self.requirement_templates, 'Requirement templates')


class RequirementTemplate(ModelElement):
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

    def __init__(self, name=None,
                 target_node_type_name=None,
                 target_node_template_name=None,
                 target_capability_type_name=None,
                 target_capability_name=None):
        if name is not None and not isinstance(name, basestring):
            raise ValueError('name must be a string or None')
        if target_node_type_name is not None and not isinstance(target_node_type_name, basestring):
            raise ValueError('target_node_type_name must be a string or None')
        if target_node_template_name is not None and not isinstance(target_node_template_name,
                                                                    basestring):
            raise ValueError('target_node_template_name must be a string or None')
        if target_capability_type_name is not None and not isinstance(target_capability_type_name,
                                                                      basestring):
            raise ValueError('target_capability_type_name must be a string or None')
        if target_capability_name is not None and not isinstance(target_capability_name,
                                                                 basestring):
            raise ValueError('target_capability_name must be a string or None')
        if target_node_type_name is not None and target_node_template_name is not None \
                or target_node_type_name is None and target_node_template_name is None:
            raise ValueError('must set either target_node_type_name or target_node_template_name')
        if target_capability_type_name is not None and target_capability_name is not None:
            raise ValueError('can set either target_capability_type_name or target_capability_name')

        self.name = name
        self.target_node_type_name = target_node_type_name
        self.target_node_template_name = target_node_template_name
        self.target_node_template_constraints = StrictList(value_class=FunctionType)
        self.target_capability_type_name = target_capability_type_name
        self.target_capability_name = target_capability_name
        self.relationship_template = None  # optional

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
                                          level=Issue.BETWEEN_TYPES)
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
        return OrderedDict((
            ('name', self.name),
            ('target_node_type_name', self.target_node_type_name),
            ('target_node_template_name', self.target_node_template_name),
            ('target_capability_type_name', self.target_capability_type_name),
            ('target_capability_name', self.target_capability_name),
            ('relationship_template', as_raw(self.relationship_template))))

    def validate(self, context):
        node_types = context.modeling.node_types
        capability_types = context.modeling.capability_types
        if self.target_node_type_name \
                and node_types.get_descendant(self.target_node_type_name) is None:
            context.validation.report('requirement "%s" refers to an unknown node type: %s'
                                      % (self.name, safe_repr(self.target_node_type_name)),
                                      level=Issue.BETWEEN_TYPES)
        if self.target_capability_type_name and \
                capability_types.get_descendant(self.target_capability_type_name is None):
            context.validation.report('requirement "%s" refers to an unknown capability type: %s'
                                      % (self.name, safe_repr(self.target_capability_type_name)),
                                      level=Issue.BETWEEN_TYPES)
        if self.relationship_template:
            self.relationship_template.validate(context)

    def coerce_values(self, context, container, report_issues):
        if self.relationship_template is not None:
            self.relationship_template.coerce_values(context, container, report_issues)

    def dump(self, context):
        if self.name:
            puts(context.style.node(self.name))
        else:
            puts('Requirement:')
        with context.style.indent:
            if self.target_node_type_name is not None:
                puts('Target node type: %s'
                     % context.style.type(self.target_node_type_name))
            elif self.target_node_template_name is not None:
                puts('Target node template: %s'
                     % context.style.node(self.target_node_template_name))
            if self.target_capability_type_name is not None:
                puts('Target capability type: %s'
                     % context.style.type(self.target_capability_type_name))
            elif self.target_capability_name is not None:
                puts('Target capability name: %s'
                     % context.style.node(self.target_capability_name))
            if self.target_node_template_constraints:
                puts('Target node template constraints:')
                with context.style.indent:
                    for constraint in self.target_node_template_constraints:
                        puts(context.style.literal(constraint))
            if self.relationship_template:
                puts('Relationship:')
                with context.style.indent:
                    self.relationship_template.dump(context)


class CapabilityTemplate(ModelElement):
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

    def __init__(self, name, type_name, valid_source_node_type_names=None):
        if not isinstance(name, basestring):
            raise ValueError('name must be a string or None')
        if not isinstance(type_name, basestring):
            raise ValueError('type_name must be a string or None')

        self.name = name
        self.description = None
        self.type_name = type_name
        self.min_occurrences = None  # optional
        self.max_occurrences = None  # optional
        self.valid_source_node_type_names = valid_source_node_type_names
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)

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
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('min_occurrences', self.min_occurrences),
            ('max_occurrences', self.max_occurrences),
            ('valid_source_node_type_names', self.valid_source_node_type_names),
            ('properties', as_raw_dict(self.properties))))

    def instantiate(self, context, container):
        capability = Capability(self.name, self.type_name)
        capability.min_occurrences = self.min_occurrences
        capability.max_occurrences = self.max_occurrences
        instantiate_dict(context, container, capability.properties, self.properties)
        return capability

    def validate(self, context):
        if context.modeling.capability_types.get_descendant(self.type_name) is None:
            context.validation.report(
                'capability "%s" refers to an unknown type: %s'
                % (self.name, safe_repr(self.type)),  # pylint: disable=no-member
                # TODO fix self.type reference
                level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, self, self.properties, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            puts('Type: %s' % context.style.type(self.type_name))
            puts('Occurrences: %d%s'
                 % (self.min_occurrences or 0, (' to %d' % self.max_occurrences)
                    if self.max_occurrences is not None
                    else ' or more'))
            if self.valid_source_node_type_names:
                puts('Valid source node types: %s'
                     % ', '.join((str(context.style.type(v))
                                  for v in self.valid_source_node_type_names)))
            dump_parameters(context, self.properties)


class RelationshipTemplate(ModelElement):
    """
    Optional addition to a :class:`Requirement` in :class:`NodeTemplate` that can be applied when
    the requirement is matched with a capability.

    Properties:

    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`description`: Description
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`source_interface_templates`: Dict of :class:`InterfaceTemplate`
    * :code:`target_interface_templates`: Dict of :class:`InterfaceTemplate`
    """

    def __init__(self, type_name=None, template_name=None):
        if (type_name is not None) and (not isinstance(type_name, basestring)):
            raise ValueError('type_name must be a string or None')
        if (template_name is not None) and (not isinstance(template_name, basestring)):
            raise ValueError('template_name must be a string or None')
        if type_name is not None and template_name is not None \
                or type_name is None and template_name is None:
            raise ValueError('must set either type_name or template_name')

        self.type_name = type_name
        self.template_name = template_name
        self.description = None
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.source_interface_templates = StrictDict(key_class=basestring,
                                                     value_class=InterfaceTemplate)
        self.target_interface_templates = StrictDict(key_class=basestring,
                                                     value_class=InterfaceTemplate)

    @property
    def as_raw(self):
        return OrderedDict((
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('description', self.description),
            ('properties', as_raw_dict(self.properties)),
            ('source_interface_templates', as_raw_list(self.source_interface_templates)),
            ('target_interface_templates', as_raw_list(self.target_interface_templates))))

    def instantiate(self, context, container):
        relationship = Relationship(self.type_name, self.template_name)
        instantiate_dict(context, container,
                         relationship.properties, self.properties)
        instantiate_dict(context, container,
                         relationship.source_interfaces, self.source_interface_templates)
        instantiate_dict(context, container,
                         relationship.target_interfaces, self.target_interface_templates)
        return relationship

    def validate(self, context):
        if context.modeling.relationship_types.get_descendant(self.type_name) is None:
            context.validation.report(
                'relationship template "%s" has an unknown type: %s'
                % (self.name, safe_repr(self.type_name)),  # pylint: disable=no-member
                # TODO fix self.name reference
                level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.source_interface_templates)
        validate_dict_values(context, self.target_interface_templates)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, self, self.properties, report_issues)
        coerce_dict_values(context, self, self.source_interface_templates, report_issues)
        coerce_dict_values(context, self, self.target_interface_templates, report_issues)

    def dump(self, context):
        if self.type_name is not None:
            puts('Relationship type: %s' % context.style.type(self.type_name))
        else:
            puts('Relationship template: %s' % context.style.node(self.template_name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            dump_parameters(context, self.properties)
            dump_interfaces(context, self.source_interface_templates, 'Source interface templates')
            dump_interfaces(context, self.target_interface_templates, 'Target interface templates')


class ArtifactTemplate(ModelElement):
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

    def __init__(self, name, type_name, source_path):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')
        if not isinstance(source_path, basestring):
            raise ValueError('must set source_path (string)')

        self.name = name
        self.description = None
        self.type_name = type_name
        self.source_path = source_path
        self.target_path = None
        self.repository_url = None
        self.repository_credential = StrictDict(key_class=basestring, value_class=basestring)
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('source_path', self.source_path),
            ('target_path', self.target_path),
            ('repository_url', self.repository_url),
            ('repository_credential', as_agnostic(self.repository_credential)),
            ('properties', as_raw_dict(self.properties.iteritems()))))

    def instantiate(self, context, container):
        artifact = Artifact(self.name, self.type_name, self.source_path)
        artifact.description = deepcopy_with_locators(self.description)
        artifact.target_path = self.target_path
        artifact.repository_url = self.repository_url
        artifact.repository_credential = self.repository_credential
        instantiate_dict(context, container, artifact.properties, self.properties)
        return artifact

    def validate(self, context):
        if context.modeling.artifact_types.get_descendant(self.type_name) is None:
            context.validation.report('artifact "%s" has an unknown type: %s'
                                      % (self.name, safe_repr(self.type_name)),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            puts('Artifact type: %s' % context.style.type(self.type_name))
            puts('Source path: %s' % context.style.literal(self.source_path))
            if self.target_path is not None:
                puts('Target path: %s' % context.style.literal(self.target_path))
            if self.repository_url is not None:
                puts('Repository URL: %s' % context.style.literal(self.repository_url))
            if self.repository_credential:
                puts('Repository credential: %s'
                     % context.style.literal(self.repository_credential))
            dump_parameters(context, self.properties)


class GroupTemplate(ModelElement):
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

    def __init__(self, name, type_name=None):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if (type_name is not None) and (not isinstance(type_name, basestring)):
            raise ValueError('type_name must be a string or None')

        self.name = name
        self.description = None
        self.type_name = type_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.interface_templates = StrictDict(key_class=basestring, value_class=InterfaceTemplate)
        self.policy_templates = StrictDict(key_class=basestring, value_class=GroupPolicyTemplate)
        self.member_node_template_names = StrictList(value_class=basestring)
        self.member_group_template_names = StrictList(value_class=basestring)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('properties', as_raw_dict(self.properties)),
            ('interface_templates', as_raw_list(self.interface_templates)),
            ('policy_templates', as_raw_list(self.policy_templates)),
            ('member_node_template_names', self.member_node_template_names),
            ('member_group_template_names', self.member_group_template_names)))

    def instantiate(self, context, container):
        group = Group(context, self.type_name, self.name)
        instantiate_dict(context, self, group.properties, self.properties)
        instantiate_dict(context, self, group.interfaces, self.interface_templates)
        instantiate_dict(context, self, group.policies, self.policy_templates)
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
                                      % (self.name, safe_repr(self.type_name)),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.interface_templates)
        validate_dict_values(context, self.policy_templates)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, self, self.properties, report_issues)
        coerce_dict_values(context, self, self.interface_templates, report_issues)
        coerce_dict_values(context, self, self.policy_templates, report_issues)

    def dump(self, context):
        puts('Group template: %s' % context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            if self.type_name:
                puts('Type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.properties)
            dump_interfaces(context, self.interface_templates)
            dump_dict_values(context, self.policy_templates, 'Policy templates')
            if self.member_node_template_names:
                puts('Member node templates: %s' % ', '.join(
                    (str(context.style.node(v)) for v in self.member_node_template_names)))


class PolicyTemplate(ModelElement):
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

    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')

        self.name = name
        self.description = None
        self.type_name = type_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.target_node_template_names = StrictList(value_class=basestring)
        self.target_group_template_names = StrictList(value_class=basestring)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('properties', as_raw_dict(self.properties)),
            ('target_node_template_names', self.target_node_template_names),
            ('target_group_template_names', self.target_group_template_names)))

    def instantiate(self, context, container):
        policy = Policy(self.name, self.type_name)
        instantiate_dict(context, self, policy.properties, self.properties)
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
                                      % (self.name, safe_repr(self.type_name)),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, self, self.properties, report_issues)

    def dump(self, context):
        puts('Policy template: %s' % context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            puts('Type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.properties)
            if self.target_node_template_names:
                puts('Target node templates: %s' % ', '.join(
                    (str(context.style.node(v)) for v in self.target_node_template_names)))
            if self.target_group_template_names:
                puts('Target group templates: %s' % ', '.join(
                    (str(context.style.node(v)) for v in self.target_group_template_names)))


class GroupPolicyTemplate(ModelElement):
    """
    Policies applied to groups.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`triggers`: Dict of :class:`GroupPolicyTrigger`
    """

    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')

        self.name = name
        self.description = None
        self.type_name = type_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.triggers = StrictDict(key_class=basestring, value_class=GroupPolicyTriggerTemplate)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('properties', as_raw_dict(self.properties)),
            ('triggers', as_raw_list(self.triggers))))

    def instantiate(self, context, container):
        group_policy = GroupPolicy(self.name, self.type_name)
        group_policy.description = deepcopy_with_locators(self.description)
        instantiate_dict(context, container, group_policy.properties, self.properties)
        instantiate_dict(context, container, group_policy.triggers, self.triggers)
        return group_policy

    def validate(self, context):
        if context.modeling.policy_types.get_descendant(self.type_name) is None:
            context.validation.report('group policy "%s" has an unknown type: %s'
                                      % (self.name, safe_repr(self.type_name)),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.triggers)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)
        coerce_dict_values(context, container, self.triggers, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            puts('Group policy type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.properties)
            dump_dict_values(context, self.triggers, 'Triggers')


class GroupPolicyTriggerTemplate(ModelElement):
    """
    Triggers for :class:`GroupPolicyTemplate`.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`implementation`: Implementation string (interpreted by the orchestrator)
    * :code:`properties`: Dict of :class:`Parameter`
    """

    def __init__(self, name, implementation):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(implementation, basestring):
            raise ValueError('must set implementation (string)')

        self.name = name
        self.description = None
        self.implementation = implementation
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('implementation', self.implementation),
            ('properties', as_raw_dict(self.properties))))

    def instantiate(self, context, container):
        group_policy_trigger = GroupPolicyTrigger(self.name, self.implementation)
        group_policy_trigger.description = deepcopy_with_locators(self.description)
        instantiate_dict(context, container, group_policy_trigger.properties, self.properties)
        return group_policy_trigger

    def validate(self, context):
        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            puts('Implementation: %s' % context.style.literal(self.implementation))
            dump_parameters(context, self.properties)


class MappingTemplate(ModelElement):
    """
    Used by :class:`SubstitutionTemplate` to map a capability or a requirement to a node.

    Properties:

    * :code:`mapped_name`: Exposed capability or requirement name
    * :code:`node_template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`name`: Name of capability or requirement at the node template
    """

    def __init__(self, mapped_name, node_template_name, name):
        if not isinstance(mapped_name, basestring):
            raise ValueError('must set mapped_name (string)')
        if not isinstance(node_template_name, basestring):
            raise ValueError('must set node_template_name (string)')
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')

        self.mapped_name = mapped_name
        self.node_template_name = node_template_name
        self.name = name

    @property
    def as_raw(self):
        return OrderedDict((
            ('mapped_name', self.mapped_name),
            ('node_template_name', self.node_template_name),
            ('name', self.name)))

    def instantiate(self, context, container):
        nodes = context.modeling.instance.find_nodes(self.node_template_name)
        if len(nodes) == 0:
            context.validation.report('mapping "%s" refer to node template "%s" but there are no '
                                      'node instances' % (self.mapped_name,
                                                          self.node_template_name),
                                      level=Issue.BETWEEN_INSTANCES)
            return None
        return Mapping(self.mapped_name, nodes[0].id, self.name)

    def validate(self, context):
        if self.node_template_name not in context.modeling.model.node_templates:
            context.validation.report('mapping "%s" refers to an unknown node template: %s'
                                      % (self.mapped_name, safe_repr(self.node_template_name)),
                                      level=Issue.BETWEEN_TYPES)

    def dump(self, context):
        puts('%s -> %s.%s' % (context.style.node(self.mapped_name),
                              context.style.node(self.node_template_name),
                              context.style.node(self.name)))


class SubstitutionTemplate(ModelElement):
    """
    Used to substitute a single node for the entire deployment.

    Properties:

    * :code:`node_type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`capability_templates`: Dict of :class:`MappingTemplate`
    * :code:`requirement_templates`: Dict of :class:`MappingTemplate`
    """

    def __init__(self, node_type_name):
        if not isinstance(node_type_name, basestring):
            raise ValueError('must set node_type_name (string)')

        self.node_type_name = node_type_name
        self.capability_templates = StrictDict(key_class=basestring, value_class=MappingTemplate)
        self.requirement_templates = StrictDict(key_class=basestring, value_class=MappingTemplate)

    @property
    def as_raw(self):
        return OrderedDict((
            ('node_type_name', self.node_type_name),
            ('capability_templates', as_raw_list(self.capability_templates)),
            ('requirement_templates', as_raw_list(self.requirement_templates))))

    def instantiate(self, context, container):
        substitution = Substitution(self.node_type_name)
        instantiate_dict(context, container, substitution.capabilities, self.capability_templates)
        instantiate_dict(context, container, substitution.requirements, self.requirement_templates)
        return substitution

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.node_type_name) is None:
            context.validation.report('substitution template has an unknown type: %s'
                                      % safe_repr(self.node_type_name),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.capability_templates)
        validate_dict_values(context, self.requirement_templates)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, self, self.capability_templates, report_issues)
        coerce_dict_values(context, self, self.requirement_templates, report_issues)

    def dump(self, context):
        puts('Substitution template:')
        with context.style.indent:
            puts('Node type: %s' % context.style.type(self.node_type_name))
            dump_dict_values(context, self.capability_templates, 'Capability template mappings')
            dump_dict_values(context, self.requirement_templates, 'Requirement template mappings')


class InterfaceTemplate(ModelElement):
    """
    A typed set of :class:`OperationTemplate`.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`inputs`: Dict of :class:`Parameter`
    * :code:`operation_templates`: Dict of :class:`OperationTemplate`
    """

    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')

        self.name = name
        self.description = None
        self.type_name = type_name
        self.inputs = StrictDict(key_class=basestring, value_class=Parameter)
        self.operation_templates = StrictDict(key_class=basestring, value_class=OperationTemplate)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('inputs', as_raw_dict(self.properties)),  # pylint: disable=no-member
            # TODO fix self.properties reference
            ('operation_templates', as_raw_list(self.operation_templates))))

    def instantiate(self, context, container):
        interface = Interface(self.name, self.type_name)
        interface.description = deepcopy_with_locators(self.description)
        instantiate_dict(context, container, interface.inputs, self.inputs)
        instantiate_dict(context, container, interface.operations, self.operation_templates)
        return interface

    def validate(self, context):
        if self.type_name:
            if context.modeling.interface_types.get_descendant(self.type_name) is None:
                context.validation.report('interface "%s" has an unknown type: %s'
                                          % (self.name, safe_repr(self.type_name)),
                                          level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.inputs)
        validate_dict_values(context, self.operation_templates)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.inputs, report_issues)
        coerce_dict_values(context, container, self.operation_templates, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            puts('Interface type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.inputs, 'Inputs')
            dump_dict_values(context, self.operation_templates, 'Operation templates')


class OperationTemplate(ModelElement):
    """
    An operation in a :class:`InterfaceTemplate`.

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

    def __init__(self, name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')

        self.name = name
        self.description = None
        self.implementation = None
        self.dependencies = StrictList(value_class=basestring)
        self.executor = None
        self.max_retries = None
        self.retry_interval = None
        self.inputs = StrictDict(key_class=basestring, value_class=Parameter)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('implementation', self.implementation),
            ('dependencies', self.dependencies),
            ('executor', self.executor),
            ('max_retries', self.max_retries),
            ('retry_interval', self.retry_interval),
            ('inputs', as_raw_dict(self.inputs))))

    def instantiate(self, context, container):
        operation = Operation(self.name)
        operation.description = deepcopy_with_locators(self.description)
        operation.implementation = self.implementation
        operation.dependencies = self.dependencies
        operation.executor = self.executor
        operation.max_retries = self.max_retries
        operation.retry_interval = self.retry_interval
        instantiate_dict(context, container, operation.inputs, self.inputs)
        return operation

    def validate(self, context):
        validate_dict_values(context, self.inputs)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.inputs, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            if self.implementation is not None:
                puts('Implementation: %s' % context.style.literal(self.implementation))
            if self.dependencies:
                puts('Dependencies: %s' % ', '.join(
                    (str(context.style.literal(v)) for v in self.dependencies)))
            if self.executor is not None:
                puts('Executor: %s' % context.style.literal(self.executor))
            if self.max_retries is not None:
                puts('Max retries: %s' % context.style.literal(self.max_retries))
            if self.retry_interval is not None:
                puts('Retry interval: %s' % context.style.literal(self.retry_interval))
            dump_parameters(context, self.inputs, 'Inputs')
