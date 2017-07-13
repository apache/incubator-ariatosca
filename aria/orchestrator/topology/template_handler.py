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

from datetime import datetime

from ...utils import (
    formatting,
    versions
)
from ...modeling import utils as modeling_utils
from . import utils, common


class ServiceTemplate(common.TemplateHandlerBase):
    def dump(self, out_stream):
        if self._model.description is not None:
            out_stream.write(out_stream.meta_style(self._model.description))
        self._topology.dump(self._model.meta_data, out_stream, title='Metadata')
        self._topology.dump(self._model.node_templates, out_stream)
        self._topology.dump(self._model.group_templates, out_stream)
        self._topology.dump(self._model.policy_templates, out_stream)
        self._topology.dump(self._model.substitution_template, out_stream)
        self._topology.dump(self._model.inputs, out_stream, title='Inputs')
        self._topology.dump(self._model.outputs, out_stream, title='Outputs')
        self._topology.dump(self._model.workflow_templates, out_stream, title='Workflow templates')

    def coerce(self, **kwargs):
        self._coerce(self._model.meta_data,
                     self._model.node_templates,
                     self._model.group_templates,
                     self._model.policy_templates,
                     self._model.substitution_template,
                     self._model.inputs,
                     self._model.outputs,
                     self._model.workflow_templates,
                     **kwargs)

    def instantiate(self, instance_cls, inputs=None, plugins=None):                                 # pylint: disable=arguments-differ
        now = datetime.now()

        modeling_utils.validate_no_undeclared_inputs(
            declared_inputs=self._model.inputs, supplied_inputs=inputs or {})
        modeling_utils.validate_required_inputs_are_supplied(
            declared_inputs=self._model.inputs, supplied_inputs=inputs or {})

        service = instance_cls(
            created_at=now,
            updated_at=now,
            description=utils.deepcopy_with_locators(self._model.description),
            service_template=self._model,
            inputs=modeling_utils.merge_parameter_values(inputs, self._model.inputs)
        )

        for plugin_specification in self._model.plugin_specifications.itervalues():
            if plugin_specification.enabled and plugins:
                if self._resolve_plugin_specification(plugin_specification, plugins):
                    plugin = plugin_specification.plugin
                    service.plugins[plugin.name] = plugin
                else:
                    self._topology.report('specified plugin not found: {0}'.format(
                        plugin_specification.name), level=self._topology.Issue.EXTERNAL)
        service.meta_data = self._topology.instantiate(self._model.meta_data)

        for node_template in self._model.node_templates.itervalues():
            for _ in range(self._scaling(node_template)['default_instances']):
                node = self._topology.instantiate(node_template)
                service.nodes[node.name] = node

        service.groups = self._topology.instantiate(self._model.group_templates)
        service.policies = self._topology.instantiate(self._model.policy_templates)
        service.workflows = self._topology.instantiate(self._model.workflow_templates)
        service.substitution = self._topology.instantiate(self._model.substitution_template)
        service.outputs = self._topology.instantiate(self._model.outputs)

        return service

    @staticmethod
    def _resolve_plugin_specification(plugin_specification, plugins):
        matching_plugins = []
        if plugins:
            for plugin in plugins:
                if (plugin.name == plugin_specification.name and
                        (plugin_specification.version is None or
                         versions.VersionString(plugin.package_version) >=
                         plugin_specification.version)
                   ):
                    matching_plugins.append(plugin)
        plugin_specification.plugin = None
        if matching_plugins:
            # Return highest version of plugin
            plugin_specification.plugin = \
                max(matching_plugins,
                    key=lambda plugin: versions.VersionString(plugin.package_version).key)
        return plugin_specification.plugin is not None

    def _scaling(self, node_template):
        scaling = node_template.scaling

        if any([scaling['min_instances'] < 0,
                scaling['max_instances'] < scaling['min_instances'],
                scaling['max_instances'] < 0,

                scaling['default_instances'] < 0,
                scaling['default_instances'] < scaling['min_instances'],
                scaling['default_instances'] > scaling['max_instances']
               ]):
            self._topology.report(
                'invalid scaling parameters for node template "{0}": min={min_instances}, max='
                '{max_instances}, default={default_instances}'.format(self._model.name, **scaling),
                level=self._topology.Issue.BETWEEN_TYPES)

        return scaling

    def validate(self, **kwargs):
        self._validate(
            self._model.meta_data,
            self._model.node_templates,
            self._model.group_templates,
            self._model.policy_templates,
            self._model.substitution_template,
            self._model.inputs,
            self._model.outputs,
            self._model.workflow_templates,
            self._model.node_types,
            self._model.group_types,
            self._model.policy_types,
            self._model.relationship_types,
            self._model.capability_types,
            self._model.interface_types,
            self._model.artifact_types,
            **kwargs
        )


