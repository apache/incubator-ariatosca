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
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

from aria.orchestrator.exceptions import TaskAbortException, TaskRetryException

from .type import List, Dict
from .structure import ModelMixin

__all__ = (
    'ServiceInstanceUpdateStepBase',
    'ServiceInstanceUpdateBase',
    'ServiceInstanceModificationBase',
    'Execution',
    'PluginBase',
    'TaskBase'
)

# pylint: disable=no-self-argument, no-member, abstract-method


class Execution(ModelMixin):
    """
    Execution model representation.
    """
    # Needed only for pylint. the id will be populated by sqlalcehmy and the proper column.
    __tablename__ = 'execution'

    __private_fields__ = ['service_instance_fk']

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
    def service_template(cls):
        return association_proxy('service_instance', 'service_template')

    @declared_attr
    def service_instance_fk(cls):
        return cls.foreign_key('service_instance')

    @declared_attr
    def service_instance(cls):
        return cls.many_to_one_relationship('service_instance')

    @declared_attr
    def service_instance_name(cls):
        return association_proxy('service_instance', cls.name_column_name())

    @declared_attr
    def service_template_name(cls):
        return association_proxy('service_instance', 'service_template_name')

    def __str__(self):
        return '<{0} id=`{1}` (status={2})>'.format(
            self.__class__.__name__,
            getattr(self, self.name_column_name()),
            self.status
        )


class ServiceInstanceUpdateBase(ModelMixin):
    """
    Deployment update model representation.
    """
    # Needed only for pylint. the id will be populated by sqlalcehmy and the proper column.
    steps = None

    __tablename__ = 'service_instance_update'
    __private_fields__ = ['service_instance_fk',
                          'execution_fk']

    _private_fields = ['execution_fk', 'deployment_fk']

    created_at = Column(DateTime, nullable=False, index=True)
    service_instance_plan = Column(Dict, nullable=False)
    service_instance_update_node_instances = Column(Dict)
    service_instance_update_service_instance = Column(Dict)
    service_instance_update_nodes = Column(List)
    modified_entity_ids = Column(Dict)
    state = Column(Text)

    @declared_attr
    def execution_fk(cls):
        return cls.foreign_key('execution', nullable=True)

    @declared_attr
    def execution(cls):
        return cls.many_to_one_relationship('execution')

    @declared_attr
    def execution_name(cls):
        return association_proxy('execution', cls.name_column_name())

    @declared_attr
    def service_instance_fk(cls):
        return cls.foreign_key('service_instance')

    @declared_attr
    def service_instance(cls):
        return cls.many_to_one_relationship('service_instance')

    @declared_attr
    def service_instance_name(cls):
        return association_proxy('service_instance', cls.name_column_name())

    def to_dict(self, suppress_error=False, **kwargs):
        dep_update_dict = super(ServiceInstanceUpdateBase, self).to_dict(suppress_error)     #pylint: disable=no-member
        # Taking care of the fact the DeploymentSteps are _BaseModels
        dep_update_dict['steps'] = [step.to_dict() for step in self.steps]
        return dep_update_dict


class ServiceInstanceUpdateStepBase(ModelMixin):
    """
    Deployment update step model representation.
    """
    # Needed only for pylint. the id will be populated by sqlalcehmy and the proper column.
    __tablename__ = 'service_instance_update_step'
    __private_fields__ = ['service_instance_update_fk']

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
    def service_instance_update_fk(cls):
        return cls.foreign_key('service_instance_update')

    @declared_attr
    def service_instance_update(cls):
        return cls.many_to_one_relationship('service_instance_update',
                                            backreference='steps')

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


class ServiceInstanceModificationBase(ModelMixin):
    """
    Deployment modification model representation.
    """
    __tablename__ = 'service_instance_modification'
    __private_fields__ = ['service_instance_fk']

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
    def service_instance_fk(cls):
        return cls.foreign_key('service_instance')

    @declared_attr
    def service_instance(cls):
        return cls.many_to_one_relationship('service_instance',
                                            backreference='modifications')

    @declared_attr
    def service_instance_name(cls):
        return association_proxy('service_instance', cls.name_column_name())


