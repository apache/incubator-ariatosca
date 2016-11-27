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
from collections import namedtuple
from datetime import datetime

from sqlalchemy.ext.declarative.base import declared_attr

from .structures import (
    SQLModelBase,
    Column,
    Integer,
    Text,
    DateTime,
    Boolean,
    Enum,
    String,
    Float,
    List,
    Dict,
    foreign_key,
    one_to_many_relationship,
    relationship_to_self,
    orm)

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
    'ProviderContext',
    'Plugin',
)


#pylint: disable=no-self-argument


class Blueprint(SQLModelBase):
    """
    Blueprint model representation.
    """
    __tablename__ = 'blueprints'

    name = Column(Text, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    main_file_name = Column(Text, nullable=False)
    plan = Column(Dict, nullable=False)
    updated_at = Column(DateTime)
    description = Column(Text)


class Deployment(SQLModelBase):
    """
    Deployment model representation.
    """
    __tablename__ = 'deployments'

    _private_fields = ['blueprint_id']

    blueprint_id = foreign_key(Blueprint.id)

    name = Column(Text, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    description = Column(Text)
    inputs = Column(Dict)
    groups = Column(Dict)
    permalink = Column(Text)
    policy_triggers = Column(Dict)
    policy_types = Column(Dict)
    outputs = Column(Dict)
    scaling_groups = Column(Dict)
    updated_at = Column(DateTime)
    workflows = Column(Dict)

    @declared_attr
    def blueprint(cls):
        return one_to_many_relationship(cls, Blueprint, cls.blueprint_id)


class Execution(SQLModelBase):
    """
    Execution model representation.
    """
    __tablename__ = 'executions'

    TERMINATED = 'terminated'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    PENDING = 'pending'
    STARTED = 'started'
    CANCELLING = 'cancelling'
    FORCE_CANCELLING = 'force_cancelling'

    STATES = [TERMINATED, FAILED, CANCELLED, PENDING, STARTED, CANCELLING, FORCE_CANCELLING]
    END_STATES = [TERMINATED, FAILED, CANCELLED]
    ACTIVE_STATES = [state for state in STATES if state not in END_STATES]

    VALID_TRANSITIONS = {
        PENDING: [STARTED, CANCELLED],
        STARTED: END_STATES + [CANCELLING],
        CANCELLING: END_STATES
    }

    @orm.validates('status')
    def validate_status(self, key, value):
        """Validation function that verifies execution status transitions are OK"""
        try:
            current_status = getattr(self, key)
        except AttributeError:
            return
        valid_transitions = Execution.VALID_TRANSITIONS.get(current_status, [])
        if all([current_status is not None,
                current_status != value,
                value not in valid_transitions]):
            raise ValueError('Cannot change execution status from {current} to {new}'.format(
                current=current_status,
                new=value))
        return value

    deployment_id = foreign_key(Deployment.id)
    blueprint_id = foreign_key(Blueprint.id)
    _private_fields = ['deployment_id', 'blueprint_id']

    created_at = Column(DateTime, index=True)
    started_at = Column(DateTime, nullable=True, index=True)
    ended_at = Column(DateTime, nullable=True, index=True)
    error = Column(Text, nullable=True)
    is_system_workflow = Column(Boolean, nullable=False, default=False)
    parameters = Column(Dict)
    status = Column(Enum(*STATES, name='execution_status'), default=PENDING)
    workflow_name = Column(Text, nullable=False)

    @declared_attr
    def deployment(cls):
        return one_to_many_relationship(cls, Deployment, cls.deployment_id)

    @declared_attr
    def blueprint(cls):
        return one_to_many_relationship(cls, Blueprint, cls.blueprint_id)

    def __str__(self):
        return '<{0} id=`{1}` (status={2})>'.format(
            self.__class__.__name__,
            self.id,
            self.status
        )


class DeploymentUpdate(SQLModelBase):
    """
    Deployment update model representation.
    """
    __tablename__ = 'deployment_updates'

    deployment_id = foreign_key(Deployment.id)
    execution_id = foreign_key(Execution.id, nullable=True)
    _private_fields = ['execution_id', 'deployment_id']

    created_at = Column(DateTime, nullable=False, index=True)
    deployment_plan = Column(Dict, nullable=False)
    deployment_update_node_instances = Column(Dict)
    deployment_update_deployment = Column(Dict)
    deployment_update_nodes = Column(Dict)
    modified_entity_ids = Column(Dict)
    state = Column(Text)

    @declared_attr
    def execution(cls):
        return one_to_many_relationship(cls, Execution, cls.execution_id)

    @declared_attr
    def deployment(cls):
        return one_to_many_relationship(cls, Deployment, cls.deployment_id)

    def to_dict(self, suppress_error=False, **kwargs):
        dep_update_dict = super(DeploymentUpdate, self).to_dict(suppress_error)
        # Taking care of the fact the DeploymentSteps are objects
        dep_update_dict['steps'] = [step.to_dict() for step in self.steps]
        return dep_update_dict


class DeploymentUpdateStep(SQLModelBase):
    """
    Deployment update step model representation.
    """
    __tablename__ = 'deployment_update_steps'
    _action_types = namedtuple('ACTION_TYPES', 'ADD, REMOVE, MODIFY')
    ACTION_TYPES = _action_types(ADD='add', REMOVE='remove', MODIFY='modify')
    _entity_types = namedtuple(
        'ENTITY_TYPES',
        'NODE, RELATIONSHIP, PROPERTY, OPERATION, WORKFLOW, OUTPUT, DESCRIPTION, GROUP, '
        'POLICY_TYPE, POLICY_TRIGGER, PLUGIN')
    ENTITY_TYPES = _entity_types(
        NODE='node',
        RELATIONSHIP='relationship',
        PROPERTY='property',
        OPERATION='operation',
        WORKFLOW='workflow',
        OUTPUT='output',
        DESCRIPTION='description',
        GROUP='group',
        POLICY_TYPE='policy_type',
        POLICY_TRIGGER='policy_trigger',
        PLUGIN='plugin'
    )

    deployment_update_id = foreign_key(DeploymentUpdate.id)
    _private_fields = ['deployment_update_id']

    action = Column(Enum(*ACTION_TYPES, name='action_type'), nullable=False)
    entity_id = Column(Text, nullable=False)
    entity_type = Column(Enum(*ENTITY_TYPES, name='entity_type'), nullable=False)

    @declared_attr
    def deployment_update(cls):
        return one_to_many_relationship(cls,
                                        DeploymentUpdate,
                                        cls.deployment_update_id,
                                        backreference='steps')

    def __hash__(self):
        return hash((self.id, self.entity_id))

    def __lt__(self, other):
        """
        the order is 'remove' < 'modify' < 'add'
        :param other:
        :return:
        """
        if not isinstance(other, self.__class__):
            return not self >= other

        if self.action != other.action:
            if self.action == 'remove':
                return_value = True
            elif self.action == 'add':
                return_value = False
            else:
                return_value = other.action == 'add'
            return return_value

        if self.action == 'add':
            return self.entity_type == 'node' and other.entity_type == 'relationship'
        if self.action == 'remove':
            return self.entity_type == 'relationship' and other.entity_type == 'node'
        return False


class DeploymentModification(SQLModelBase):
    """
    Deployment modification model representation.
    """
    __tablename__ = 'deployment_modifications'

    STARTED = 'started'
    FINISHED = 'finished'
    ROLLEDBACK = 'rolledback'

    STATES = [STARTED, FINISHED, ROLLEDBACK]
    END_STATES = [FINISHED, ROLLEDBACK]

    deployment_id = foreign_key(Deployment.id)
    _private_fields = ['deployment_id']

    context = Column(Dict)
    created_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, index=True)
    modified_nodes = Column(Dict)
    node_instances = Column(Dict)
    status = Column(Enum(*STATES, name='deployment_modification_status'))

    @declared_attr
    def deployment(cls):
        return one_to_many_relationship(cls,
                                        Deployment,
                                        cls.deployment_id,
                                        backreference='modifications')


class Node(SQLModelBase):
    """
    Node model representation.
    """
    __tablename__ = 'nodes'

    # See base class for an explanation on these properties
    is_id_unique = False

    name = Column(Text, index=True)
    _private_fields = ['deployment_id', 'host_id']
    deployment_id = foreign_key(Deployment.id)
    host_id = foreign_key('nodes.id', nullable=True)

    @declared_attr
    def deployment(cls):
        return one_to_many_relationship(cls, Deployment, cls.deployment_id)

    deploy_number_of_instances = Column(Integer, nullable=False)
    # TODO: This probably should be a foreign key, but there's no guarantee
    # in the code, currently, that the host will be created beforehand
    max_number_of_instances = Column(Integer, nullable=False)
    min_number_of_instances = Column(Integer, nullable=False)
    number_of_instances = Column(Integer, nullable=False)
    planned_number_of_instances = Column(Integer, nullable=False)
    plugins = Column(Dict)
    plugins_to_install = Column(Dict)
    properties = Column(Dict)
    operations = Column(Dict)
    type = Column(Text, nullable=False, index=True)
    type_hierarchy = Column(List)

    @declared_attr
    def host(cls):
        return relationship_to_self(cls, cls.host_id, cls.id)


class Relationship(SQLModelBase):
    """
    Relationship model representation.
    """
    __tablename__ = 'relationships'

    _private_fields = ['source_node_id', 'target_node_id']

    source_node_id = foreign_key(Node.id)
    target_node_id = foreign_key(Node.id)

    @declared_attr
    def source_node(cls):
        return one_to_many_relationship(cls,
                                        Node,
                                        cls.source_node_id,
                                        'outbound_relationships')

    @declared_attr
    def target_node(cls):
        return one_to_many_relationship(cls,
                                        Node,
                                        cls.target_node_id,
                                        'inbound_relationships')

    source_interfaces = Column(Dict)
    source_operations = Column(Dict, nullable=False)
    target_interfaces = Column(Dict)
    target_operations = Column(Dict, nullable=False)
    type = Column(String, nullable=False)
    type_hierarchy = Column(List)
    properties = Column(Dict)


class NodeInstance(SQLModelBase):
    """
    Node instance model representation.
    """
    __tablename__ = 'node_instances'

    node_id = foreign_key(Node.id)
    deployment_id = foreign_key(Deployment.id)
    host_id = foreign_key('node_instances.id', nullable=True)

    _private_fields = ['node_id', 'host_id']

    name = Column(Text, index=True)
    runtime_properties = Column(Dict)
    scaling_groups = Column(Dict)
    state = Column(Text, nullable=False)
    version = Column(Integer, default=1)

    @declared_attr
    def deployment(cls):
        return one_to_many_relationship(cls, Deployment, cls.deployment_id)

    @declared_attr
    def node(cls):
        return one_to_many_relationship(cls, Node, cls.node_id)

    @declared_attr
    def host(cls):
        return relationship_to_self(cls, cls.host_id, cls.id)


class RelationshipInstance(SQLModelBase):
    """
    Relationship instance model representation.
    """
    __tablename__ = 'relationship_instances'

    relationship_id = foreign_key(Relationship.id)
    source_node_instance_id = foreign_key(NodeInstance.id)
    target_node_instance_id = foreign_key(NodeInstance.id)

    _private_fields = ['relationship_storage_id',
                       'source_node_instance_id',
                       'target_node_instance_id']

    @declared_attr
    def source_node_instance(cls):
        return one_to_many_relationship(cls,
                                        NodeInstance,
                                        cls.source_node_instance_id,
                                        'outbound_relationship_instances')

    @declared_attr
    def target_node_instance(cls):
        return one_to_many_relationship(cls,
                                        NodeInstance,
                                        cls.target_node_instance_id,
                                        'inbound_relationship_instances')

    @declared_attr
    def relationship(cls):
        return one_to_many_relationship(cls, Relationship, cls.relationship_id)


class ProviderContext(SQLModelBase):
    """
    Provider context model representation.
    """
    __tablename__ = 'provider_context'

    name = Column(Text, nullable=False)
    context = Column(Dict, nullable=False)


class Plugin(SQLModelBase):
    """
    Plugin model representation.
    """
    __tablename__ = 'plugins'

    archive_name = Column(Text, nullable=False, index=True)
    distribution = Column(Text)
    distribution_release = Column(Text)
    distribution_version = Column(Text)
    excluded_wheels = Column(Dict)
    package_name = Column(Text, nullable=False, index=True)
    package_source = Column(Text)
    package_version = Column(Text)
    supported_platform = Column(Dict)
    supported_py_versions = Column(Dict)
    uploaded_at = Column(DateTime, nullable=False, index=True)
    wheels = Column(Dict, nullable=False)


class Task(SQLModelBase):
    """
    A Model which represents an task
    """

    __tablename__ = 'task'
    node_instance_id = foreign_key(NodeInstance.id, nullable=True)
    relationship_instance_id = foreign_key(RelationshipInstance.id, nullable=True)
    execution_id = foreign_key(Execution.id, nullable=True)

    _private_fields = ['node_instance_id',
                       'relationship_instance_id',
                       'execution_id']

    @declared_attr
    def node_instance(cls):
        return one_to_many_relationship(cls, NodeInstance, cls.node_instance_id)

    @declared_attr
    def relationship_instance(cls):
        return one_to_many_relationship(cls,
                                        RelationshipInstance,
                                        cls.relationship_instance_id)

    PENDING = 'pending'
    RETRYING = 'retrying'
    SENT = 'sent'
    STARTED = 'started'
    SUCCESS = 'success'
    FAILED = 'failed'
    STATES = (
        PENDING,
        RETRYING,
        SENT,
        STARTED,
        SUCCESS,
        FAILED,
    )

    WAIT_STATES = [PENDING, RETRYING]
    END_STATES = [SUCCESS, FAILED]

    @orm.validates('max_attempts')
    def validate_max_attempts(self, _, value):                                  # pylint: disable=no-self-use
        """Validates that max attempts is either -1 or a positive number"""
        if value < 1 and value != Task.INFINITE_RETRIES:
            raise ValueError('Max attempts can be either -1 (infinite) or any positive number. '
                             'Got {value}'.format(value=value))
        return value

    INFINITE_RETRIES = -1

    status = Column(Enum(*STATES), name='status', default=PENDING)

    due_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, default=None)
    ended_at = Column(DateTime, default=None)
    max_attempts = Column(Integer, default=1)
    retry_count = Column(Integer, default=0)
    retry_interval = Column(Float, default=0)
    ignore_failure = Column(Boolean, default=False)

    # Operation specific fields
    name = Column(String)
    operation_mapping = Column(String)
    inputs = Column(Dict)

    @declared_attr
    def execution(cls):
        return one_to_many_relationship(cls, Execution, cls.execution_id)

    @property
    def actor(self):
        """
        Return the actor of the task
        :return:
        """
        return self.node_instance or self.relationship_instance

    @classmethod
    def as_node_instance(cls, instance_id, **kwargs):
        return cls(node_instance_id=instance_id, **kwargs)

    @classmethod
    def as_relationship_instance(cls, instance_id, **kwargs):
        return cls(relationship_instance_id=instance_id, **kwargs)
