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
classes:
    * Execution - execution implementation model.
    * Plugin - plugin implementation model.
    * Task - a task
"""

# pylint: disable=no-self-argument, no-member, abstract-method

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

from ..orchestrator.exceptions import (TaskAbortException, TaskRetryException)
from .types import Dict
from .mixins import ModelMixin
from . import (
    relationship,
    types as modeling_types
)


class ExecutionBase(ModelMixin):
    """
    Execution model representation.
    """

    __tablename__ = 'execution'

    __private_fields__ = ['service_fk',
                          'service_name',
                          'service_template',
                          'service_template_name']

    TERMINATED = 'terminated'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    PENDING = 'pending'
    STARTED = 'started'
    CANCELLING = 'cancelling'
    FORCE_CANCELLING = 'force_cancelling'

    STATES = [TERMINATED, FAILED, CANCELLED, PENDING, STARTED, CANCELLING, FORCE_CANCELLING]
    END_STATES = [TERMINATED, FAILED, CANCELLED]

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

    @property
    def has_ended(self):
        return self.status in self.END_STATES

    @property
    def is_active(self):
        return not self.has_ended

    @declared_attr
    def logs(cls):
        return relationship.one_to_many(cls, 'log')

    @declared_attr
    def service(cls):
        return relationship.many_to_one(cls, 'service')

    @declared_attr
    def tasks(cls):
        return relationship.one_to_many(cls, 'task')

    # region foreign keys

    @declared_attr
    def service_fk(cls):
        return relationship.foreign_key('service')

    # endregion

    # region association proxies

    @declared_attr
    def service_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('service', cls.name_column_name())

    @declared_attr
    def service_template(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('service', 'service_template')

    @declared_attr
    def service_template_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('service', 'service_template_name')

    # endregion

    def __str__(self):
        return '<{0} id=`{1}` (status={2})>'.format(
            self.__class__.__name__,
            getattr(self, self.name_column_name()),
            self.status
        )


class PluginBase(ModelMixin):
    """
    An installed plugin.

    Plugins are usually packaged as `wagons <https://github.com/cloudify-cosmo/wagon>`__, which
    are archives of one or more `wheels <https://packaging.python.org/distributing/#wheels>`__.
    Most of these fields are indeed extracted from the installed wagon's metadata.

    :ivar archive_name: Filename (not the full path) of the wagon's archive, often with a ".wgn"
                        extension
    :vartype archive_name: basestring
    :ivar distribution: The name of the operating system on which the wagon was installed (e.g.
                        "ubuntu")
    :vartype distribution: basestring
    :ivar distribution_release: The release of the operating system on which the wagon was installed
                                (e.g. "trusty")
    :vartype distribution_release: basestring
    :ivar distribution_version: The version of the operating system on which the wagon was installed
                                (e.g. "14.04")
    :vartype distribution_version: basestring
    :ivar package_name: The primary Python package name used when the wagon was installed, which is
                        one of the wheels in the wagon (e.g. "cloudify-script-plugin")
    :vartype package_name: basestring
    :ivar package_source: The full install string for the primary Python package name used when the
                          wagon was installed (e.g. "cloudify-script-plugin==1.2")
    :vartype package_source: basestring
    :ivar package_version: The version for the primary Python package name used when the wagon was
                           installed (e.g. "1.2")
    :vartype package_version: basestring
    :ivar supported_platform: If the wheels are *all* pure Python then this would be "any",
                              otherwise it would be the installed platform name (e.g.
                              "linux_x86_64")
    :vartype supported_platform: basestring
    :ivar supported_py_versions: The Python versions supported by all the wheels (e.g. ["py26",
                                 "py27"])
    :vartype supported_py_versions: [basestring]
    :ivar wheels: The filenames of the wheels archived in the wagon, often with a ".whl" extension
    :vartype wheels: [basestring]
    :ivar uploaded_at: Timestamp for when the wagon was installed
    :vartype uploaded_at: basestring
    """

    __tablename__ = 'plugin'

    @declared_attr
    def tasks(cls):
        return relationship.one_to_many(cls, 'task')

    archive_name = Column(Text, nullable=False, index=True)
    distribution = Column(Text)
    distribution_release = Column(Text)
    distribution_version = Column(Text)
    package_name = Column(Text, nullable=False, index=True)
    package_source = Column(Text)
    package_version = Column(Text)
    supported_platform = Column(Text)
    supported_py_versions = Column(modeling_types.StrictList(basestring))
    wheels = Column(modeling_types.StrictList(basestring), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, index=True)


class TaskBase(ModelMixin):
    """
    A Model which represents an task
    """

    __tablename__ = 'task'

    __private_fields__ = ['node_fk',
                          'relationship_fk',
                          'plugin_fk',
                          'execution_fk',
                          'node_name',
                          'relationship_name',
                          'execution_name']

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

    RUNS_ON_SOURCE = 'source'
    RUNS_ON_TARGET = 'target'
    RUNS_ON_NODE = 'node'
    RUNS_ON = (RUNS_ON_NODE, RUNS_ON_SOURCE, RUNS_ON_TARGET)

    INFINITE_RETRIES = -1

    @declared_attr
    def logs(cls):
        return relationship.one_to_many(cls, 'log')

    @declared_attr
    def node(cls):
        return relationship.many_to_one(cls, 'node')

    @declared_attr
    def relationship(cls):
        return relationship.many_to_one(cls, 'relationship')

    @declared_attr
    def plugin(cls):
        return relationship.many_to_one(cls, 'plugin')

    @declared_attr
    def execution(cls):
        return relationship.many_to_one(cls, 'execution')

    @declared_attr
    def inputs(cls):
        return relationship.many_to_many(cls, 'parameter', prefix='inputs', dict_key='name')

    status = Column(Enum(*STATES, name='status'), default=PENDING)

    due_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow())
    started_at = Column(DateTime, default=None)
    ended_at = Column(DateTime, default=None)
    max_attempts = Column(Integer, default=1)
    retry_count = Column(Integer, default=0)
    retry_interval = Column(Float, default=0)
    ignore_failure = Column(Boolean, default=False)

    # Operation specific fields
    implementation = Column(String)
    _runs_on = Column(Enum(*RUNS_ON, name='runs_on'), name='runs_on')

    @property
    def has_ended(self):
        return self.status in [self.SUCCESS, self.FAILED]

    @property
    def is_waiting(self):
        return self.status in [self.PENDING, self.RETRYING]

    @property
    def runs_on(self):
        if self._runs_on == self.RUNS_ON_NODE:
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

    @orm.validates('max_attempts')
    def validate_max_attempts(self, _, value):                                  # pylint: disable=no-self-use
        """Validates that max attempts is either -1 or a positive number"""
        if value < 1 and value != TaskBase.INFINITE_RETRIES:
            raise ValueError('Max attempts can be either -1 (infinite) or any positive number. '
                             'Got {value}'.format(value=value))
        return value

    # region foreign keys

    @declared_attr
    def node_fk(cls):
        return relationship.foreign_key('node', nullable=True)

    @declared_attr
    def relationship_fk(cls):
        return relationship.foreign_key('relationship', nullable=True)

    @declared_attr
    def plugin_fk(cls):
        return relationship.foreign_key('plugin', nullable=True)

    @declared_attr
    def execution_fk(cls):
        return relationship.foreign_key('execution', nullable=True)

    # endregion

    # region association proxies

    @declared_attr
    def node_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('node', cls.name_column_name())

    @declared_attr
    def relationship_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('relationship', cls.name_column_name())

    @declared_attr
    def execution_name(cls):
        """Required for use by SQLAlchemy queries"""
        return association_proxy('execution', cls.name_column_name())

    # endregion

    @classmethod
    def for_node(cls, instance, runs_on, **kwargs):
        return cls(node=instance, _runs_on=runs_on, **kwargs)

    @classmethod
    def for_relationship(cls, instance, runs_on, **kwargs):
        return cls(relationship=instance, _runs_on=runs_on, **kwargs)

    @staticmethod
    def abort(message=None):
        raise TaskAbortException(message)

    @staticmethod
    def retry(message=None, retry_interval=None):
        raise TaskRetryException(message, retry_interval=retry_interval)


class LogBase(ModelMixin):

    __tablename__ = 'log'

    __private_fields__ = ['execution_fk',
                          'task_fk']

    @declared_attr
    def execution(cls):
        return relationship.many_to_one(cls, 'execution')

    @declared_attr
    def task(cls):
        return relationship.many_to_one(cls, 'task')

    level = Column(String)
    msg = Column(String)
    created_at = Column(DateTime, index=True)
    actor = Column(String)

    # region foreign keys

    @declared_attr
    def execution_fk(cls):
        return relationship.foreign_key('execution')

    @declared_attr
    def task_fk(cls):
        return relationship.foreign_key('task', nullable=True)

    # endregion

    def __repr__(self):
        return "<{self.created_at}: [{self.level}] @{self.actor}> {msg}".format(
            self=self, msg=self.msg[:50])
