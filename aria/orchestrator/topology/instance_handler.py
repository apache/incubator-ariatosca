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

from ... parser.modeling import context
from ... modeling import models, functions
from ... utils import formatting
from .. import execution_plugin
from .. import decorators
from . import common


class Artifact(common.InstanceHandlerBase):

    def coerce(self, **kwargs):
        self._topology.coerce(self._model.properties, **kwargs)

    def validate(self, **kwargs):
        self._topology.validate(self._model.properties, **kwargs)

    def dump(self, out_stream):
        with out_stream.indent():
            out_stream.write(out_stream.node_style(self._model.name))
            out_stream.write(out_stream.meta_style(self._model.description))
            with out_stream.indent():
                out_stream.write(u'Artifact type: {0}'.format(out_stream.type_style(
                    self._model.type.name)))
                out_stream.write(u'Source path: {0}'.format(
                    out_stream.literal_style(self._model.source_path)))
                if self._model.target_path is not None:
                    out_stream.write(u'Target path: {0}'.format(
                        out_stream.literal_style(self._model.target_path)))
                if self._model.repository_url is not None:
                    out_stream.write(u'Repository URL: {0}'.format(
                        out_stream.literal_style(self._model.repository_url)))
                if self._model.repository_credential:
                    out_stream.write(u'Repository credential: {0}'.format(
                        out_stream.literal_style(self._model.repository_credential)))
                self._topology.dump(self._model.properties, out_stream, title='Properties')


class Capability(common.InstanceHandlerBase):
    def coerce(self, **kwargs):
        self._topology.coerce(self._model.properties, **kwargs)

    def validate(self, **kwargs):
        self._topology.validate(self._model.properties, **kwargs)

    def dump(self, out_stream):
        out_stream.write(out_stream.node_style(self._model.name))
        with out_stream.indent():
            out_stream.write(u'Type: {0}'.format(out_stream.type_style(self._model.type.name)))
            out_stream.write(u'Occurrences: {0:d} ({1:d}{2})'.format(
                self._model.occurrences,
                self._model.min_occurrences or 0,
                u' to {0:d}'.format(self._model.max_occurrences)
                if self._model.max_occurrences is not None
                else ' or more'))
            self._topology.dump(self._model.properties, out_stream, title='Properties')


class Group(common.ActorHandlerBase):

    def coerce(self, **kwargs):
        self._coerce(self._model.properties, self._model.interfaces, **kwargs)

    def validate(self, **kwargs):
        self._validate(self._model.properties,
                       self._model.interfaces,
                       **kwargs)

    def dump(self, out_stream):
        out_stream.write(u'Group: {0}'.format(out_stream.node_style(self._model.name)))
        with out_stream.indent():
            out_stream.write(u'Type: {0}'.format(out_stream.type_style(self._model.type.name)))
            self._topology.dump(self._model.properties, out_stream, title='Properties')
            self._topology.dump(self._model.interfaces, out_stream, title='Interfaces')
            if self._model.nodes:
                out_stream.write('Member nodes:')
                with out_stream.indent():
                    for node in self._model.nodes:
                        out_stream.write(out_stream.node_style(node.name))

    def configure_operations(self):
        for interface in self._model.interfaces.values():
            self._topology.configure_operations(interface)


class Interface(common.ActorHandlerBase):
    def coerce(self, **kwargs):
        self._coerce(self._model.inputs, self._model.operations, **kwargs)

    def validate(self, **kwargs):
        self._validate(self._model.inputs,
                       self._model.operations,
                       **kwargs)

    def dump(self, out_stream):
        out_stream.write(out_stream.node_style(self._model.name))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))
        with out_stream.indent():
            out_stream.write(u'Interface type: {0}'.format(
                out_stream.type_style(self._model.type.name)))
            self._topology.dump(self._model.inputs, out_stream, title='Inputs')
            self._topology.dump(self._model.operations, out_stream, title='Operations')

    def configure_operations(self):
        for operation in self._model.operations.values():
            self._topology.configure_operations(operation)