class ArtifactTemplate(common.TemplateHandlerBase):
    def dump(self, out_stream):
        out_stream.write(out_stream.node_style(self._model.name))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))
        with out_stream.indent():
            out_stream.write('Artifact type: {0}'.format(out_stream.type_style(
                self._model.type.name)))
            out_stream.write('Source path: {0}'.format(out_stream.literal_style(
                self._model.source_path)))
            if self._model.target_path is not None:
                out_stream.write('Target path: {0}'.format(out_stream.literal_style(
                    self._model.target_path)))
            if self._model.repository_url is not None:
                out_stream.write('Repository URL: {0}'.format(
                    out_stream.literal_style(self._model.repository_url)))
            if self._model.repository_credential:
                out_stream.write('Repository credential: {0}'.format(
                    out_stream.literal_style(self._model.repository_credential)))
            self._topology.dump(self._model.properties, out_stream, title='Properties')

    def coerce(self, **kwargs):
        self._topology.coerce(self._model.properties, **kwargs)

    def instantiate(self, instance_cls, **_):
        return instance_cls(
            name=self._model.name,
            type=self._model.type,
            description=utils.deepcopy_with_locators(self._model.description),
            source_path=self._model.source_path,
            target_path=self._model.target_path,
            repository_url=self._model.repository_url,
            repository_credential=self._model.repository_credential,
            artifact_template=self._model)

    def validate(self, **kwargs):
        self._topology.validate(self._model.properties, **kwargs)


class CapabilityTemplate(common.TemplateHandlerBase):
    def dump(self, out_stream):
        out_stream.write(out_stream.node_style(self._model.name))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))
        with out_stream.indent():
            out_stream.write('Type: {0}'.format(out_stream.type_style(self._model.type.name)))
            out_stream.write(
                'Occurrences: {0:d}{1}'.format(
                    self._model.min_occurrences or 0,
                    ' to {0:d}'.format(self._model.max_occurrences)
                    if self._model.max_occurrences is not None
                    else ' or more'))
            if self._model.valid_source_node_types:
                out_stream.write('Valid source node types: {0}'.format(
                    ', '.join((str(out_stream.type_style(v.name))
                               for v in self._model.valid_source_node_types))))
            self._topology.dump(self._model.properties, out_stream, title='Properties')

    def coerce(self, **kwargs):
        self._topology.coerce(self._model.properties, **kwargs)

    def instantiate(self, instance_cls, **_):
        return instance_cls(name=self._model.name,
                            type=self._model.type,
                            min_occurrences=self._model.min_occurrences,
                            max_occurrences=self._model.max_occurrences,
                            occurrences=0,
                            capability_template=self._model)

    def validate(self, **kwargs):
        self._topology.validate(self._model.properties, **kwargs)


class RequirementTemplate(common.TemplateHandlerBase):
    def dump(self, out_stream):
        if self._model.name:
            out_stream.write(out_stream.node_style(self._model.name))
        else:
            out_stream.write('Requirement:')
        with out_stream.indent():
            if self._model.target_node_type is not None:
                out_stream.write('Target node type: {0}'.format(
                    out_stream.type_style(self._model.target_node_type.name)))
            elif self._model.target_node_template is not None:
                out_stream.write('Target node template: {0}'.format(
                    out_stream.node_style(self._model.target_node_template.name)))
            if self._model.target_capability_type is not None:
                out_stream.write('Target capability type: {0}'.format(
                    out_stream.type_style(self._model.target_capability_type.name)))
            elif self._model.target_capability_name is not None:
                out_stream.write('Target capability name: {0}'.format(
                    out_stream.node_style(self._model.target_capability_name)))
            if self._model.target_node_template_constraints:
                out_stream.write('Target node template constraints:')
                with out_stream.indent():
                    for constraint in self._model.target_node_template_constraints:
                        out_stream.write(out_stream.literal_style(constraint))
            if self._model.relationship_template:
                out_stream.write('Relationship:')
                with out_stream.indent():
                    self._topology.dump(self._model.relationship_template, out_stream)

    def coerce(self, **kwargs):
        self._topology.coerce(self._model.relationship_template, **kwargs)

    def instantiate(self, instance_cls, **_):
        pass

    def validate(self, **kwargs):
        self._topology.validate(self._model.relationship_template, **kwargs)


