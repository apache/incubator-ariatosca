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

from sqlalchemy.ext.declarative import declarative_base

from . import (
    template_elements,
    instance_elements,
    orchestrator_elements,
    elements,
    structure,
)

__all__ = (
    'aria_declarative_base',

    'Parameter',
    'Metadata',

    'MappingTemplate',
    'InterfaceTemplate',
    'OperationTemplate',
    'ServiceTemplate',
    'NodeTemplate',
    'GroupTemplate',
    'ArtifactTemplate',
    'PolicyTemplate',
    'RequirementTemplate',
    'CapabilityTemplate',
    'RelationshipTemplate',

    'Mapping',
    'Substitution',
    'ServiceInstance',
    'Node',
    'Relationship',
    'Artifact',
    'Group',
    'Interface',
    'Operation',
    'Capability',
    'Policy',

    'Execution',
    'ServiceInstanceUpdate',
    'ServiceInstanceUpdateStep',
    'ServiceInstanceModification',
    'Plugin',
    'Task'
)

aria_declarative_base = declarative_base(cls=structure.ModelIDMixin)

# pylint: disable=abstract-method


# region elements

class Parameter(aria_declarative_base, elements.ParameterBase):
    pass


class Metadata(aria_declarative_base, elements.MetadataBase):
    pass


# endregion

# region template models


class MappingTemplate(aria_declarative_base, template_elements.MappingTemplateBase):
    pass


class SubstitutionTemplate(aria_declarative_base, template_elements.SubstitutionTemplateBase):
    pass


class InterfaceTemplate(aria_declarative_base, template_elements.InterfaceTemplateBase):
    pass


class OperationTemplate(aria_declarative_base, template_elements.OperationTemplateBase):
    pass


class ServiceTemplate(aria_declarative_base, template_elements.ServiceTemplateBase):
    pass


class NodeTemplate(aria_declarative_base, template_elements.NodeTemplateBase):
    pass


class GroupTemplate(aria_declarative_base, template_elements.GroupTemplateBase):
    pass


class ArtifactTemplate(aria_declarative_base, template_elements.ArtifactTemplateBase):
    pass


class PolicyTemplate(aria_declarative_base, template_elements.PolicyTemplateBase):
    pass


class RequirementTemplate(aria_declarative_base, template_elements.RequirementTemplateBase):
    pass


class CapabilityTemplate(aria_declarative_base, template_elements.CapabilityTemplateBase):
    pass


class RelationshipTemplate(aria_declarative_base, template_elements.RelationshipTemplateBase):
    pass

# endregion


# region instance models

class Mapping(aria_declarative_base, instance_elements.MappingBase):
    pass


class Substitution(aria_declarative_base, instance_elements.SubstitutionBase):
    pass


class ServiceInstance(aria_declarative_base, instance_elements.ServiceInstanceBase):
    pass


class Node(aria_declarative_base, instance_elements.NodeBase):
    pass


class Relationship(aria_declarative_base, instance_elements.RelationshipBase):
    pass


class Artifact(aria_declarative_base, instance_elements.ArtifactBase):
    pass


class Group(aria_declarative_base, instance_elements.GroupBase):
    pass


class Interface(aria_declarative_base, instance_elements.InterfaceBase):
    pass


class Operation(aria_declarative_base, instance_elements.OperationBase):
    pass


class Capability(aria_declarative_base, instance_elements.CapabilityBase):
    pass


class Policy(aria_declarative_base, instance_elements.PolicyBase):
    pass


# endregion


# region orchestrator models

class Execution(aria_declarative_base, orchestrator_elements.Execution):
    pass


class ServiceInstanceUpdate(aria_declarative_base,
                            orchestrator_elements.ServiceInstanceUpdateBase):
    pass


class ServiceInstanceUpdateStep(aria_declarative_base,
                                orchestrator_elements.ServiceInstanceUpdateStepBase):
    pass


class ServiceInstanceModification(aria_declarative_base,
                                  orchestrator_elements.ServiceInstanceModificationBase):
    pass


class Plugin(aria_declarative_base, orchestrator_elements.PluginBase):
    pass


class Task(aria_declarative_base, orchestrator_elements.TaskBase):
    pass

# endregion