class Node(common.ActorHandlerBase):
    def coerce(self, **kwargs):
        self._coerce(self._model.properties,
                     self._model.attributes,
                     self._model.interfaces,
                     self._model.artifacts,
                     self._model.capabilities,
                     self._model.outbound_relationships,
                     **kwargs)

    def validate(self, **kwargs):
        if len(self._model.name) > context.ID_MAX_LENGTH:
            self._topology.report(
                u'"{0}" has an ID longer than the limit of {1:d} characters: {2:d}'.format(
                    self._model.name, context.ID_MAX_LENGTH, len(self._model.name)),
                level=self._topology.Issue.BETWEEN_INSTANCES)

        self._validate(self._model.properties,
                       self._model.attributes,
                       self._model.interfaces,
                       self._model.artifacts,
                       self._model.capabilities,
                       self._model.outbound_relationships)

    def dump(self, out_stream):
        out_stream.write(u'Node: {0}'.format(out_stream.node_style(self._model.name)))
        with out_stream.indent():
            out_stream.write(u'Type: {0}'.format(out_stream.type_style(self._model.type.name)))
            out_stream.write(u'Template: {0}'.format(
                out_stream.node_style(self._model.node_template.name)))
            self._topology.dump(self._model.properties, out_stream, title='Properties')
            self._topology.dump(self._model.attributes, out_stream, title='Attributes')
            self._topology.dump(self._model.interfaces, out_stream, title='Interfaces')
            self._topology.dump(self._model.artifacts, out_stream, title='Artifacts')
            self._topology.dump(self._model.capabilities, out_stream, title='Capabilities')
            self._topology.dump(self._model.outbound_relationships, out_stream,
                                title='Relationships')

    def configure_operations(self):
        for interface in self._model.interfaces.values():
            self._topology.configure_operations(interface)
        for relationship in self._model.outbound_relationships:
            self._topology.configure_operations(relationship)

    def validate_capabilities(self):
        satisfied = False
        for capability in self._model.capabilities.itervalues():
            if not capability.has_enough_relationships:
                self._topology.report(
                    u'capability "{0}" of node "{1}" requires at least {2:d} '
                    u'relationships but has {3:d}'.format(capability.name,
                                                          self._model.name,
                                                          capability.min_occurrences,
                                                          capability.occurrences),
                    level=self._topology.Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    def satisfy_requirements(self):
        satisfied = True
        for requirement_template in self._model.node_template.requirement_templates:

            # Since we try and satisfy requirements, which are node template bound, and use that
            # information in the creation of the relationship, Some requirements may have been
            # satisfied by a previous run on that node template.
            # The entire mechanism of satisfying requirements needs to be refactored.
            if any(rel.requirement_template == requirement_template
                   for rel in self._model.outbound_relationships):
                continue

            # Find target template
            target_node_template, target_node_capability = self._find_target(requirement_template)
            if target_node_template is not None:
                satisfied = self._satisfy_capability(
                    target_node_capability, target_node_template, requirement_template)
            else:
                self._topology.report(u'requirement "{0}" of node "{1}" has no target node template'
                                      .format(requirement_template.name, self._model.name),
                                      level=self._topology.Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    def _satisfy_capability(self, target_node_capability, target_node_template,
                            requirement_template):
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
                    relationship_model = self._topology.instantiate(
                        requirement_template.relationship_template)
                else:
                    relationship_model = models.Relationship()
                relationship_model.name = requirement_template.name
                relationship_model.requirement_template = requirement_template
                relationship_model.target_node = target_node
                relationship_model.target_capability = target_capability
                self._model.outbound_relationships.append(relationship_model)
                return True
            else:
                self._topology.report(
                    u'requirement "{0}" of node "{1}" targets node '
                    u'template "{2}" but its instantiated nodes do not '
                    u'have enough capacity'.format(
                        requirement_template.name, self._model.name, target_node_template.name),
                    level=self._topology.Issue.BETWEEN_INSTANCES)
                return False
        else:
            self._topology.report(
                u'requirement "{0}" of node "{1}" targets node template '
                u'"{2}" but it has no instantiated nodes'.format(
                    requirement_template.name, self._model.name, target_node_template.name),
                level=self._topology.Issue.BETWEEN_INSTANCES)
            return False

    def _find_target(self, requirement_template):
        # We might already have a specific node template from the requirement template, so
        # we'll just verify it
        if requirement_template.target_node_template is not None:
            if not self._model.node_template.is_target_node_template_valid(
                    requirement_template.target_node_template):
                self._topology.report(
                    u'requirement "{0}" of node template "{1}" is for node '
                    u'template "{2}" but it does not match constraints'.format(
                        requirement_template.name,
                        requirement_template.target_node_template.name,
                        self._model.node_template.name),
                    level=self._topology.Issue.BETWEEN_TYPES)
            if (requirement_template.target_capability_type is not None or
                    requirement_template.target_capability_name is not None):
                target_node_capability = self._get_capability(requirement_template)
                if target_node_capability is None:
                    return None, None
            else:
                target_node_capability = None

            return requirement_template.target_node_template, target_node_capability

        # Find first node that matches the type
        elif requirement_template.target_node_type is not None:
            for target_node_template in \
                    self._model.node_template.service_template.node_templates.itervalues():
                if requirement_template.target_node_type.get_descendant(
                        target_node_template.type.name) is None:
                    continue

                if not self._model.node_template.is_target_node_template_valid(
                        target_node_template):
                    continue

                target_node_capability = self._get_capability(requirement_template,
                                                              target_node_template)

                if target_node_capability is None:
                    continue

                return target_node_template, target_node_capability

        # Find the first node which has a capability of the required type
        elif requirement_template.target_capability_type is not None:
            for target_node_template in \
                    self._model.node_template.service_template.node_templates.itervalues():
                target_node_capability = \
                    self._get_capability(requirement_template, target_node_template)
                if target_node_capability:
                    return target_node_template, target_node_capability

        return None, None

    def _get_capability(self, requirement_template, target_node_template=None):
        target_node_template = target_node_template or requirement_template.target_node_template

        for capability_template in target_node_template.capability_templates.values():
            if self._satisfies_requirement(
                    capability_template, requirement_template, target_node_template):
                return capability_template

        return None

    def _satisfies_requirement(
            self, capability_template, requirement_template, target_node_template):
        # Do we match the required capability type?
        if (requirement_template.target_capability_type and
                requirement_template.target_capability_type.get_descendant(
                    capability_template.type.name) is None):
            return False

        # Are we in valid_source_node_types?
        if capability_template.valid_source_node_types:
            for valid_source_node_type in capability_template.valid_source_node_types:
                if valid_source_node_type.get_descendant(
                        self._model.node_template.type.name) is None:
                    return False

        # Apply requirement constraints
        if requirement_template.target_node_template_constraints:
            for node_template_constraint in requirement_template.target_node_template_constraints:
                if not node_template_constraint.matches(
                        self._model.node_template, target_node_template):
                    return False

        return True


class Operation(common.ActorHandlerBase):
    def coerce(self, **kwargs):
        self._coerce(self._model.inputs,
                     self._model.configurations,
                     self._model.arguments,
                     **kwargs)

    def validate(self, **kwargs):
        self._validate(self._model.inputs,
                       self._model.configurations,
                       self._model.arguments,
                       **kwargs)

    def dump(self, out_stream):
        out_stream.write(out_stream.node_style(self._model.name))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))
        with out_stream.indent():
            if self._model.implementation is not None:
                out_stream.write(u'Implementation: {0}'.format(
                    out_stream.literal_style(self._model.implementation)))
            if self._model.dependencies:
                out_stream.write(
                    u'Dependencies: {0}'.format(u', '.join((str(out_stream.literal_style(v))
                                                            for v in self._model.dependencies))))
            self._topology.dump(self._model.inputs, out_stream, title='Inputs')
            if self._model.executor is not None:
                out_stream.write(u'Executor: {0}'.format(out_stream.literal_style(
                    self._model.executor)))
            if self._model.max_attempts is not None:
                out_stream.write(u'Max attempts: {0}'.format(out_stream.literal_style(
                    self._model.max_attempts)))
            if self._model.retry_interval is not None:
                out_stream.write(u'Retry interval: {0}'.format(
                    out_stream.literal_style(self._model.retry_interval)))
            if self._model.plugin is not None:
                out_stream.write(u'Plugin: {0}'.format(
                    out_stream.literal_style(self._model.plugin.name)))
            self._topology.dump(self._model.configurations, out_stream, title='Configuration')
            if self._model.function is not None:
                out_stream.write(u'Function: {0}'.format(out_stream.literal_style(
                    self._model.function)))
            self._topology.dump(self._model.arguments, out_stream, title='Arguments')

    def configure_operations(self):
        if self._model.implementation is None and self._model.function is None:
            return

        if (self._model.interface is not None and
                self._model.plugin is None and
                self._model.function is None):
            # ("interface" is None for workflow operations, which do not currently use "plugin")
            # The default (None) plugin is the execution plugin
            execution_plugin.instantiation.configure_operation(self._model, self._topology)
        else:
            # In the future plugins may be able to add their own "configure_operation" hook that
            # can validate the configuration and otherwise create specially derived arguments. For
            # now, we just send all configuration parameters as arguments without validation.
            for key, conf in self._model.configurations.items():
                self._model.arguments[key] = self._topology.instantiate(conf.as_argument())

        if self._model.interface is not None:
            # Send all interface inputs as extra arguments
            # ("interface" is None for workflow operations)
            # Note that they will override existing arguments of the same names
            for key, input in self._model.interface.inputs.items():
                self._model.arguments[key] = self._topology.instantiate(input.as_argument())

        # Send all inputs as extra arguments
        # Note that they will override existing arguments of the same names
        for key, input in self._model.inputs.items():
            self._model.arguments[key] = self._topology.instantiate(input.as_argument())

        # Check for reserved arguments
        used_reserved_names = set(decorators.OPERATION_DECORATOR_RESERVED_ARGUMENTS).intersection(
            self._model.arguments.keys())
        if used_reserved_names:
            self._topology.report(
                u'using reserved arguments in operation "{0}": {1}'.format(
                    self._model.name, formatting.string_list_as_string(used_reserved_names)),
                level=self._topology.Issue.EXTERNAL)


