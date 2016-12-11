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
Aria's storage.models module
Path: aria.storage.models

models module holds aria's models.

classes:
    * Field - represents a single field.
    * IterField - represents an iterable field.
    * Model - abstract model implementation.
    * Snapshot - snapshots implementation model.
    * Deployment - deployment implementation model.
    * DeploymentUpdateStep - deployment update step implementation model.
    * DeploymentUpdate - deployment update implementation model.
    * DeploymentModification - deployment modification implementation model.
    * Execution - execution implementation model.
    * Node - node implementation model.
    * Relationship - relationship implementation model.
    * NodeInstance - node instance implementation model.
    * RelationshipInstance - relationship instance implementation model.
    * ProviderContext - provider context implementation model.
    * Plugin - plugin implementation model.
"""
from sqlalchemy.ext.declarative import declarative_base

from . import structure
from . import base_model as base

__all__ = (
    'Blueprint',
    'Deployment',
    'DeploymentUpdateStep',
    'DeploymentUpdate',
    'DeploymentModification',
    'Execution',
    'Node',
    'Relationship',
    'NodeInstance',
    'RelationshipInstance',
    'Plugin',
)


#pylint: disable=abstract-method
# The required abstract method implementation are implemented in the ModelIDMixin, which is used as
# a base to the DeclerativeBase.
DeclarativeBase = declarative_base(cls=structure.ModelIDMixin)


class Blueprint(DeclarativeBase, base.BlueprintBase):
    pass


class Deployment(DeclarativeBase, base.DeploymentBase):
    pass


class Execution(DeclarativeBase, base.ExecutionBase):
    pass


class DeploymentUpdate(DeclarativeBase, base.DeploymentUpdateBase):
    pass


class DeploymentUpdateStep(DeclarativeBase, base.DeploymentUpdateStepBase):
    pass


class DeploymentModification(DeclarativeBase, base.DeploymentModificationBase):
    pass


class Node(DeclarativeBase, base.NodeBase):
    pass


class Relationship(DeclarativeBase, base.RelationshipBase):
    pass


class NodeInstance(DeclarativeBase, base.NodeInstanceBase):
    pass


class RelationshipInstance(DeclarativeBase, base.RelationshipInstanceBase):
    pass


class Plugin(DeclarativeBase, base.PluginBase):
    pass


class Task(DeclarativeBase, base.TaskBase):
    pass
