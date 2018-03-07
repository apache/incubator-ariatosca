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
Data models.

Type definition models
-----------------------

.. autosummary::
   :nosignatures:

   aria.modeling.models.TypeDefinition

Service template models
-----------------------

.. autosummary::
   :nosignatures:

   aria.modeling.models.ServiceTemplate
   aria.modeling.models.NodeTemplate
   aria.modeling.models.GroupTemplate
   aria.modeling.models.PolicyTemplate
   aria.modeling.models.SubstitutionTemplate
   aria.modeling.models.SubstitutionTemplateMapping
   aria.modeling.models.RequirementTemplate
   aria.modeling.models.RelationshipTemplate
   aria.modeling.models.CapabilityTemplate
   aria.modeling.models.InterfaceTemplate
   aria.modeling.models.OperationTemplate
   aria.modeling.models.ArtifactTemplate
   aria.modeling.models.PluginSpecification

Service instance models
-----------------------

.. autosummary::
   :nosignatures:

   aria.modeling.models.Service
   aria.modeling.models.Node
   aria.modeling.models.Group
   aria.modeling.models.Policy
   aria.modeling.models.Substitution
   aria.modeling.models.SubstitutionMapping
   aria.modeling.models.Relationship
   aria.modeling.models.Capability
   aria.modeling.models.Interface
   aria.modeling.models.Operation
   aria.modeling.models.Artifact

Common models
-------------

.. autosummary::
   :nosignatures:

   aria.modeling.models.Output
   aria.modeling.models.Input
   aria.modeling.models.Configuration
   aria.modeling.models.Property
   aria.modeling.models.Attribute
   aria.modeling.models.Type
   aria.modeling.models.Metadata

Orchestration models
--------------------

.. autosummary::
   :nosignatures:

   aria.modeling.models.Execution
   aria.modeling.models.Task
   aria.modeling.models.Log
   aria.modeling.models.Plugin
   aria.modeling.models.Argument
"""

# pylint: disable=abstract-method

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Text
)

from . import (
    type_definition,
    service_template,
    service_instance,
    service_changes,
    service_common,
    orchestration,
    mixins,
    utils
)


aria_declarative_base = declarative_base(cls=mixins.ModelIDMixin)


# See also models_to_register at the bottom of this file
__all__ = (
    'models_to_register',

    # Type definition models
    'TypeDefinition',

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
    'Input',
    'Configuration',
    'Output',
    'Property',
    'Attribute',
    'Type',
    'Metadata',

    # Orchestration models
    'Execution',
    'Plugin',
    'Task',
    'Log',
    'Argument'
)

# region type definition models

@utils.fix_doc
class TypeDefinition(aria_declarative_base, type_definition.TypeDefinitionBase):
    pass

# region service template models

@utils.fix_doc
class ServiceTemplate(aria_declarative_base, service_template.ServiceTemplateBase):
    name = Column(Text, index=True, unique=True)


@utils.fix_doc
class NodeTemplate(aria_declarative_base, service_template.NodeTemplateBase):
    pass


@utils.fix_doc
class GroupTemplate(aria_declarative_base, service_template.GroupTemplateBase):
    pass


@utils.fix_doc
class PolicyTemplate(aria_declarative_base, service_template.PolicyTemplateBase):
    pass


@utils.fix_doc
class SubstitutionTemplate(aria_declarative_base, service_template.SubstitutionTemplateBase):
    pass


@utils.fix_doc
class SubstitutionTemplateMapping(aria_declarative_base,
                                  service_template.SubstitutionTemplateMappingBase):
    pass


@utils.fix_doc
class RequirementTemplate(aria_declarative_base, service_template.RequirementTemplateBase):
    pass


@utils.fix_doc
class RelationshipTemplate(aria_declarative_base, service_template.RelationshipTemplateBase):
    pass


@utils.fix_doc
class CapabilityTemplate(aria_declarative_base, service_template.CapabilityTemplateBase):
    pass


@utils.fix_doc
class InterfaceTemplate(aria_declarative_base, service_template.InterfaceTemplateBase):
    pass


@utils.fix_doc
class OperationTemplate(aria_declarative_base, service_template.OperationTemplateBase):
    pass


@utils.fix_doc
class ArtifactTemplate(aria_declarative_base, service_template.ArtifactTemplateBase):
    pass


@utils.fix_doc
class PluginSpecification(aria_declarative_base, service_template.PluginSpecificationBase):
    pass

# endregion


# region service instance models

@utils.fix_doc
class Service(aria_declarative_base, service_instance.ServiceBase):
    name = Column(Text, index=True, unique=True)


@utils.fix_doc
class Node(aria_declarative_base, service_instance.NodeBase):
    pass


@utils.fix_doc
class Group(aria_declarative_base, service_instance.GroupBase):
    pass


@utils.fix_doc
class Policy(aria_declarative_base, service_instance.PolicyBase):
    pass


@utils.fix_doc
class Substitution(aria_declarative_base, service_instance.SubstitutionBase):
    pass


@utils.fix_doc
class SubstitutionMapping(aria_declarative_base, service_instance.SubstitutionMappingBase):
    pass


@utils.fix_doc
class Relationship(aria_declarative_base, service_instance.RelationshipBase):
    pass


@utils.fix_doc
class Capability(aria_declarative_base, service_instance.CapabilityBase):
    pass


@utils.fix_doc
class Interface(aria_declarative_base, service_instance.InterfaceBase):
    pass


@utils.fix_doc
class Operation(aria_declarative_base, service_instance.OperationBase):
    pass


@utils.fix_doc
class Artifact(aria_declarative_base, service_instance.ArtifactBase):
    pass

# endregion


# region service changes models

@utils.fix_doc
class ServiceUpdate(aria_declarative_base, service_changes.ServiceUpdateBase):
    pass


@utils.fix_doc
class ServiceUpdateStep(aria_declarative_base, service_changes.ServiceUpdateStepBase):
    pass


@utils.fix_doc
class ServiceModification(aria_declarative_base, service_changes.ServiceModificationBase):
    pass

# endregion


# region common service models

@utils.fix_doc
class Input(aria_declarative_base, service_common.InputBase):
    pass


@utils.fix_doc
class Configuration(aria_declarative_base, service_common.ConfigurationBase):
    pass


@utils.fix_doc
class Output(aria_declarative_base, service_common.OutputBase):
    pass


@utils.fix_doc
class Property(aria_declarative_base, service_common.PropertyBase):
    pass


@utils.fix_doc
class Attribute(aria_declarative_base, service_common.AttributeBase):
    pass


@utils.fix_doc
class Type(aria_declarative_base, service_common.TypeBase):
    pass


@utils.fix_doc
class Metadata(aria_declarative_base, service_common.MetadataBase):
    pass

# endregion


# region orchestration models

@utils.fix_doc
class Execution(aria_declarative_base, orchestration.ExecutionBase):
    pass


@utils.fix_doc
class Plugin(aria_declarative_base, orchestration.PluginBase):
    pass


@utils.fix_doc
class Task(aria_declarative_base, orchestration.TaskBase):
    pass


@utils.fix_doc
class Log(aria_declarative_base, orchestration.LogBase):
    pass


@utils.fix_doc
class Argument(aria_declarative_base, orchestration.ArgumentBase):
    pass

# endregion


# See also __all__ at the top of this file
models_to_register = (
    # Type definition models
    TypeDefinition,

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
    Input,
    Configuration,
    Output,
    Property,
    Attribute,
    Type,
    Metadata,

    # Orchestration models
    Execution,
    Plugin,
    Task,
    Log,
    Argument
)