class Policy(common.InstanceHandlerBase):
    def coerce(self, **kwargs):
        self._topology.coerce(self._model.properties, **kwargs)

    def validate(self, **kwargs):
        self._topology.validate(self._model.properties, **kwargs)

    def dump(self, out_stream):
        out_stream.write(u'Policy: {0}'.format(out_stream.node_style(self._model.name)))
        with out_stream.indent():
            out_stream.write(u'Type: {0}'.format(out_stream.type_style(self._model.type.name)))
            self._topology.dump(self._model.properties, out_stream, title='Properties')
            if self._model.nodes:
                out_stream.write('Target nodes:')
                with out_stream.indent():
                    for node in self._model.nodes:
                        out_stream.write(out_stream.node_style(node.name))
            if self._model.groups:
                out_stream.write('Target groups:')
                with out_stream.indent():
                    for group in self._model.groups:
                        out_stream.write(out_stream.node_style(group.name))


class Relationship(common.ActorHandlerBase):
    def coerce(self, **kwargs):
        self._coerce(self._model.properties,
                     self._model.interfaces,
                     **kwargs)

    def validate(self, **kwargs):
        self._validate(self._model.properties,
                       self._model.interfaces,
                       **kwargs)

    def dump(self, out_stream):
        if self._model.name:
            out_stream.write(u'{0} ->'.format(out_stream.node_style(self._model.name)))
        else:
            out_stream.write('->')
        with out_stream.indent():
            out_stream.write(u'Node: {0}'.format(out_stream.node_style(
                self._model.target_node.name)))
            if self._model.target_capability:
                out_stream.write(u'Capability: {0}'.format(out_stream.node_style(
                    self._model.target_capability.name)))
            if self._model.type is not None:
                out_stream.write(u'Relationship type: {0}'.format(
                    out_stream.type_style(self._model.type.name)))
            if (self._model.relationship_template is not None and
                    self._model.relationship_template.name):
                out_stream.write(u'Relationship template: {0}'.format(
                    out_stream.node_style(self._model.relationship_template.name)))
            self._topology.dump(self._model.properties, out_stream, title='Properties')
            self._topology.dump(self._model.interfaces, out_stream, title='Interfaces')

    def configure_operations(self):
        for interface in self._model.interfaces.values():
            self._topology.configure_operations(interface)


