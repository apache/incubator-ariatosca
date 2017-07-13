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

from ...parser.validation import issue
from ...modeling import models
from ...utils import console
from . import (
    template_handler,
    instance_handler,
    common
)


class Topology(issue.ReporterMixin):

    _init_map = {
        models.ServiceTemplate: models.Service,
        models.ArtifactTemplate: models.Artifact,
        models.CapabilityTemplate: models.Capability,
        models.GroupTemplate: models.Group,
        models.InterfaceTemplate: models.Interface,
        models.NodeTemplate: models.Node,
        models.PolicyTemplate: models.Policy,
        models.SubstitutionTemplate: models.Substitution,
        models.RelationshipTemplate: models.Relationship,
        models.OperationTemplate: models.Operation,
        models.SubstitutionTemplateMapping: models.SubstitutionMapping,

        # Common
        models.Metadata: models.Metadata,
        models.Attribute: models.Attribute,
        models.Property: models.Property,
        models.Input: models.Input,
        models.Output: models.Output,
        models.Configuration: models.Configuration,
        models.Argument: models.Argument,
        models.Type: models.Type
    }

    def __init__(self, *args, **kwargs):
        super(Topology, self).__init__(*args, **kwargs)
        self._model_cls_to_handler = dict(self._init_handlers(instance_handler),
                                          **self._init_handlers(template_handler))

    @staticmethod
    def _init_handlers(module_):
        """
        Register handlers from a handler module to the models

        :param module_: The module to look for handlers
        :return: a dict where the key is the models class, and the value is the handler class
        associated with it from the provided module
        """
        handlers = {}
        for attribute_name in dir(module_):
            if attribute_name.startswith('_'):
                continue
            attribute = getattr(module_, attribute_name)
            if isinstance(attribute, type) and issubclass(attribute, common.HandlerBase):
                handlers[getattr(models, attribute_name)] = attribute
        return handlers

    def instantiate(self, model, **kwargs):
        """
        instantiate the provided model

        :param model:
        :param kwargs:
        :return:
        """
        if isinstance(model, dict):
            return dict((name, self.instantiate(value, **kwargs))
                        for name, value in model.iteritems())
        elif isinstance(model, list):
            return list(self.instantiate(value, **kwargs) for value in model)
        elif model is not None:
            _handler = self._model_cls_to_handler[model.__class__]
            model_instance_cls = self._init_map[model.__class__]
            return _handler(self, model).instantiate(model_instance_cls, **kwargs)

    def validate(self, model, **kwargs):
        if isinstance(model, dict):
            return self.validate(model.values(), **kwargs)
        elif isinstance(model, list):
            return all(self.validate(value, **kwargs) for value in model)
        elif model is not None:
            _handler = self._model_cls_to_handler[model.__class__]
            return _handler(self, model).validate(**kwargs)

    def dump(self, model, out_stream=None, title=None, **kwargs):
        out_stream = out_stream or console.TopologyStylizer()

        # if model is empty, no need to print out the section name
        if model and title:
            out_stream.write('{0}:'.format(title))

        if isinstance(model, dict):
            if str(out_stream):
                with out_stream.indent():
                    return self.dump(model.values(), out_stream=out_stream, **kwargs)
            else:
                return self.dump(model.values(), out_stream=out_stream, **kwargs)

        elif isinstance(model, list):
            for value in model:
                self.dump(value, out_stream=out_stream, **kwargs)

        elif model is not None:
            _handler = self._model_cls_to_handler[model.__class__]
            _handler(self, model).dump(out_stream=out_stream, **kwargs)

        return out_stream

    def dump_graph(self, service):
        out_stream = console.TopologyStylizer()
        for node in service.nodes.itervalues():
            if not node.inbound_relationships:
                self._dump_graph_node(out_stream, node)
        return out_stream

    def _dump_graph_node(self, out_stream, node, capability=None):
        out_stream.write(out_stream.node_style(node.name))
        if capability is not None:
            out_stream.write('{0} ({1})'.format(out_stream.property_style(capability.name),
                                                out_stream.type_style(capability.type.name)))
        if node.outbound_relationships:
            with out_stream.indent():
                for relationship_model in node.outbound_relationships:
                    styled_relationship_name = out_stream.property_style(relationship_model.name)
                    if relationship_model.type is not None:
                        out_stream.write('-> {0} ({1})'.format(
                            styled_relationship_name,
                            out_stream.type_style(relationship_model.type.name)))
                    else:
                        out_stream.write('-> {0}'.format(styled_relationship_name))
                    with out_stream.indent(3):
                        self._dump_graph_node(out_stream,
                                              relationship_model.target_node,
                                              relationship_model.target_capability)

    def coerce(self, model, **kwargs):
        if isinstance(model, dict):
            return self.coerce(model.values(), **kwargs)
        elif isinstance(model, list):
            return all(self.coerce(value, **kwargs) for value in model)
        elif model is not None:
            _handler = self._model_cls_to_handler[model.__class__]
            return _handler(self, model).coerce(**kwargs)

    def dump_types(self, service_template, out_stream=None):
        out_stream = out_stream or console.TopologyStylizer()
        self.dump(service_template.node_types, out_stream, 'Node types')
        self.dump(service_template.group_types, out_stream, 'Group types')
        self.dump(service_template.capability_types, out_stream, 'Capability types')
        self.dump(service_template.relationship_types, out_stream, 'Relationship types')
        self.dump(service_template.policy_types, out_stream, 'Policy types')
        self.dump(service_template.artifact_types, out_stream, 'Artifact types')
        self.dump(service_template.interface_types, out_stream, 'Interface types')

        return out_stream

    def satisfy_requirements(self, model, **kwargs):
        if isinstance(model, dict):
            return self.satisfy_requirements(model.values(), **kwargs)
        elif isinstance(model, list):
            return all(self.satisfy_requirements(value, **kwargs) for value in model)
        elif model is not None:
            _handler = self._model_cls_to_handler[model.__class__]
            return _handler(self, model).satisfy_requirements(**kwargs)

    def validate_capabilities(self, model, **kwargs):
        if isinstance(model, dict):
            return self.validate_capabilities(model.values(), **kwargs)
        elif isinstance(model, list):
            return all(self.validate_capabilities(value, **kwargs) for value in model)
        elif model is not None:
            _handler = self._model_cls_to_handler[model.__class__]
            return _handler(self, model).validate_capabilities(**kwargs)

    def _find_host(self, node):
        if node.type.role == 'host':
            return node

        def target_has_role(rel, role):
            return (rel.target_capability is not None and
                    rel.target_capability.type.role == role)

        for outbound_relationship in node.outbound_relationships:
            if target_has_role(outbound_relationship, 'host'):
                host = self._find_host(outbound_relationship.target_node)
                if host is not None:
                    return host
        for inbound_relationship in node.inbound_relationships:
            if target_has_role(inbound_relationship, 'feature'):
                host = self._find_host(inbound_relationship.source_node)
                if host is not None:
                    return host
        return None

    def assign_hosts(self, service):
        for node in service.nodes.values():
            node.host = self._find_host(node)

    def configure_operations(self, model, **kwargs):
        if isinstance(model, dict):
            return self.configure_operations(model.values(), **kwargs)
        elif isinstance(model, list):
            return all(self.configure_operations(value, **kwargs) for value in model)
        elif model is not None:
            _handler = self._model_cls_to_handler[model.__class__]
            return _handler(self, model).configure_operations(**kwargs)
