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

from ...utils.collections import StrictList, StrictDict, FrozenList, OrderedDict
from ...utils.formatting import as_raw, as_raw_list, as_raw_dict, as_agnostic, safe_repr
from ...utils.console import puts, indent
from ..validation import Issue
from .elements import Element, Parameter
from .utils import (validate_dict_values, validate_list_values, coerce_dict_values,
                    coerce_list_values, dump_list_values, dump_dict_values, dump_parameters,
                    dump_interfaces)


class ServiceInstance(Element):
    """
    A service instance is an instance of a :class:`ServiceModel`.

    You will usually not create it programmatically, but instead instantiate
    it from the model.

    Properties:

    * :code:`description`: Human-readable description
    * :code:`metadata`: :class:`Metadata`
    * :code:`nodes`: Dict of :class:`Node`
    * :code:`groups`: Dict of :class:`Group`
    * :code:`policies`: Dict of :class:`Policy`
    * :code:`substitution`: :class:`Substitution`
    * :code:`inputs`: Dict of :class:`Parameter`
    * :code:`outputs`: Dict of :class:`Parameter`
    * :code:`operations`: Dict of :class:`Operation`
    """

    def __init__(self):
        self.description = None
        self.metadata = None
        self.nodes = StrictDict(key_class=basestring, value_class=Node)
        self.groups = StrictDict(key_class=basestring, value_class=Group)
        self.policies = StrictDict(key_class=basestring, value_class=Policy)
        self.substitution = None
        self.inputs = StrictDict(key_class=basestring, value_class=Parameter)
        self.outputs = StrictDict(key_class=basestring, value_class=Parameter)
        self.operations = StrictDict(key_class=basestring, value_class=Operation)

    def satisfy_requirements(self, context):
        satisfied = True
        for node in self.nodes.itervalues():
            if not node.satisfy_requirements(context):
                satisfied = False
        return satisfied

    def validate_capabilities(self, context):
        satisfied = True
        for node in self.nodes.itervalues():
            if not node.validate_capabilities(context):
                satisfied = False
        return satisfied

    def find_nodes(self, node_template_name):
        nodes = []
        for node in self.nodes.itervalues():
            if node.template_name == node_template_name:
                nodes.append(node)
        return FrozenList(nodes)

    def get_node_ids(self, node_template_name):
        return FrozenList((node.id for node in self.find_nodes(node_template_name)))

    def find_groups(self, group_template_name):
        groups = []
        for group in self.groups.itervalues():
            if group.template_name == group_template_name:
                groups.append(group)
        return FrozenList(groups)

    def get_group_ids(self, group_template_name):
        return FrozenList((group.id for group in self.find_groups(group_template_name)))

    def is_node_a_target(self, context, target_node):
        for node in self.nodes.itervalues():
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

    @property
    def as_raw(self):
        return OrderedDict((
            ('description', self.description),
            ('metadata', as_raw(self.metadata)),
            ('nodes', as_raw_list(self.nodes)),
            ('groups', as_raw_list(self.groups)),
            ('policies', as_raw_list(self.policies)),
            ('substitution', as_raw(self.substitution)),
            ('inputs', as_raw_dict(self.inputs)),
            ('outputs', as_raw_dict(self.outputs)),
            ('operations', as_raw_list(self.operations))))

    def validate(self, context):
        if self.metadata is not None:
            self.metadata.validate(context)
        validate_dict_values(context, self.nodes)
        validate_dict_values(context, self.groups)
        validate_dict_values(context, self.policies)
        if self.substitution is not None:
            self.substitution.validate(context)
        validate_dict_values(context, self.inputs)
        validate_dict_values(context, self.outputs)
        validate_dict_values(context, self.operations)

    def coerce_values(self, context, container, report_issues):
        if self.metadata is not None:
            self.metadata.coerce_values(context, container, report_issues)
        coerce_dict_values(context, container, self.nodes, report_issues)
        coerce_dict_values(context, container, self.groups, report_issues)
        coerce_dict_values(context, container, self.policies, report_issues)
        if self.substitution is not None:
            self.substitution.coerce_values(context, container, report_issues)
        coerce_dict_values(context, container, self.inputs, report_issues)
        coerce_dict_values(context, container, self.outputs, report_issues)
        coerce_dict_values(context, container, self.operations, report_issues)

    def dump(self, context):
        if self.description is not None:
            puts(context.style.meta(self.description))
        if self.metadata is not None:
            self.metadata.dump(context)
        for node in self.nodes.itervalues():
            node.dump(context)
        for group in self.groups.itervalues():
            group.dump(context)
        for policy in self.policies.itervalues():
            policy.dump(context)
        if self.substitution is not None:
            self.substitution.dump(context)
        dump_parameters(context, self.inputs, 'Inputs')
        dump_parameters(context, self.outputs, 'Outputs')
        dump_dict_values(context, self.operations, 'Operations')

    def dump_graph(self, context):
        for node in self.nodes.itervalues():
            if not self.is_node_a_target(context, node):
                self._dump_graph_node(context, node)

    def _dump_graph_node(self, context, node):
        puts(context.style.node(node.id))
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
                        puts('-> %s %s' % (relationship_name, capability_name))
                    else:
                        puts('-> %s' % relationship_name)
                    target_node = self.nodes.get(relationship.target_node_id)
                    with indent(3):
                        self._dump_graph_node(context, target_node)


