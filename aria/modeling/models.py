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

# pylint: disable=abstract-method

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Text
)

from . import (
    service_template,
    service_instance,
    service_changes,
    service_common,
    orchestration,
    mixins,
)

aria_declarative_base = declarative_base(cls=mixins.ModelIDMixin)


# See also models_to_register at the bottom of this file
__all__ = (
    'aria_declarative_base',
    'models_to_register',

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
    'PluginSpecification',

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

    # Service changes models
    'ServiceUpdate',
    'ServiceUpdateStep',
    'ServiceModification',

    # Common service models
    'Parameter',
    'Type',
    'Metadata',

    # Orchestration models
    'Execution',
    'Plugin',
    'Task',
    'Log'
)


# region service template models

class ServiceTemplate(aria_declarative_base, service_template.ServiceTemplateBase):
    name = Column(Text, index=True, unique=True)


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

class PluginSpecification(aria_declarative_base, service_template.PluginSpecificationBase):
    pass

# endregion


# region service instance models

class Service(aria_declarative_base, service_instance.ServiceBase):
    name = Column(Text, index=True, unique=True)


class Node(aria_declarative_base, service_instance.NodeBase):
    pass


class Group(aria_declarative_base, service_instance.GroupBase):
    pass


class Policy(aria_declarative_base, service_instance.PolicyBase):
    pass


class Substitution(aria_declarative_base, service_instance.SubstitutionBase):
    pass


class SubstitutionMapping(aria_declarative_base, service_instance.SubstitutionMappingBase):
    pass


class Relationship(aria_declarative_base, service_instance.RelationshipBase):
    pass


class Capability(aria_declarative_base, service_instance.CapabilityBase):
    pass


class Interface(aria_declarative_base, service_instance.InterfaceBase):
    pass


class Operation(aria_declarative_base, service_instance.OperationBase):
    pass


class Artifact(aria_declarative_base, service_instance.ArtifactBase):
    pass

# endregion


# region service changes models

class ServiceUpdate(aria_declarative_base, service_changes.ServiceUpdateBase):
    pass


class ServiceUpdateStep(aria_declarative_base, service_changes.ServiceUpdateStepBase):
    pass


class ServiceModification(aria_declarative_base, service_changes.ServiceModificationBase):
    pass

# endregion


# region common service models

class Parameter(aria_declarative_base, service_common.ParameterBase):
    pass


class Type(aria_declarative_base, service_common.TypeBase):
    pass


class Metadata(aria_declarative_base, service_common.MetadataBase):
    pass

# endregion


# region orchestration models

class Execution(aria_declarative_base, orchestration.ExecutionBase):
    pass


class Plugin(aria_declarative_base, orchestration.PluginBase):
    pass


class Task(aria_declarative_base, orchestration.TaskBase):
    pass


class Log(aria_declarative_base, orchestration.LogBase):
    pass

# endregion


# See also __all__ at the top of this file
models_to_register = [
    # Service template models
    ServiceTemplate,
    NodeTemplate,
    GroupTemplate,
    PolicyTemplate,
    SubstitutionTemplate,
    SubstitutionTemplateMapping,
    RequirementTemplate,
    RelationshipTemplate,
    CapabilityTemplate,
    InterfaceTemplate,
    OperationTemplate,
    ArtifactTemplate,
    PluginSpecification,

    # Service instance models
    Service,
    Node,
    Group,
    Policy,
    SubstitutionMapping,
    Substitution,
    Relationship,
    Capability,
    Interface,
    Operation,
    Artifact,

    # Service changes models
    ServiceUpdate,
    ServiceUpdateStep,
    ServiceModification,

    # Common service models
    Parameter,
    Type,
    Metadata,

    # Orchestration models
    Execution,
    Plugin,
    Task,
    Log
]