class GroupTemplate(common.TemplateHandlerBase):
    def dump(self, out_stream):
        out_stream.write('Group template: {0}'.format(out_stream.node_style(self._model.name)))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))
        with out_stream.indent():
            out_stream.write('Type: {0}'.format(out_stream.type_style(self._model.type.name)))
            self._topology.dump(self._model.properties, out_stream, title='Properties')
            self._topology.dump(self._model.interface_templates, out_stream,
                                title='Interface Templates')
            if self._model.node_templates:
                out_stream.write('Member node templates: {0}'.format(', '.join(
                    (str(out_stream.node_style(v.name)) for v in self._model.node_templates))))

    def coerce(self, **kwargs):
        self._coerce(self._model.properties,
                     self._model.interface_templates,
                     **kwargs)

    def instantiate(self, instance_cls, **_):
        group = instance_cls(
            name=self._model.name,
            type=self._model.type,
            description=utils.deepcopy_with_locators(self._model.description),
            group_template=self._model)
        group.properties = self._topology.instantiate(self._model.properties)
        group.interfaces = self._topology.instantiate(self._model.interface_templates)
        if self._model.node_templates:
            for node_template in self._model.node_templates:
                group.nodes += node_template.nodes
        return group

    def validate(self, **kwargs):
        self._validate(self._model.properties,
                       self._model.interface_templates,
                       **kwargs)


class InterfaceTemplate(common.TemplateHandlerBase):
    def dump(self, out_stream):
        out_stream.write(out_stream.node_style(self._model.name))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))
        with out_stream.indent():
            out_stream.write('Interface type: {0}'.format(out_stream.type_style(
                self._model.type.name)))
            self._topology.dump(self._model.inputs, out_stream, title='Inputs')
            self._topology.dump(self._model.operation_templates, out_stream,
                                title='Operation templates')

    def coerce(self, **kwargs):
        self._coerce(self._model.inputs,
                     self._model.operation_templates,
                     **kwargs)

    def instantiate(self, instance_cls, **_):
        interface = instance_cls(
            name=self._model.name,
            type=self._model.type,
            description=utils.deepcopy_with_locators(self._model.description),
            interface_template=self._model)
        interface.inputs = self._topology.instantiate(self._model.inputs)
        interface.operations = self._topology.instantiate(self._model.operation_templates)
        return interface

    def validate(self, **kwargs):
        self._validate(self._model.inputs,
                       self._model.operation_templates,
                       **kwargs)


class NodeTemplate(common.TemplateHandlerBase):
    def dump(self, out_stream):
        out_stream.write('Node template: {0}'.format(out_stream.node_style(self._model.name)))
        with out_stream.indent():
            if self._model.description:
                out_stream.write(out_stream.meta_style(self._model.description))
            out_stream.write('Type: {0}'.format(out_stream.type_style(self._model.type.name)))
            self._topology.dump(self._model.properties, out_stream, title='Properties')
            self._topology.dump(self._model.attributes, out_stream, title='Attributes')
            self._topology.dump(
                self._model.interface_templates, out_stream, title='Interface Templates')
            self._topology.dump(
                self._model.artifact_templates, out_stream, title='Artifact Templates')
            self._topology.dump(
                self._model.capability_templates, out_stream, title='Capability Templates')
            self._topology.dump(
                self._model.requirement_templates, out_stream, title='Requirement Templates')

    def coerce(self, **kwargs):
        self._coerce(self._model.properties,
                     self._model.attributes,
                     self._model.interface_templates,
                     self._model.artifact_templates,
                     self._model.capability_templates,
                     self._model.requirement_templates,
                     **kwargs)

    def instantiate(self, instance_cls, **_):
        node = instance_cls(
            name=self._model._next_name,
            type=self._model.type,
            description=utils.deepcopy_with_locators(self._model.description),
            node_template=self._model
        )

        node.properties = self._topology.instantiate(self._model.properties)
        node.attributes = self._topology.instantiate(self._model.attributes)
        node.interfaces = self._topology.instantiate(self._model.interface_templates)
        node.artifacts = self._topology.instantiate(self._model.artifact_templates)
        node.capabilities = self._topology.instantiate(self._model.capability_templates)

        # Default attributes
        if 'tosca_name' in node.attributes and node.attributes['tosca_name'].type_name == 'string':
            node.attributes['tosca_name'].value = self._model.name
        if 'tosca_id' in node.attributes and node.attributes['tosca_id'].type_name == 'string':
            node.attributes['tosca_id'].value = node.name

        return node

    def validate(self, **kwargs):
        self._validate(self._model.properties,
                       self._model.attributes,
                       self._model.interface_templates,
                       self._model.artifact_templates,
                       self._model.capability_templates,
                       self._model.requirement_templates,
                       **kwargs)