class Node(Element):
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
    * :code:`relationship`: List of :class:`Relationship`
    """

    def __init__(self, context, type_name, template_name):
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')
        if not isinstance(template_name, basestring):
            raise ValueError('must set template_name (string)')

        self.id = '%s_%s' % (template_name, context.modeling.generate_id())
        self.type_name = type_name
        self.template_name = template_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.interfaces = StrictDict(key_class=basestring, value_class=Interface)
        self.artifacts = StrictDict(key_class=basestring, value_class=Artifact)
        self.capabilities = StrictDict(key_class=basestring, value_class=Capability)
        self.relationships = StrictList(value_class=Relationship)

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
                                          level=Issue.BETWEEN_INSTANCES)
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
                if requirement_template.relationship_template is not None:
                    relationship = \
                        requirement_template.relationship_template.instantiate(context, self)
                else:
                    relationship = Relationship()
                relationship.name = requirement_template.name
                relationship.source_requirement_index = requirement_template_index
                relationship.target_node_id = target_node.id
                if target_capability is not None:
                    relationship.target_capability_name = target_capability.name
                self.relationships.append(relationship)
            else:
                context.validation.report('requirement "%s" of node "%s" targets node '
                                          'template "%s" but its instantiated nodes do not '
                                          'have enough capacity'
                                          % (requirement_template.name,
                                             self.id,
                                             target_node_template.name),
                                          level=Issue.BETWEEN_INSTANCES)
                return False
        else:
            context.validation.report('requirement "%s" of node "%s" targets node template '
                                      '"%s" but it has no instantiated nodes'
                                      % (requirement_template.name,
                                         self.id,
                                         target_node_template.name),
                                      level=Issue.BETWEEN_INSTANCES)
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
                                          level=Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    @property
    def as_raw(self):
        return OrderedDict((
            ('id', self.id),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', as_raw_dict(self.properties)),
            ('interfaces', as_raw_list(self.interfaces)),
            ('artifacts', as_raw_list(self.artifacts)),
            ('capabilities', as_raw_list(self.capabilities)),
            ('relationships', as_raw_list(self.relationships))))

    def validate(self, context):
        if len(self.id) > context.modeling.id_max_length:
            context.validation.report('"%s" has an ID longer than the limit of %d characters: %d'
                                      % (self.id,
                                         context.modeling.id_max_length,
                                         len(self.id)),
                                      level=Issue.BETWEEN_INSTANCES)

        # TODO: validate that node template is of type?

        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.interfaces)
        validate_dict_values(context, self.artifacts)
        validate_dict_values(context, self.capabilities)
        validate_list_values(context, self.relationships)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, self, self.properties, report_issues)
        coerce_dict_values(context, self, self.interfaces, report_issues)
        coerce_dict_values(context, self, self.artifacts, report_issues)
        coerce_dict_values(context, self, self.capabilities, report_issues)
        coerce_list_values(context, self, self.relationships, report_issues)

    def dump(self, context):
        puts('Node: %s' % context.style.node(self.id))
        with context.style.indent:
            puts('Template: %s' % context.style.node(self.template_name))
            puts('Type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.properties)
            dump_interfaces(context, self.interfaces)
            dump_dict_values(context, self.artifacts, 'Artifacts')
            dump_dict_values(context, self.capabilities, 'Capabilities')
            dump_list_values(context, self.relationships, 'Relationships')


class Capability(Element):
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

    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('name must be a string or None')
        if not isinstance(type_name, basestring):
            raise ValueError('type_name must be a string or None')

        self.name = name
        self.type_name = type_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)

        self.min_occurrences = None # optional
        self.max_occurrences = None # optional
        self.occurrences = 0

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
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('properties', as_raw_dict(self.properties))))

    def validate(self, context):
        if context.modeling.capability_types.get_descendant(self.type_name) is None:
            context.validation.report('capability "%s" has an unknown type: %s'
                                      % (self.name,
                                         safe_repr(self.type_name)),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        with context.style.indent:
            puts('Type: %s' % context.style.type(self.type_name))
            puts('Occurrences: %s (%s%s)'
                 % (self.occurrences,
                    self.min_occurrences or 0,
                    (' to %d' % self.max_occurrences)
                    if self.max_occurrences is not None
                    else ' or more'))
            dump_parameters(context, self.properties)


class Relationship(Element):
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

    def __init__(self, name=None,
                 source_requirement_index=None,
                 type_name=None,
                 template_name=None):
        if name is not None and not isinstance(name, basestring):
            raise ValueError('name must be a string or None')
        if (source_requirement_index is not None and
                (not isinstance(source_requirement_index, int) or (source_requirement_index < 0))):
            raise ValueError('source_requirement_index must be int > 0')
        if type_name is not None and not isinstance(type_name, basestring):
            raise ValueError('type_name must be a string or None')
        if template_name is not None and not isinstance(template_name, basestring):
            raise ValueError('template_name must be a string or None')

        self.name = name
        self.source_requirement_index = source_requirement_index
        self.target_node_id = None
        self.target_capability_name = None
        self.type_name = type_name
        self.template_name = template_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.source_interfaces = StrictDict(key_class=basestring, value_class=Interface)
        self.target_interfaces = StrictDict(key_class=basestring, value_class=Interface)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('source_requirement_index', self.source_requirement_index),
            ('target_node_id', self.target_node_id),
            ('target_capability_name', self.target_capability_name),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', as_raw_dict(self.properties)),
            ('source_interfaces', as_raw_list(self.source_interfaces)),
            ('target_interfaces', as_raw_list(self.target_interfaces))))

    def validate(self, context):
        if self.type_name:
            if context.modeling.relationship_types.get_descendant(self.type_name) is None:
                context.validation.report('relationship "%s" has an unknown type: %s'
                                          % (self.name,
                                             safe_repr(self.type_name)),
                                          level=Issue.BETWEEN_TYPES)
        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.source_interfaces)
        validate_dict_values(context, self.target_interfaces)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)
        coerce_dict_values(context, container, self.source_interfaces, report_issues)
        coerce_dict_values(context, container, self.target_interfaces, report_issues)

    def dump(self, context):
        if self.name:
            if self.source_requirement_index is not None:
                puts('%s (%d) ->' % (context.style.node(self.name), self.source_requirement_index))
            else:
                puts('%s ->' % context.style.node(self.name))
        else:
            puts('->')
        with context.style.indent:
            puts('Node: %s' % context.style.node(self.target_node_id))
            if self.target_capability_name is not None:
                puts('Capability: %s' % context.style.node(self.target_capability_name))
            if self.type_name is not None:
                puts('Relationship type: %s' % context.style.type(self.type_name))
            if self.template_name is not None:
                puts('Relationship template: %s' % context.style.node(self.template_name))
            dump_parameters(context, self.properties)
            dump_interfaces(context, self.source_interfaces, 'Source interfaces')
            dump_interfaces(context, self.target_interfaces, 'Target interfaces')


class Artifact(Element):
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
            ('properties', as_raw_dict(self.properties))))

    def validate(self, context):
        if context.modeling.artifact_types.get_descendant(self.type_name) is None:
            context.validation.report('artifact "%s" has an unknown type: %s'
                                      % (self.name,
                                         safe_repr(self.type_name)),
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


class Group(Element):
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

    def __init__(self, context, type_name, template_name):
        if not isinstance(template_name, basestring):
            raise ValueError('must set template_name (string)')

        self.id = '%s_%s' % (template_name, context.modeling.generate_id())
        self.type_name = type_name
        self.template_name = template_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.interfaces = StrictDict(key_class=basestring, value_class=Interface)
        self.policies = StrictDict(key_class=basestring, value_class=GroupPolicy)
        self.member_node_ids = StrictList(value_class=basestring)
        self.member_group_ids = StrictList(value_class=basestring)

    @property
    def as_raw(self):
        return OrderedDict((
            ('id', self.id),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', as_raw_dict(self.properties)),
            ('interfaces', as_raw_list(self.interfaces)),
            ('policies', as_raw_list(self.policies)),
            ('member_node_ids', self.member_node_ids),
            ('member_group_ids', self.member_group_ids)))

    def validate(self, context):
        if context.modeling.group_types.get_descendant(self.type_name) is None:
            context.validation.report('group "%s" has an unknown type: %s'
                                      % (self.name,  # pylint: disable=no-member
                                         # TODO fix self.name reference
                                         safe_repr(self.type_name)),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.interfaces)
        validate_dict_values(context, self.policies)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)
        coerce_dict_values(context, container, self.interfaces, report_issues)
        coerce_dict_values(context, container, self.policies, report_issues)

    def dump(self, context):
        puts('Group: %s' % context.style.node(self.id))
        with context.style.indent:
            puts('Type: %s' % context.style.type(self.type_name))
            puts('Template: %s' % context.style.type(self.template_name))
            dump_parameters(context, self.properties)
            dump_interfaces(context, self.interfaces)
            dump_dict_values(context, self.policies, 'Policies')
            if self.member_node_ids:
                puts('Member nodes:')
                with context.style.indent:
                    for node_id in self.member_node_ids:
                        puts(context.style.node(node_id))


class Policy(Element):
    """
    An instance of a :class:`PolicyTemplate`.

    Properties:

    * :code:`name`: Name
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`target_node_ids`: Must be represented in the :class:`ServiceInstance`
    * :code:`target_group_ids`: Must be represented in the :class:`ServiceInstance`
    """

    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')

        self.name = name
        self.type_name = type_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.target_node_ids = StrictList(value_class=basestring)
        self.target_group_ids = StrictList(value_class=basestring)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('properties', as_raw_dict(self.properties)),
            ('target_node_ids', self.target_node_ids),
            ('target_group_ids', self.target_group_ids)))

    def validate(self, context):
        if context.modeling.policy_types.get_descendant(self.type_name) is None:
            context.validation.report('policy "%s" has an unknown type: %s'
                                      % (self.name,
                                         safe_repr(self.type_name)),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        puts('Policy: %s' % context.style.node(self.name))
        with context.style.indent:
            puts('Type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.properties)
            if self.target_node_ids:
                puts('Target nodes:')
                with context.style.indent:
                    for node_id in self.target_node_ids:
                        puts(context.style.node(node_id))
            if self.target_group_ids:
                puts('Target groups:')
                with context.style.indent:
                    for group_id in self.target_group_ids:
                        puts(context.style.node(group_id))


class GroupPolicy(Element):
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
        self.triggers = StrictDict(key_class=basestring, value_class=GroupPolicyTrigger)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('properties', as_raw_dict(self.properties)),
            ('triggers', as_raw_list(self.triggers))))

    def validate(self, context):
        if context.modeling.policy_types.get_descendant(self.type_name) is None:
            context.validation.report('group policy "%s" has an unknown type: %s'
                                      % (self.name,
                                         safe_repr(self.type_name)),
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


class GroupPolicyTrigger(Element):
    """
    Triggers for :class:`GroupPolicy`.

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