class Service(common.ActorHandlerBase):
    def coerce(self, **kwargs):
        self._coerce(self._model.meta_data,
                     self._model.nodes,
                     self._model.groups,
                     self._model.policies,
                     self._model.substitution,
                     self._model.inputs,
                     self._model.outputs,
                     self._model.workflows,
                     **kwargs)

    def validate(self, **kwargs):
        self._validate(self._model.meta_data,
                       self._model.nodes,
                       self._model.groups,
                       self._model.policies,
                       self._model.substitution,
                       self._model.inputs,
                       self._model.outputs,
                       self._model.workflows,
                       **kwargs)

    def dump(self, out_stream):
        if self._model.description is not None:
            out_stream.write(out_stream.meta_style(self._model.description))
        self._topology.dump(self._model.meta_data, out_stream, title='Metadata')
        self._topology.dump(self._model.nodes, out_stream)
        self._topology.dump(self._model.groups, out_stream)
        self._topology.dump(self._model.policies, out_stream)
        self._topology.dump(self._model.substitution, out_stream)
        self._topology.dump(self._model.inputs, out_stream, title='Inputs')
        self._topology.dump(self._model.outputs, out_stream, title='Outputs')
        self._topology.dump(self._model.workflows, out_stream, title='Workflows')

    def configure_operations(self):
        for node in self._model.nodes.itervalues():
            self._topology.configure_operations(node)
        for group in self._model.groups.itervalues():
            self._topology.configure_operations(group)
        for operation in self._model.workflows.itervalues():
            self._topology.configure_operations(operation)

    def validate_capabilities(self):
        satisfied = True
        for node in self._model.nodes.values():
            if not self._topology.validate_capabilities(node):
                satisfied = False
        return satisfied

    def satisfy_requirements(self):
        return all(self._topology.satisfy_requirements(node)
                   for node in self._model.nodes.values())