class PolicyTemplate(common.TemplateHandlerBase):
    def dump(self, out_stream):
        out_stream.write('Policy template: {0}'.format(out_stream.node_style(self._model.name)))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))
        with out_stream.indent():
            out_stream.write('Type: {0}'.format(out_stream.type_style(self._model.type.name)))
            self._topology.dump(self._model.properties, out_stream, title='Properties')
            if self._model.node_templates:
                out_stream.write('Target node templates: {0}'.format(', '.join(
                    (str(out_stream.node_style(v.name)) for v in self._model.node_templates))))
            if self._model.group_templates:
                out_stream.write('Target group templates: {0}'.format(', '.join(
                    (str(out_stream.node_style(v.name)) for v in self._model.group_templates))))

    def coerce(self, **kwargs):
        self._topology.coerce(self._model.properties, **kwargs)

    def instantiate(self, instance_cls, **_):
        policy = instance_cls(
            name=self._model.name,
            type=self._model.type,
            description=utils.deepcopy_with_locators(self._model.description),
            policy_template=self._model)

        policy.properties = self._topology.instantiate(self._model.properties)
        if self._model.node_templates:
            for node_template in self._model.node_templates:
                policy.nodes += node_template.nodes
        if self._model.group_templates:
            for group_template in self._model.group_templates:
                policy.groups += group_template.groups
        return policy

    def validate(self, **kwargs):
        self._topology.validate(self._model.properties, **kwargs)


class SubstitutionTemplate(common.TemplateHandlerBase):

    def dump(self, out_stream):
        out_stream.write('Substitution template:')
        with out_stream.indent():
            out_stream.write('Node type: {0}'.format(out_stream.type_style(
                self._model.node_type.name)))
            self._topology.dump(self._model.mappings, out_stream, title='Mappings')

    def coerce(self, **kwargs):
        self._topology.coerce(self._model.mappings, **kwargs)

    def instantiate(self, instance_cls, **_):
        return instance_cls(node_type=self._model.node_type, substitution_template=self._model)

    def validate(self, **kwargs):
        self._topology.validate(self._model.mappings, **kwargs)


class SubstitutionTemplateMapping(common.TemplateHandlerBase):

    def dump(self, out_stream):
        if self._topology.capability_template is not None:
            node_template = self._model.capability_template.node_template
        else:
            node_template = self._model.requirement_template.node_template
        out_stream.write('{0} -> {1}.{2}'.format(
            out_stream.node_style(self._model.name),
            out_stream.node_style(node_template.name),
            out_stream.node_style(self._model.capability_template.name
                                  if self._model.capability_template
                                  else self._model.requirement_template.name)))

    def coerce(self, **_):
        pass

    def instantiate(self, instance_cls, **_):
        substitution_mapping = instance_cls(
            name=self._model.name,
            requirement_template=self._model.requirement_template)

        if self._model.capability_template is not None:
            node_template = self._model.capability_template.node_template
        else:
            node_template = self._model.requirement_template.node_template
        nodes = node_template.nodes
        if len(nodes) == 0:
            self._topology.report(
                'mapping "{0}" refers to node template "{1}" but there are no node instances'.
                format(self._model.mapped_name, self._model.node_template.name),
                level=self._topology.Issue.BETWEEN_INSTANCES)
            return None
        # The TOSCA spec does not provide a way to choose the node,
        # so we will just pick the first one
        substitution_mapping.node_style = nodes[0]
        if self._model.capability_template:
            for a_capability in substitution_mapping.node_style.capabilities.itervalues():
                if a_capability.capability_template.name == \
                        self._model.capability_template.name:
                    substitution_mapping.capability = a_capability

        return substitution_mapping

    def validate(self, **_):
        if self._model.capability_template is None and self._model.requirement_template is None:
            self._topology.report(
                'mapping "{0}" refers to neither capability nor a requirement '
                'in node template: {1}'.format(
                    self._model.name, formatting.safe_repr(self._model.node_template.name)),
                level=self._topology.Issue.BETWEEN_TYPES)