class Mapping(Element):
    """
    An instance of a :class:`MappingTemplate`.

    Properties:

    * :code:`mapped_name`: Exposed capability or requirement name
    * :code:`node_id`: Must be represented in the :class:`ServiceInstance`
    * :code:`name`: Name of capability or requirement at the node
    """

    def __init__(self, mapped_name, node_id, name):
        if not isinstance(mapped_name, basestring):
            raise ValueError('must set mapped_name (string)')
        if not isinstance(node_id, basestring):
            raise ValueError('must set node_id (string)')
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')

        self.mapped_name = mapped_name
        self.node_id = node_id
        self.name = name

    @property
    def as_raw(self):
        return OrderedDict((
            ('mapped_name', self.mapped_name),
            ('node_id', self.node_id),
            ('name', self.name)))

    def dump(self, context):
        puts('%s -> %s.%s'
             % (context.style.node(self.mapped_name),
                context.style.node(self.node_id),
                context.style.node(self.name)))


class Substitution(Element):
    """
    An instance of a :class:`SubstitutionTemplate`.

    Properties:

    * :code:`node_type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`capabilities`: Dict of :class:`Mapping`
    * :code:`requirements`: Dict of :class:`Mapping`
    """

    def __init__(self, node_type_name):
        if not isinstance(node_type_name, basestring):
            raise ValueError('must set node_type_name (string)')

        self.node_type_name = node_type_name
        self.capabilities = StrictDict(key_class=basestring, value_class=Mapping)
        self.requirements = StrictDict(key_class=basestring, value_class=Mapping)

    @property
    def as_raw(self):
        return OrderedDict((
            ('node_type_name', self.node_type_name),
            ('capabilities', as_raw_list(self.capabilities)),
            ('requirements', as_raw_list(self.requirements))))

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.node_type_name) is None:
            context.validation.report('substitution "%s" has an unknown type: %s'
                                      % (self.name,  # pylint: disable=no-member
                                         # TODO fix self.name reference
                                         safe_repr(self.node_type_name)),
                                      level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.capabilities)
        validate_dict_values(context, self.requirements)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.capabilities, report_issues)
        coerce_dict_values(context, container, self.requirements, report_issues)

    def dump(self, context):
        puts('Substitution:')
        with context.style.indent:
            puts('Node type: %s' % context.style.type(self.node_type_name))
            dump_dict_values(context, self.capabilities, 'Capability mappings')
            dump_dict_values(context, self.requirements, 'Requirement mappings')


