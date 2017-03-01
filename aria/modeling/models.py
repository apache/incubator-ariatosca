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
    service_template,
    service,
    orchestration,
    bases,
)

__all__ = (
    'aria_declarative_base',

    # Service template models
    'ServiceTemplate',
    'NodeTemplate',
    'GroupTemplate',
    'PolicyTemplate',
    'SubstitutionTemplate',
    'SubstitutionTemplateMapping',
    'RequirementTemplate',
    'RelationshipTemplate',
    'CapabilityTemplate',
    'InterfaceTemplate',
    'OperationTemplate',
    'ArtifactTemplate',

    # Service template and instance models
    'Parameter',
    'Metadata',

    # Service instance models
    'Service',
    'Node',
    'Group',
    'Policy',
    'Substitution',
    'SubstitutionMapping',
    'Relationship',
    'Capability',
    'Interface',
    'Operation',
    'Artifact',

    # Orchestrator models
    'Execution',
    'ServiceUpdate',
    'ServiceUpdateStep',
    'ServiceModification',
    'Plugin',
    'Task'
)

aria_declarative_base = declarative_base(cls=bases.ModelIDMixin)

# pylint: disable=abstract-method


# region service template models

class ServiceTemplate(aria_declarative_base, service_template.ServiceTemplateBase):
    pass


class NodeTemplate(aria_declarative_base, service_template.NodeTemplateBase):
    pass


class GroupTemplate(aria_declarative_base, service_template.GroupTemplateBase):
    pass


class PolicyTemplate(aria_declarative_base, service_template.PolicyTemplateBase):
    pass


class SubstitutionTemplate(aria_declarative_base, service_template.SubstitutionTemplateBase):
    pass


class SubstitutionTemplateMapping(aria_declarative_base,
                                  service_template.SubstitutionTemplateMappingBase):
    pass


class RequirementTemplate(aria_declarative_base, service_template.RequirementTemplateBase):
    pass


class RelationshipTemplate(aria_declarative_base, service_template.RelationshipTemplateBase):
    pass


class CapabilityTemplate(aria_declarative_base, service_template.CapabilityTemplateBase):
    pass


class InterfaceTemplate(aria_declarative_base, service_template.InterfaceTemplateBase):
    pass


class OperationTemplate(aria_declarative_base, service_template.OperationTemplateBase):
    pass


class ArtifactTemplate(aria_declarative_base, service_template.ArtifactTemplateBase):
    pass

# endregion


# region service template and instance models

class Parameter(aria_declarative_base, service_template.ParameterBase):
    pass


class Metadata(aria_declarative_base, service_template.MetadataBase):
    pass

# endregion


# region service instance models

class Service(aria_declarative_base, service.ServiceBase):
    pass


class Node(aria_declarative_base, service.NodeBase):
    pass


class Group(aria_declarative_base, service.GroupBase):
    pass


class Policy(aria_declarative_base, service.PolicyBase):
    pass


class Substitution(aria_declarative_base, service.SubstitutionBase):
    pass


class SubstitutionMapping(aria_declarative_base, service.SubstitutionMappingBase):
    pass


class Relationship(aria_declarative_base, service.RelationshipBase):
    pass


class Capability(aria_declarative_base, service.CapabilityBase):
    pass


class Interface(aria_declarative_base, service.InterfaceBase):
    pass


class Operation(aria_declarative_base, service.OperationBase):
    pass


class Artifact(aria_declarative_base, service.ArtifactBase):
    pass

# endregion


# region orchestration models

class Execution(aria_declarative_base, orchestration.Execution):
    pass


class ServiceUpdate(aria_declarative_base, orchestration.ServiceUpdateBase):
    pass


class ServiceUpdateStep(aria_declarative_base, orchestration.ServiceUpdateStepBase):
    pass


class ServiceModification(aria_declarative_base, orchestration.ServiceModificationBase):
    pass


class Plugin(aria_declarative_base, orchestration.PluginBase):
    pass


class Task(aria_declarative_base, orchestration.TaskBase):
    pass

# endregion
