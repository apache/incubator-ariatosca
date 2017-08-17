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
Parser implementation of `TOSCA Simple Profile v1.0 cos01 <http://docs.oasis-open.org/tosca
/TOSCA-Simple-Profile-YAML/v1.0/cos01/TOSCA-Simple-Profile-YAML-v1.0-cos01.html>`__.

.. autosummary::
   :nosignatures:

   aria_extension_tosca.simple_v1_0.ToscaSimplePresenter1_0

Assignments
-----------

.. autosummary::
   :nosignatures:

   aria_extension_tosca.simple_v1_0.PropertyAssignment
   aria_extension_tosca.simple_v1_0.OperationAssignment
   aria_extension_tosca.simple_v1_0.InterfaceAssignment
   aria_extension_tosca.simple_v1_0.RelationshipAssignment
   aria_extension_tosca.simple_v1_0.RequirementAssignment
   aria_extension_tosca.simple_v1_0.AttributeAssignment
   aria_extension_tosca.simple_v1_0.CapabilityAssignment
   aria_extension_tosca.simple_v1_0.ArtifactAssignment

Definitions
-----------

.. autosummary::
   :nosignatures:

   aria_extension_tosca.simple_v1_0.PropertyDefinition
   aria_extension_tosca.simple_v1_0.AttributeDefinition
   aria_extension_tosca.simple_v1_0.InputDefinition
   aria_extension_tosca.simple_v1_0.OutputDefinition
   aria_extension_tosca.simple_v1_0.OperationDefinition
   aria_extension_tosca.simple_v1_0.InterfaceDefinition
   aria_extension_tosca.simple_v1_0.RelationshipDefinition
   aria_extension_tosca.simple_v1_0.RequirementDefinition
   aria_extension_tosca.simple_v1_0.CapabilityDefinition

Filters
-------

.. autosummary::
   :nosignatures:

   aria_extension_tosca.simple_v1_0.CapabilityFilter
   aria_extension_tosca.simple_v1_0.NodeFilter

Miscellaneous
-------------

.. autosummary::
   :nosignatures:

   aria_extension_tosca.simple_v1_0.Description
   aria_extension_tosca.simple_v1_0.MetaData
   aria_extension_tosca.simple_v1_0.Repository
   aria_extension_tosca.simple_v1_0.Import
   aria_extension_tosca.simple_v1_0.ConstraintClause
   aria_extension_tosca.simple_v1_0.EntrySchema
   aria_extension_tosca.simple_v1_0.OperationImplementation
   aria_extension_tosca.simple_v1_0.SubstitutionMappingsRequirement
   aria_extension_tosca.simple_v1_0.SubstitutionMappingsCapability
   aria_extension_tosca.simple_v1_0.SubstitutionMappings

Templates
---------

.. autosummary::
   :nosignatures:

   aria_extension_tosca.simple_v1_0.NodeTemplate
   aria_extension_tosca.simple_v1_0.RelationshipTemplate
   aria_extension_tosca.simple_v1_0.GroupTemplate
   aria_extension_tosca.simple_v1_0.PolicyTemplate
   aria_extension_tosca.simple_v1_0.TopologyTemplate
   aria_extension_tosca.simple_v1_0.ServiceTemplate

Types
-----

.. autosummary::
   :nosignatures:

   aria_extension_tosca.simple_v1_0.ArtifactType
   aria_extension_tosca.simple_v1_0.DataType
   aria_extension_tosca.simple_v1_0.CapabilityType
   aria_extension_tosca.simple_v1_0.InterfaceType
   aria_extension_tosca.simple_v1_0.RelationshipType
   aria_extension_tosca.simple_v1_0.NodeType
   aria_extension_tosca.simple_v1_0.GroupType
   aria_extension_tosca.simple_v1_0.PolicyType

Data types
----------

.. autosummary::
   :nosignatures:

   aria_extension_tosca.simple_v1_0.Timestamp
   aria_extension_tosca.simple_v1_0.Version
   aria_extension_tosca.simple_v1_0.Range
   aria_extension_tosca.simple_v1_0.List
   aria_extension_tosca.simple_v1_0.Map
   aria_extension_tosca.simple_v1_0.ScalarSize
   aria_extension_tosca.simple_v1_0.ScalarTime
   aria_extension_tosca.simple_v1_0.ScalarFrequency
"""

from .presenter import ToscaSimplePresenter1_0
from .assignments import (PropertyAssignment, OperationAssignment, InterfaceAssignment,
                          RelationshipAssignment, RequirementAssignment, AttributeAssignment,
                          CapabilityAssignment, ArtifactAssignment)
from .definitions import (PropertyDefinition, AttributeDefinition, InputDefinition,
                          OutputDefinition, OperationDefinition, InterfaceDefinition,
                          RelationshipDefinition, RequirementDefinition, CapabilityDefinition)
from .filters import CapabilityFilter, NodeFilter
from .misc import (Description, MetaData, Repository, Import, ConstraintClause, EntrySchema,
                   OperationImplementation, SubstitutionMappingsRequirement,
                   SubstitutionMappingsCapability, SubstitutionMappings)
from .templates import (NodeTemplate, RelationshipTemplate, GroupTemplate, PolicyTemplate,
                        TopologyTemplate, ServiceTemplate)
from .types import (ArtifactType, DataType, CapabilityType, InterfaceType, RelationshipType,
                    NodeType, GroupType, PolicyType)
from .data_types import (Timestamp, Version, Range, List, Map, ScalarSize, ScalarTime,
                         ScalarFrequency)

MODULES = (
    'modeling',
    'presentation')

__all__ = (
    'MODULES',
    'ToscaSimplePresenter1_0',
    'PropertyAssignment',
    'OperationAssignment',
    'InterfaceAssignment',
    'RelationshipAssignment',
    'RequirementAssignment',
    'AttributeAssignment',
    'CapabilityAssignment',
    'ArtifactAssignment',
    'PropertyDefinition',
    'AttributeDefinition',
    'InputDefinition',
    'OutputDefinition',
    'OperationDefinition',
    'InterfaceDefinition',
    'RelationshipDefinition',
    'RequirementDefinition',
    'CapabilityDefinition',
    'CapabilityFilter',
    'NodeFilter',
    'Description',
    'MetaData',
    'Repository',
    'Import',
    'ConstraintClause',
    'EntrySchema',
    'OperationImplementation',
    'SubstitutionMappingsRequirement',
    'SubstitutionMappingsCapability',
    'SubstitutionMappings',
    'NodeTemplate',
    'RelationshipTemplate',
    'GroupTemplate',
    'PolicyTemplate',
    'TopologyTemplate',
    'ServiceTemplate',
    'ArtifactType',
    'DataType',
    'CapabilityType',
    'InterfaceType',
    'RelationshipType',
    'NodeType',
    'GroupType',
    'PolicyType',
    'Timestamp',
    'Version',
    'Range',
    'List',
    'Map',
    'ScalarSize',
    'ScalarTime',
    'ScalarFrequency')