class PluginBase(ModelMixin):
    """
    Plugin model representation.
    """
    __tablename__ = 'plugin'

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
    __tablename__ = 'task'
    __private_fields__ = ['node_fk',
                          'relationship_fk',
                          'execution_fk',
                          'plugin_fk']

    @declared_attr
    def node_fk(cls):
        return cls.foreign_key('node', nullable=True)

    @declared_attr
    def node_name(cls):
        return association_proxy('node', cls.name_column_name())

    @declared_attr
    def node(cls):
        return cls.many_to_one_relationship('node')

    @declared_attr
    def relationship_fk(cls):
        return cls.foreign_key('relationship', nullable=True)

    @declared_attr
    def relationship_name(cls):
        return association_proxy('relationships', cls.name_column_name())

    @declared_attr
    def relationship(cls):
        return cls.many_to_one_relationship('relationship')

    @declared_attr
    def plugin_fk(cls):
        return cls.foreign_key('plugin', nullable=True)

    @declared_attr
    def plugin(cls):
        return cls.many_to_one_relationship('plugin')

    @declared_attr
    def execution_fk(cls):
        return cls.foreign_key('execution', nullable=True)

    @declared_attr
    def execution(cls):
        return cls.many_to_one_relationship('execution')

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

    RUNS_ON_SOURCE = 'source'
    RUNS_ON_TARGET = 'target'
    RUNS_ON_NODE_INSTANCE = 'node_instance'
    RUNS_ON = (RUNS_ON_NODE_INSTANCE, RUNS_ON_SOURCE, RUNS_ON_TARGET)

    @orm.validates('max_attempts')
    def validate_max_attempts(self, _, value):                                  # pylint: disable=no-self-use
        """Validates that max attempts is either -1 or a positive number"""
        if value < 1 and value != TaskBase.INFINITE_RETRIES:
            raise ValueError('Max attempts can be either -1 (infinite) or any positive number. '
                             'Got {value}'.format(value=value))
        return value

    INFINITE_RETRIES = -1

    status = Column(Enum(*STATES, name='status'), default=PENDING)

    due_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, default=None)
    ended_at = Column(DateTime, default=None)
    max_attempts = Column(Integer, default=1)
    retry_count = Column(Integer, default=0)
    retry_interval = Column(Float, default=0)
    ignore_failure = Column(Boolean, default=False)

    # Operation specific fields
    implementation = Column(String)
    inputs = Column(Dict)
    # This is unrelated to the plugin of the task. This field is related to the plugin name
    # received from the blueprint.
    plugin_name = Column(String)
    _runs_on = Column(Enum(*RUNS_ON, name='runs_on'), name='runs_on')

    @property
    def runs_on(self):
        if self._runs_on == self.RUNS_ON_NODE_INSTANCE:
            return self.node
        elif self._runs_on == self.RUNS_ON_SOURCE:
            return self.relationship.source_node  # pylint: disable=no-member
        elif self._runs_on == self.RUNS_ON_TARGET:
            return self.relationship.target_node  # pylint: disable=no-member
        return None

    @property
    def actor(self):
        """
        Return the actor of the task
        :return:
        """
        return self.node or self.relationship

    @classmethod
    def as_node_instance(cls, instance, runs_on, **kwargs):
        return cls(node=instance, _runs_on=runs_on, **kwargs)

    @classmethod
    def as_relationship_instance(cls, instance, runs_on, **kwargs):
        return cls(relationship=instance, _runs_on=runs_on, **kwargs)

    @staticmethod
    def abort(message=None):
        raise TaskAbortException(message)

    @staticmethod
    def retry(message=None, retry_interval=None):
        raise TaskRetryException(message, retry_interval=retry_interval)


class LogBase(ModelMixin):
    __tablename__ = 'log'

    @declared_attr
    def execution_fk(cls):
        return cls.foreign_key('execution')

    @declared_attr
    def execution(cls):
        return cls.many_to_one_relationship('execution')

    @declared_attr
    def task_fk(cls):
        return cls.foreign_key('task', nullable=True)

    @declared_attr
    def task(cls):
        return cls.many_to_one_relationship('task')

    level = Column(String)
    msg = Column(String)
    created_at = Column(DateTime, index=True)
    actor = Column(String)

    def __repr__(self):
        return "<{self.created_at}: [{self.level}] @{self.actor}> {msg}".format(
            self=self, msg=self.msg[:50])
