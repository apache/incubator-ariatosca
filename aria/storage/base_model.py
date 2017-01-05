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
    * Plugin - plugin implementation model.
"""
from collections import namedtuple
from datetime import datetime

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    Boolean,
    Enum,
    String,
    Float,
    orm,
)

from .structure import ModelMixin

from .type import (
    List,
    Dict
)

__all__ = (
    'BlueprintBase',
    'DeploymentBase',
    'DeploymentUpdateStepBase',
    'DeploymentUpdateBase',
    'DeploymentModificationBase',
    'ExecutionBase',
    'NodeBase',
    'RelationshipBase',
    'NodeInstanceBase',
    'RelationshipInstanceBase',
    'PluginBase',
    'TaskBase'
)

#pylint: disable=no-self-argument, abstract-method


class BlueprintBase(ModelMixin):
    """
    Blueprint model representation.
    """
    __tablename__ = 'blueprints'

    created_at = Column(DateTime, nullable=False, index=True)
    main_file_name = Column(Text, nullable=False)
    plan = Column(Dict, nullable=False)
    updated_at = Column(DateTime)
    description = Column(Text)


class DeploymentBase(ModelMixin):
    """
    Deployment model representation.
    """
    __tablename__ = 'deployments'

    _private_fields = ['blueprint_fk']

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
    def blueprint_fk(cls):
        return cls.foreign_key(BlueprintBase, nullable=False)

    @declared_attr
    def blueprint(cls):
        return cls.one_to_many_relationship('blueprint_fk')

    @declared_attr
    def blueprint_name(cls):
        return association_proxy('blueprint', cls.name_column_name())


class ExecutionBase(ModelMixin):
    """
    Execution model representation.
    """
    # Needed only for pylint. the id will be populated by sqlalcehmy and the proper column.
    __tablename__ = 'executions'
    _private_fields = ['deployment_fk']

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
        CANCELLING: END_STATES + [FORCE_CANCELLING]
    }

    @orm.validates('status')
    def validate_status(self, key, value):
        """Validation function that verifies execution status transitions are OK"""
        try:
            current_status = getattr(self, key)
        except AttributeError:
            return
        valid_transitions = self.VALID_TRANSITIONS.get(current_status, [])
        if all([current_status is not None,
                current_status != value,
                value not in valid_transitions]):
            raise ValueError('Cannot change execution status from {current} to {new}'.format(
                current=current_status,
                new=value))
        return value

    created_at = Column(DateTime, index=True)
    started_at = Column(DateTime, nullable=True, index=True)
    ended_at = Column(DateTime, nullable=True, index=True)
    error = Column(Text, nullable=True)
    is_system_workflow = Column(Boolean, nullable=False, default=False)
    parameters = Column(Dict)
    status = Column(Enum(*STATES, name='execution_status'), default=PENDING)
    workflow_name = Column(Text)

    @declared_attr
    def blueprint(cls):
        return association_proxy('deployment', 'blueprint')

    @declared_attr
    def deployment_fk(cls):
        return cls.foreign_key(DeploymentBase, nullable=True)

    @declared_attr
    def deployment(cls):
        return cls.one_to_many_relationship('deployment_fk')

    @declared_attr
    def deployment_name(cls):
        return association_proxy('deployment', cls.name_column_name())

    @declared_attr
    def blueprint_name(cls):
        return association_proxy('deployment', 'blueprint_name')

    def __str__(self):
        return '<{0} id=`{1}` (status={2})>'.format(
            self.__class__.__name__,
            getattr(self, self.name_column_name()),
            self.status
        )


class DeploymentUpdateBase(ModelMixin):
    """
    Deployment update model representation.
    """
    # Needed only for pylint. the id will be populated by sqlalcehmy and the proper column.
    steps = None

    __tablename__ = 'deployment_updates'

    _private_fields = ['execution_fk', 'deployment_fk']

    created_at = Column(DateTime, nullable=False, index=True)
    deployment_plan = Column(Dict, nullable=False)
    deployment_update_node_instances = Column(Dict)
    deployment_update_deployment = Column(Dict)
    deployment_update_nodes = Column(List)
    modified_entity_ids = Column(Dict)
    state = Column(Text)

    @declared_attr
    def execution_fk(cls):
        return cls.foreign_key(ExecutionBase, nullable=True)

    @declared_attr
    def execution(cls):
        return cls.one_to_many_relationship('execution_fk')

    @declared_attr
    def execution_name(cls):
        return association_proxy('execution', cls.name_column_name())

    @declared_attr
    def deployment_fk(cls):
        return cls.foreign_key(DeploymentBase)

    @declared_attr
    def deployment(cls):
        return cls.one_to_many_relationship('deployment_fk')

    @declared_attr
    def deployment_name(cls):
        return association_proxy('deployment', cls.name_column_name())

    def to_dict(self, suppress_error=False, **kwargs):
        dep_update_dict = super(DeploymentUpdateBase, self).to_dict(suppress_error)     #pylint: disable=no-member
        # Taking care of the fact the DeploymentSteps are _BaseModels
        dep_update_dict['steps'] = [step.to_dict() for step in self.steps]
        return dep_update_dict


class DeploymentUpdateStepBase(ModelMixin):
    """
    Deployment update step model representation.
    """
    # Needed only for pylint. the id will be populated by sqlalcehmy and the proper column.
    __tablename__ = 'deployment_update_steps'
    _private_fields = ['deployment_update_fk']

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

    action = Column(Enum(*ACTION_TYPES, name='action_type'), nullable=False)
    entity_id = Column(Text, nullable=False)
    entity_type = Column(Enum(*ENTITY_TYPES, name='entity_type'), nullable=False)

    @declared_attr
    def deployment_update_fk(cls):
        return cls.foreign_key(DeploymentUpdateBase)

    @declared_attr
    def deployment_update(cls):
        return cls.one_to_many_relationship('deployment_update_fk', backreference='steps')

    @declared_attr
    def deployment_update_name(cls):
        return association_proxy('deployment_update', cls.name_column_name())

    def __hash__(self):
        return hash((getattr(self, self.id_column_name()), self.entity_id))

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


class DeploymentModificationBase(ModelMixin):
    """
    Deployment modification model representation.
    """
    __tablename__ = 'deployment_modifications'
    _private_fields = ['deployment_fk']

    STARTED = 'started'
    FINISHED = 'finished'
    ROLLEDBACK = 'rolledback'

    STATES = [STARTED, FINISHED, ROLLEDBACK]
    END_STATES = [FINISHED, ROLLEDBACK]

    context = Column(Dict)
    created_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, index=True)
    modified_nodes = Column(Dict)
    node_instances = Column(Dict)
    status = Column(Enum(*STATES, name='deployment_modification_status'))

    @declared_attr
    def deployment_fk(cls):
        return cls.foreign_key(DeploymentBase)

    @declared_attr
    def deployment(cls):
        return cls.one_to_many_relationship('deployment_fk', backreference='modifications')

    @declared_attr
    def deployment_name(cls):
        return association_proxy('deployment', cls.name_column_name())


class NodeBase(ModelMixin):
    """
    Node model representation.
    """
    __tablename__ = 'nodes'

    # See base class for an explanation on these properties
    is_id_unique = False

    _private_fields = ['blueprint_fk', 'host_fk']

    @declared_attr
    def host_fk(cls):
        return cls.foreign_key(NodeBase, nullable=True)

    @declared_attr
    def host(cls):
        return cls.relationship_to_self('host_fk')

    @declared_attr
    def host_name(cls):
        return association_proxy('host', cls.name_column_name())

    @declared_attr
    def deployment_fk(cls):
        return cls.foreign_key(DeploymentBase)

    @declared_attr
    def deployment(cls):
        return cls.one_to_many_relationship('deployment_fk')

    @declared_attr
    def deployment_name(cls):
        return association_proxy('deployment', cls.name_column_name())

    @declared_attr
    def blueprint_name(cls):
        return association_proxy('deployment', 'blueprint_{0}'.format(cls.name_column_name()))

    deploy_number_of_instances = Column(Integer, nullable=False)
    max_number_of_instances = Column(Integer, nullable=False)
    min_number_of_instances = Column(Integer, nullable=False)
    number_of_instances = Column(Integer, nullable=False)
    planned_number_of_instances = Column(Integer, nullable=False)
    plugins = Column(List)
    properties = Column(Dict)
    operations = Column(Dict)
    type = Column(Text, nullable=False, index=True)
    type_hierarchy = Column(List)


class RelationshipBase(ModelMixin):
    """
    Relationship model representation.
    """
    __tablename__ = 'relationships'

    _private_fields = ['source_node_fk', 'target_node_fk']

    @declared_attr
    def source_node_fk(cls):
        return cls.foreign_key(NodeBase)

    @declared_attr
    def source_node(cls):
        return cls.one_to_many_relationship('source_node_fk',
                                            backreference='outbound_relationships')

    @declared_attr
    def source_name(cls):
        return association_proxy('source_node', cls.name_column_name())

    @declared_attr
    def target_node_fk(cls):
        return cls.foreign_key(NodeBase)

    @declared_attr
    def target_node(cls):
        return cls.one_to_many_relationship('target_node_fk', backreference='inbound_relationships')

    @declared_attr
    def target_name(cls):
        return association_proxy('target_node', cls.name_column_name())

    source_interfaces = Column(Dict)
    source_operations = Column(Dict, nullable=False)
    target_interfaces = Column(Dict)
    target_operations = Column(Dict, nullable=False)
    type = Column(String, nullable=False)
    type_hierarchy = Column(List)
    properties = Column(Dict)


class NodeInstanceBase(ModelMixin):
    """
    Node instance model representation.
    """
    __tablename__ = 'node_instances'
    _private_fields = ['node_fk', 'host_fk']

    runtime_properties = Column(Dict)
    scaling_groups = Column(List)
    state = Column(Text, nullable=False)
    version = Column(Integer, default=1)

    @declared_attr
    def host_fk(cls):
        return cls.foreign_key(NodeInstanceBase, nullable=True)

    @declared_attr
    def host(cls):
        return cls.relationship_to_self('host_fk')

    @declared_attr
    def host_name(cls):
        return association_proxy('host', cls.name_column_name())

    @declared_attr
    def deployment(cls):
        return association_proxy('node', 'deployment')

    @declared_attr
    def deployment_name(cls):
        return association_proxy('node', 'deployment_name')

    @declared_attr
    def node_fk(cls):
        return cls.foreign_key(NodeBase, nullable=True)

    @declared_attr
    def node(cls):
        return cls.one_to_many_relationship('node_fk')

    @declared_attr
    def node_name(cls):
        return association_proxy('node', cls.name_column_name())


class RelationshipInstanceBase(ModelMixin):
    """
    Relationship instance model representation.
    """
    __tablename__ = 'relationship_instances'
    _private_fields = ['relationship_storage_fk',
                       'source_node_instance_fk',
                       'target_node_instance_fk']

    @declared_attr
    def source_node_instance_fk(cls):
        return cls.foreign_key(NodeInstanceBase)

    @declared_attr
    def source_node_instance(cls):
        return cls.one_to_many_relationship('source_node_instance_fk',
                                            backreference='outbound_relationship_instances')

    @declared_attr
    def source_node_instance_name(cls):
        return association_proxy('source_node_instance', cls.name_column_name())

    @declared_attr
    def target_node_instance_fk(cls):
        return cls.foreign_key(NodeInstanceBase)

    @declared_attr
    def target_node_instance(cls):
        return cls.one_to_many_relationship('target_node_instance_fk',
                                            backreference='inbound_relationship_instances')

    @declared_attr
    def target_node_instance_name(cls):
        return association_proxy('target_node_instance', cls.name_column_name())

    @declared_attr
    def relationship_fk(cls):
        return cls.foreign_key(RelationshipBase)

    @declared_attr
    def relationship(cls):
        return cls.one_to_many_relationship('relationship_fk')

    @declared_attr
    def relationship_name(cls):
        return association_proxy('relationship', cls.name_column_name())


class PluginBase(ModelMixin):
    """
    Plugin model representation.
    """
    __tablename__ = 'plugins'

    archive_name = Column(Text, nullable=False, index=True)
    distribution = Column(Text)
    distribution_release = Column(Text)
    distribution_version = Column(Text)
    package_name = Column(Text, nullable=False, index=True)
    package_source = Column(Text)
    package_version = Column(Text)
    supported_platform = Column(Text)
    supported_py_versions = Column(List)
    uploaded_at = Column(DateTime, nullable=False, index=True)
    wheels = Column(List, nullable=False)


class TaskBase(ModelMixin):
    """
    A Model which represents an task
    """
    __tablename__ = 'tasks'
    _private_fields = ['node_instance_fk', 'relationship_instance_fk', 'execution_fk']

    @declared_attr
    def node_instance_fk(cls):
        return cls.foreign_key(NodeInstanceBase, nullable=True)

    @declared_attr
    def node_instance_name(cls):
        return association_proxy('node_instance', cls.name_column_name())

    @declared_attr
    def node_instance(cls):
        return cls.one_to_many_relationship('node_instance_fk')

    @declared_attr
    def relationship_instance_fk(cls):
        return cls.foreign_key(RelationshipInstanceBase, nullable=True)

    @declared_attr
    def relationship_instance_name(cls):
        return association_proxy('relationship_instance', cls.name_column_name())

    @declared_attr
    def relationship_instance(cls):
        return cls.one_to_many_relationship('relationship_instance_fk')

    @declared_attr
    def plugin_fk(cls):
        return cls.foreign_key(PluginBase, nullable=True)

    @declared_attr
    def plugin(cls):
        return cls.one_to_many_relationship('plugin_fk')

    @declared_attr
    def plugin_name(cls):
        return association_proxy('plugin', 'name')

    @declared_attr
    def execution_fk(cls):
        return cls.foreign_key(ExecutionBase, nullable=True)

    @declared_attr
    def execution(cls):
        return cls.one_to_many_relationship('execution_fk')

    @declared_attr
    def execution_name(cls):
        return association_proxy('execution', cls.name_column_name())

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
        if value < 1 and value != TaskBase.INFINITE_RETRIES:
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
    operation_mapping = Column(String)
    inputs = Column(Dict)

    @property
    def actor(self):
        """
        Return the actor of the task
        :return:
        """
        return self.node_instance or self.relationship_instance

    @classmethod
    def as_node_instance(cls, instance, **kwargs):
        return cls(node_instance=instance, **kwargs)

    @classmethod
    def as_relationship_instance(cls, instance, **kwargs):
        return cls(relationship_instance=instance, **kwargs)
