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
    service_template_models,
    service_instance_models,
    orchestrator_models,
    shared_service_models,
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


# region shared service models

class Parameter(aria_declarative_base, shared_service_models.ParameterBase):
    pass


class Metadata(aria_declarative_base, shared_service_models.MetadataBase):
    pass

# endregion


# region service template models

class MappingTemplate(aria_declarative_base, service_template_models.MappingTemplateBase):
    pass


class SubstitutionTemplate(aria_declarative_base, service_template_models.SubstitutionTemplateBase):
    pass


class InterfaceTemplate(aria_declarative_base, service_template_models.InterfaceTemplateBase):
    pass


class OperationTemplate(aria_declarative_base, service_template_models.OperationTemplateBase):
    pass


class ServiceTemplate(aria_declarative_base, service_template_models.ServiceTemplateBase):
    pass


class NodeTemplate(aria_declarative_base, service_template_models.NodeTemplateBase):
    pass


class GroupTemplate(aria_declarative_base, service_template_models.GroupTemplateBase):
    pass


class ArtifactTemplate(aria_declarative_base, service_template_models.ArtifactTemplateBase):
    pass


class PolicyTemplate(aria_declarative_base, service_template_models.PolicyTemplateBase):
    pass


class RequirementTemplate(aria_declarative_base, service_template_models.RequirementTemplateBase):
    pass


class CapabilityTemplate(aria_declarative_base, service_template_models.CapabilityTemplateBase):
    pass


class RelationshipTemplate(aria_declarative_base, service_template_models.RelationshipTemplateBase):
    pass

# endregion


# region service instance models

class Mapping(aria_declarative_base, service_instance_models.MappingBase):
    pass


class Substitution(aria_declarative_base, service_instance_models.SubstitutionBase):
    pass


class ServiceInstance(aria_declarative_base, service_instance_models.ServiceInstanceBase):
    pass


class Node(aria_declarative_base, service_instance_models.NodeBase):
    pass


class Relationship(aria_declarative_base, service_instance_models.RelationshipBase):
    pass


class Artifact(aria_declarative_base, service_instance_models.ArtifactBase):
    pass


class Group(aria_declarative_base, service_instance_models.GroupBase):
    pass


class Interface(aria_declarative_base, service_instance_models.InterfaceBase):
    pass


class Operation(aria_declarative_base, service_instance_models.OperationBase):
    pass


class Capability(aria_declarative_base, service_instance_models.CapabilityBase):
    pass


class Policy(aria_declarative_base, service_instance_models.PolicyBase):
    pass

# endregion


# region orchestrator models

class Execution(aria_declarative_base, orchestrator_models.Execution):
    pass


class ServiceInstanceUpdate(aria_declarative_base,
                            orchestrator_models.ServiceInstanceUpdateBase):
    pass


class ServiceInstanceUpdateStep(aria_declarative_base,
                                orchestrator_models.ServiceInstanceUpdateStepBase):
    pass


class ServiceInstanceModification(aria_declarative_base,
                                  orchestrator_models.ServiceInstanceModificationBase):
    pass


class Plugin(aria_declarative_base, orchestrator_models.PluginBase):
    pass


class Task(aria_declarative_base, orchestrator_models.TaskBase):
    pass

# endregion
