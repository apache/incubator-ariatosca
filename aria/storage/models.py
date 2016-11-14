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

from datetime import datetime
from types import NoneType

from .structures import Field, IterPointerField, Model, uuid_generator, PointerField

__all__ = (
    'Model',
    'Blueprint',
    'Snapshot',
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

# todo: sort this, maybe move from mgr or move from aria???
ACTION_TYPES = ()
ENTITY_TYPES = ()


class Blueprint(Model):
    """
    A Model which represents a blueprint
    """
    plan = Field(type=dict)
    id = Field(type=basestring, default=uuid_generator)
    description = Field(type=(basestring, NoneType))
    created_at = Field(type=datetime)
    updated_at = Field(type=datetime)
    main_file_name = Field(type=basestring)


class Snapshot(Model):
    """
    A Model which represents a snapshot
    """
    CREATED = 'created'
    FAILED = 'failed'
    CREATING = 'creating'
    UPLOADED = 'uploaded'
    END_STATES = [CREATED, FAILED, UPLOADED]

    id = Field(type=basestring, default=uuid_generator)
    created_at = Field(type=datetime)
    status = Field(type=basestring)
    error = Field(type=basestring, default=None)


class Deployment(Model):
    """
    A Model which represents a deployment
    """
    id = Field(type=basestring, default=uuid_generator)
    description = Field(type=(basestring, NoneType))
    created_at = Field(type=datetime)
    updated_at = Field(type=datetime)
    blueprint_id = Field(type=basestring)
    workflows = Field(type=dict)
    inputs = Field(type=dict, default=lambda: {})
    policy_types = Field(type=dict, default=lambda: {})
    policy_triggers = Field(type=dict, default=lambda: {})
    groups = Field(type=dict, default=lambda: {})
    outputs = Field(type=dict, default=lambda: {})
    scaling_groups = Field(type=dict, default=lambda: {})


class DeploymentUpdateStep(Model):
    """
    A Model which represents a deployment update step
    """
    id = Field(type=basestring, default=uuid_generator)
    action = Field(type=basestring, choices=ACTION_TYPES)
    entity_type = Field(type=basestring, choices=ENTITY_TYPES)
    entity_id = Field(type=basestring)
    supported = Field(type=bool, default=True)

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


class DeploymentUpdate(Model):
    """
    A Model which represents a deployment update
    """
    INITIALIZING = 'initializing'
    SUCCESSFUL = 'successful'
    UPDATING = 'updating'
    FINALIZING = 'finalizing'
    EXECUTING_WORKFLOW = 'executing_workflow'
    FAILED = 'failed'

    STATES = [
        INITIALIZING,
        SUCCESSFUL,
        UPDATING,
        FINALIZING,
        EXECUTING_WORKFLOW,
        FAILED,
    ]

    # '{0}-{1}'.format(kwargs['deployment_id'], uuid4())
    id = Field(type=basestring, default=uuid_generator)
    deployment_id = Field(type=basestring)
    state = Field(type=basestring, choices=STATES, default=INITIALIZING)
    deployment_plan = Field()
    deployment_update_nodes = Field(default=None)
    deployment_update_node_instances = Field(default=None)
    deployment_update_deployment = Field(default=None)
    modified_entity_ids = Field(default=None)
    execution_id = Field(type=basestring)
    steps = IterPointerField(type=DeploymentUpdateStep, default=())


class Execution(Model):
    """
    A Model which represents an execution
    """

    class _Validation(object):

        @staticmethod
        def execution_status_transition_validation(_, value, instance):
            """Validation function that verifies execution status transitions are OK"""
            try:
                current_status = instance.status
            except AttributeError:
                return
            valid_transitions = Execution.VALID_TRANSITIONS.get(current_status, [])
            if current_status != value and value not in valid_transitions:
                raise ValueError('Cannot change execution status from {current} to {new}'.format(
                    current=current_status,
                    new=value))

    TERMINATED = 'terminated'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    PENDING = 'pending'
    STARTED = 'started'
    CANCELLING = 'cancelling'
    STATES = (
        TERMINATED,
        FAILED,
        CANCELLED,
        PENDING,
        STARTED,
        CANCELLING,
    )
    END_STATES = [TERMINATED, FAILED, CANCELLED]
    ACTIVE_STATES = [state for state in STATES if state not in END_STATES]
    VALID_TRANSITIONS = {
        PENDING: [STARTED, CANCELLED],
        STARTED: END_STATES + [CANCELLING],
        CANCELLING: END_STATES
    }

    id = Field(type=basestring, default=uuid_generator)
    status = Field(type=basestring, choices=STATES,
                   validation_func=_Validation.execution_status_transition_validation)
    deployment_id = Field(type=basestring)
    workflow_id = Field(type=basestring)
    blueprint_id = Field(type=basestring)
    created_at = Field(type=datetime, default=datetime.utcnow)
    started_at = Field(type=datetime, default=None)
    ended_at = Field(type=datetime, default=None)
    error = Field(type=basestring, default=None)
    parameters = Field()


class Relationship(Model):
    """
    A Model which represents a relationship
    """
    id = Field(type=basestring, default=uuid_generator)
    target_id = Field(type=basestring)
    source_interfaces = Field(type=dict)
    source_operations = Field(type=dict)
    target_interfaces = Field(type=dict)
    target_operations = Field(type=dict)
    type = Field(type=basestring)
    type_hierarchy = Field(type=list)
    properties = Field(type=dict)


class Node(Model):
    """
    A Model which represents a node
    """
    id = Field(type=basestring, default=uuid_generator)
    blueprint_id = Field(type=basestring)
    type = Field(type=basestring)
    type_hierarchy = Field()
    number_of_instances = Field(type=int)
    planned_number_of_instances = Field(type=int)
    deploy_number_of_instances = Field(type=int)
    host_id = Field(type=basestring, default=None)
    properties = Field(type=dict)
    operations = Field(type=dict)
    plugins = Field(type=list, default=())
    relationships = IterPointerField(type=Relationship)
    plugins_to_install = Field(type=list, default=())
    min_number_of_instances = Field(type=int)
    max_number_of_instances = Field(type=int)

    def relationships_by_target(self, target_id):
        """
        Retreives all of the relationship by target.
        :param target_id: the node id of the target  of the relationship
        :yields: a relationship which target and node with the specified target_id
        """
        for relationship in self.relationships:
            if relationship.target_id == target_id:
                yield relationship
        # todo: maybe add here Exception if isn't exists (didn't yield one's)


class RelationshipInstance(Model):
    """
    A Model which represents a relationship instance
    """
    id = Field(type=basestring, default=uuid_generator)
    target_id = Field(type=basestring)
    target_name = Field(type=basestring)
    type = Field(type=basestring)
    relationship = PointerField(type=Relationship)


class NodeInstance(Model):
    """
    A Model which represents a node instance
    """
    # todo: add statuses
    UNINITIALIZED = 'uninitialized'
    INITIALIZING = 'initializing'
    CREATING = 'creating'
    CONFIGURING = 'configuring'
    STARTING = 'starting'
    DELETED = 'deleted'
    STOPPING = 'stopping'
    DELETING = 'deleting'
    STATES = (
        UNINITIALIZED,
        INITIALIZING,
        CREATING,
        CONFIGURING,
        STARTING,
        DELETED,
        STOPPING,
        DELETING
    )

    id = Field(type=basestring, default=uuid_generator)
    deployment_id = Field(type=basestring)
    runtime_properties = Field(type=dict)
    state = Field(type=basestring, choices=STATES, default=UNINITIALIZED)
    version = Field(type=(basestring, NoneType))
    relationship_instances = IterPointerField(type=RelationshipInstance)
    node = PointerField(type=Node)
    host_id = Field(type=basestring, default=None)
    scaling_groups = Field(default=())

    def relationships_by_target(self, target_id):
        """
        Retreives all of the relationship by target.
        :param target_id: the instance id of the target of the relationship
        :yields: a relationship instance which target and node with the specified target_id
        """
        for relationship_instance in self.relationship_instances:
            if relationship_instance.target_id == target_id:
                yield relationship_instance
        # todo: maybe add here Exception if isn't exists (didn't yield one's)


class DeploymentModification(Model):
    """
    A Model which represents a deployment modification
    """
    STARTED = 'started'
    FINISHED = 'finished'
    ROLLEDBACK = 'rolledback'
    END_STATES = [FINISHED, ROLLEDBACK]

    id = Field(type=basestring, default=uuid_generator)
    deployment_id = Field(type=basestring)
    modified_nodes = Field(type=(dict, NoneType))
    added_and_related = IterPointerField(type=NodeInstance)
    removed_and_related = IterPointerField(type=NodeInstance)
    extended_and_related = IterPointerField(type=NodeInstance)
    reduced_and_related = IterPointerField(type=NodeInstance)
    # before_modification = IterPointerField(type=NodeInstance)
    status = Field(type=basestring, choices=(STARTED, FINISHED, ROLLEDBACK))
    created_at = Field(type=datetime)
    ended_at = Field(type=(datetime, NoneType))
    context = Field()


class ProviderContext(Model):
    """
    A Model which represents a provider context
    """
    id = Field(type=basestring, default=uuid_generator)
    context = Field(type=dict)
    name = Field(type=basestring)


class Plugin(Model):
    """
    A Model which represents a plugin
    """
    id = Field(type=basestring, default=uuid_generator)
    package_name = Field(type=basestring)
    archive_name = Field(type=basestring)
    package_source = Field(type=dict)
    package_version = Field(type=basestring)
    supported_platform = Field(type=basestring)
    distribution = Field(type=basestring)
    distribution_version = Field(type=basestring)
    distribution_release = Field(type=basestring)
    wheels = Field()
    excluded_wheels = Field()
    supported_py_versions = Field(type=list)
    uploaded_at = Field(type=datetime)


class Task(Model):
    """
    A Model which represents an task
    """

    class _Validation(object):

        @staticmethod
        def validate_max_attempts(_, value, *args):
            """Validates that max attempts is either -1 or a positive number"""
            if value < 1 and value != Task.INFINITE_RETRIES:
                raise ValueError('Max attempts can be either -1 (infinite) or any positive number. '
                                 'Got {value}'.format(value=value))

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
    INFINITE_RETRIES = -1

    id = Field(type=basestring, default=uuid_generator)
    status = Field(type=basestring, choices=STATES, default=PENDING)
    execution_id = Field(type=basestring)
    due_at = Field(type=datetime, default=datetime.utcnow)
    started_at = Field(type=datetime, default=None)
    ended_at = Field(type=datetime, default=None)
    max_attempts = Field(type=int, default=1, validation_func=_Validation.validate_max_attempts)
    retry_count = Field(type=int, default=0)
    retry_interval = Field(type=(int, float), default=0)
    ignore_failure = Field(type=bool, default=False)

    # Operation specific fields
    name = Field(type=basestring)
    operation_details = Field(type=dict)
    node_instance = PointerField(type=NodeInstance)
    inputs = Field(type=dict, default=lambda: {})