class RelationshipTemplate(common.TemplateHandlerBase):
    def dump(self, out_stream):
        if self._model.type is not None:
            out_stream.write('Relationship type: {0}'.format(out_stream.type_style(
                self._model.type.name)))
        else:
            out_stream.write('Relationship template: {0}'.format(
                out_stream.node_style(self._model.name)))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))
        with out_stream.indent():
            self._topology.dump(self._model.properties, out_stream, title='Properties')
            self._topology.dump(self._model.interface_templates, out_stream,
                                title='Interface Templates')

    def coerce(self, **kwargs):
        self._coerce(self._model.properties, self._model.interface_templates, **kwargs)

    def instantiate(self, instance_cls, **_):
        relationship = instance_cls(
            name=self._model.name,
            type=self._model.type,
            relationship_template=self._model)

        relationship.properties = self._topology.instantiate(self._model.properties)
        relationship.interfaces = self._topology.instantiate(self._model.interface_templates)
        return relationship

    def validate(self, **kwargs):
        self._validate(self._model.properties, self._model.interface_templates, **kwargs)


class OperationTemplate(common.TemplateHandlerBase):

    def dump(self, out_stream):
        out_stream.write(out_stream.node_style(self._model.name))
        if self._model.description:
            out_stream.write(out_stream.meta_style(self._model.description))
        with out_stream.indent():
            if self._model.implementation is not None:
                out_stream.write('Implementation: {0}'.format(
                    out_stream.literal_style(self._model.implementation)))
            if self._model.dependencies:
                out_stream.write('Dependencies: {0}'.format(', '.join(
                    (str(out_stream.literal_style(v)) for v in self._model.dependencies))))
            self._topology.dump(self._model.inputs, out_stream, title='Inputs')
            if self._model.executor is not None:
                out_stream.write('Executor: {0}'.format(
                    out_stream.literal_style(self._model.executor)))
            if self._model.max_attempts is not None:
                out_stream.write('Max attempts: {0}'.format(out_stream.literal_style(
                    self._model.max_attempts)))
            if self._model.retry_interval is not None:
                out_stream.write('Retry interval: {0}'.format(
                    out_stream.literal_style(self._model.retry_interval)))
            if self._model.plugin_specification is not None:
                out_stream.write('Plugin specification: {0}'.format(
                    out_stream.literal_style(self._model.plugin_specification.name)))
            self._topology.dump(self._model.configurations, out_stream, title='Configuration')
            if self._model.function is not None:
                out_stream.write('Function: {0}'.format(out_stream.literal_style(
                    self._model.function)))

    def coerce(self, **kwargs):
        self._coerce(self._model.inputs,
                     self._model.configurations,
                     **kwargs)

    def instantiate(self, instance_cls, **_):
        operation = instance_cls(
            name=self._model.name,
            description=utils.deepcopy_with_locators(self._model.description),
            relationship_edge=self._model.relationship_edge,
            implementation=self._model.implementation,
            dependencies=self._model.dependencies,
            executor=self._model.executor,
            function=self._model.function,
            max_attempts=self._model.max_attempts,
            retry_interval=self._model.retry_interval,
            operation_template=self._model)

        if (self._model.plugin_specification is not None and
                self._model.plugin_specification.enabled):
            operation.plugin = self._model.plugin_specification.plugin

        operation.inputs = self._topology.instantiate(self._model.inputs)
        operation.configurations = self._topology.instantiate(self._model.configurations)

        return operation

    def validate(self, **kwargs):
        self._validate(self._model.inputs,
                       self._model.configurations,
                       **kwargs)


class PluginSpecification(common.HandlerBase):
    def validate(self, **kwargs):
        pass

    def coerce(self, **kwargs):
        pass

    def instantiate(self, **_):
        pass

    def dump(self, out_stream):
        pass