class Substitution(common.InstanceHandlerBase):
    def coerce(self, **kwargs):
        self._topology.coerce(self._model.mappings, **kwargs)

    def validate(self, **kwargs):
        self._topology.validate(self._model.mappings, **kwargs)

    def dump(self, out_stream):
        out_stream.write('Substitution:')
        with out_stream.indent():
            out_stream.write(u'Node type: {0}'.format(out_stream.type_style(
                self._model.node_type.name)))
            self._topology.dump(self._model.mappings, out_stream, title='Mappings')


class SubstitutionMapping(common.InstanceHandlerBase):

    def coerce(self, **kwargs):
        pass

    def validate(self, **_):
        if (self._model.capability is None) and (self._model.requirement_template is None):
            self._topology.report(
                u'mapping "{0}" refers to neither capability nor a requirement'
                u' in node: {1}'.format(
                    self._model.name, formatting.safe_repr(self._model.node_style.name)),
                level=self._topology.Issue.BETWEEN_TYPES)

    def dump(self, out_stream):
        if self._model.capability is not None:
            out_stream.write(u'{0} -> {1}.{2}'.format(
                out_stream.node_style(self._model.name),
                out_stream.node_style(self._model.capability.node.name),
                out_stream.node_style(self._model.capability.name)))
        else:
            out_stream.write(u'{0} -> {1}.{2}'.format(
                out_stream.node_style(self._model.name),
                out_stream.node_style(self._model.node.name),
                out_stream.node_style(self._model.requirement_template.name)))


class Metadata(common.InstanceHandlerBase):

    def dump(self, out_stream):
        out_stream.write(u'{0}: {1}'.format(
            out_stream.property_style(self._model.name),
            out_stream.literal_style(self._model.value)))

    def coerce(self, **_):
        pass

    def instantiate(self, instance_cls):
        return instance_cls(name=self._model.name, value=self._model.value)

    def validate(self):
        pass


class _Parameter(common.InstanceHandlerBase):

    def dump(self, out_stream):
        if self._model.type_name is not None:
            out_stream.write(u'{0}: {1} ({2})'.format(
                out_stream.property_style(self._model.name),
                out_stream.literal_style(formatting.as_raw(self._model.value)),
                out_stream.type_style(self._model.type_name)))
        else:
            out_stream.write(u'{0}: {1}'.format(
                out_stream.property_style(self._model.name),
                out_stream.literal_style(formatting.as_raw(self._model.value))))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))

    def instantiate(self, instance_cls, **kwargs):
        return instance_cls(
            name=self._model.name,                                                                  # pylint: disable=unexpected-keyword-arg
            type_name=self._model.type_name,
            _value=self._model._value,
            description=self._model.description
        )

    def validate(self):
        pass

    def coerce(self, report_issues):                                                                # pylint: disable=arguments-differ
        value = self._model._value
        if value is not None:
            evaluation = functions.evaluate(value, self._model, report_issues)
            if (evaluation is not None) and evaluation.final:
                # A final evaluation can safely replace the existing value
                self._model._value = evaluation.value


class Attribute(_Parameter):
    pass


class Input(_Parameter):
    pass


class Output(_Parameter):
    pass


class Argument(_Parameter):
    pass


class Property(_Parameter):
    pass


class Configuration(_Parameter):
    pass


class Type(common.InstanceHandlerBase):
    def coerce(self, **_):
        pass

    def dump(self, out_stream):
        if self._model.name:
            out_stream.write(out_stream.type_style(self._model.name))
        with out_stream.indent():
            for child in self._model.children:
                self._topology.dump(child, out_stream)

    def validate(self, **kwargs):
        pass