class Interface(Element):
    """
    A typed set of :class:`Operation`.

    Properties:

    * :code:`name`: Name
    * :code:`description`: Description
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`inputs`: Dict of :class:`Parameter`
    * :code:`operations`: Dict of :class:`Operation`
    """

    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')

        self.name = name
        self.description = None
        self.type_name = type_name
        self.inputs = StrictDict(key_class=basestring, value_class=Parameter)
        self.operations = StrictDict(key_class=basestring, value_class=Operation)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('type_name', self.type_name),
            ('inputs', as_raw_dict(self.inputs)),
            ('operations', as_raw_list(self.operations))))

    def validate(self, context):
        if self.type_name:
            if context.modeling.interface_types.get_descendant(self.type_name) is None:
                context.validation.report('interface "%s" has an unknown type: %s'
                                          % (self.name,
                                             safe_repr(self.type_name)),
                                          level=Issue.BETWEEN_TYPES)

        validate_dict_values(context, self.inputs)
        validate_dict_values(context, self.operations)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.inputs, report_issues)
        coerce_dict_values(context, container, self.operations, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        if self.description:
            puts(context.style.meta(self.description))
        with context.style.indent:
            puts('Interface type: %s' % context.style.type(self.type_name))
            dump_parameters(context, self.inputs, 'Inputs')
            dump_dict_values(context, self.operations, 'Operations')


class Operation(Element):
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
                puts('Dependencies: %s'
                     % ', '.join((str(context.style.literal(v)) for v in self.dependencies)))
            if self.executor is not None:
                puts('Executor: %s' % context.style.literal(self.executor))
            if self.max_retries is not None:
                puts('Max retries: %s' % context.style.literal(self.max_retries))
            if self.retry_interval is not None:
                puts('Retry interval: %s' % context.style.literal(self.retry_interval))
            dump_parameters(context, self.inputs, 'Inputs')
