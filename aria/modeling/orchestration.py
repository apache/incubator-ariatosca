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
ARIA modeling orchestration module
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
    PickleType)
from sqlalchemy.ext.declarative import declared_attr

from ..orchestrator.exceptions import (TaskAbortException, TaskRetryException)
from . import mixins
from . import (
    relationship,
    types as modeling_types
)


class ExecutionBase(mixins.ModelMixin):
    """
    Workflow execution.
    """

    __tablename__ = 'execution'

    __private_fields__ = ('service_fk',
                          'service_template')

    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    PENDING = 'pending'
    STARTED = 'started'
    CANCELLING = 'cancelling'

    STATES = (SUCCEEDED, FAILED, CANCELLED, PENDING, STARTED, CANCELLING)
    END_STATES = (SUCCEEDED, FAILED, CANCELLED)

    VALID_TRANSITIONS = {
        PENDING: (STARTED, CANCELLED),
        STARTED: END_STATES + (CANCELLING,),
        CANCELLING: END_STATES,
        # Retrying
        CANCELLED: PENDING,
        FAILED: PENDING
    }

    # region one_to_many relationships

    @declared_attr
    def inputs(cls):
        """
        Execution parameters.

        :type: {:obj:`basestring`: :class:`Input`}
        """
        return relationship.one_to_many(cls, 'input', dict_key='name')

    @declared_attr
    def tasks(cls):
        """
        Tasks.

        :type: [:class:`Task`]
        """
        return relationship.one_to_many(cls, 'task')

    @declared_attr
    def logs(cls):
        """
        Log messages for the execution (including log messages for its tasks).

        :type: [:class:`Log`]
        """
        return relationship.one_to_many(cls, 'log')

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service(cls):
        """
        Associated service.

        :type: :class:`Service`
        """
        return relationship.many_to_one(cls, 'service')

    # endregion

    # region association proxies

    @declared_attr
    def service_name(cls):
        return relationship.association_proxy('service', cls.name_column_name())

    @declared_attr
    def service_template(cls):
        return relationship.association_proxy('service', 'service_template')

    @declared_attr
    def service_template_name(cls):
        return relationship.association_proxy('service', 'service_template_name')

    # endregion

    # region foreign keys

    @declared_attr
    def service_fk(cls):
        return relationship.foreign_key('service')

    # endregion

    created_at = Column(DateTime, index=True, doc="""
    Creation timestamp.

    :type: :class:`~datetime.datetime`
    """)

    started_at = Column(DateTime, nullable=True, index=True, doc="""
    Started timestamp.

    :type: :class:`~datetime.datetime`
    """)

    ended_at = Column(DateTime, nullable=True, index=True, doc="""
    Ended timestamp.

    :type: :class:`~datetime.datetime`
    """)

    error = Column(Text, nullable=True, doc="""
    Error message.

    :type: :obj:`basestring`
    """)

    status = Column(Enum(*STATES, name='execution_status'), default=PENDING, doc="""
    Status.

    :type: :obj:`basestring`
    """)

    workflow_name = Column(Text, doc="""
    Workflow name.

    :type: :obj:`basestring`
    """)

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

    def has_ended(self):
        return self.status in self.END_STATES

    def is_active(self):
        return not self.has_ended() and self.status != self.PENDING

    def __str__(self):
        return '<{0} id=`{1}` (status={2})>'.format(
            self.__class__.__name__,
            getattr(self, self.name_column_name()),
            self.status
        )


class TaskBase(mixins.ModelMixin):
    """
    Represents the smallest unit of stateful execution in ARIA. The task state includes inputs,
    outputs, as well as an atomic status, ensuring that the task can only be running once at any
    given time.

    The Python :attr:`function` is usually provided by an associated :class:`Plugin`. The
    :attr:`arguments` of the function should be set according to the specific signature of the
    function.

    Tasks may be "one shot" or may be configured to run repeatedly in the case of failure.

    Tasks are often based on :class:`Operation`, and thus act on either a :class:`Node` or a
    :class:`Relationship`, however this is not required.
    """

    __tablename__ = 'task'

    __private_fields__ = ('node_fk',
                          'relationship_fk',
                          'plugin_fk',
                          'execution_fk')

    START_WORKFLOW = 'start_workflow'
    END_WORKFLOW = 'end_workflow'
    START_SUBWROFKLOW = 'start_subworkflow'
    END_SUBWORKFLOW = 'end_subworkflow'
    STUB = 'stub'
    CONDITIONAL = 'conditional'

    STUB_TYPES = (
        START_WORKFLOW,
        START_SUBWROFKLOW,
        END_WORKFLOW,
        END_SUBWORKFLOW,
        STUB,
        CONDITIONAL,
    )

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
    INFINITE_RETRIES = -1

    # region one_to_many relationships

    @declared_attr
    def logs(cls):
        """
        Log messages.

        :type: [:class:`Log`]
        """
        return relationship.one_to_many(cls, 'log')

    @declared_attr
    def arguments(cls):
        """
        Arguments sent to the Python :attr:`function``.

        :type: {:obj:`basestring`: :class:`Argument`}
        """
        return relationship.one_to_many(cls, 'argument', dict_key='name')

    # endregion

    # region many_one relationships

    @declared_attr
    def execution(cls):
        """
        Containing execution.

        :type: :class:`Execution`
        """
        return relationship.many_to_one(cls, 'execution')

    @declared_attr
    def node(cls):
        """
        Node actor (can be ``None``).

        :type: :class:`Node`
        """
        return relationship.many_to_one(cls, 'node')

    @declared_attr
    def relationship(cls):
        """
        Relationship actor (can be ``None``).

        :type: :class:`Relationship`
        """
        return relationship.many_to_one(cls, 'relationship')

    @declared_attr
    def plugin(cls):
        """
        Associated plugin.

        :type: :class:`Plugin`
        """
        return relationship.many_to_one(cls, 'plugin')

    # endregion

    # region association proxies

    @declared_attr
    def node_name(cls):
        return relationship.association_proxy('node', cls.name_column_name())

    @declared_attr
    def relationship_name(cls):
        return relationship.association_proxy('relationship', cls.name_column_name())

    @declared_attr
    def execution_name(cls):
        return relationship.association_proxy('execution', cls.name_column_name())

    # endregion

    # region foreign keys

    @declared_attr
    def execution_fk(cls):
        return relationship.foreign_key('execution', nullable=True)

    @declared_attr
    def node_fk(cls):
        return relationship.foreign_key('node', nullable=True)

    @declared_attr
    def relationship_fk(cls):
        return relationship.foreign_key('relationship', nullable=True)

    @declared_attr
    def plugin_fk(cls):
        return relationship.foreign_key('plugin', nullable=True)

    # endregion

    status = Column(Enum(*STATES, name='status'), default=PENDING, doc="""
    Current atomic status ('pending', 'retrying', 'sent', 'started', 'success', 'failed').

    :type: :obj:`basestring`
    """)

    due_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow(), doc="""
    Timestamp to start the task.

    :type: :class:`~datetime.datetime`
    """)

    started_at = Column(DateTime, default=None, doc="""
    Started timestamp.

    :type: :class:`~datetime.datetime`
    """)

    ended_at = Column(DateTime, default=None, doc="""
    Ended timestamp.

    :type: :class:`~datetime.datetime`
    """)

    attempts_count = Column(Integer, default=1, doc="""
    How many attempts occurred.

    :type: :class:`~datetime.datetime`
    """)

    function = Column(String, doc="""
    Full path to Python function.

    :type: :obj:`basestring`
    """)

    max_attempts = Column(Integer, default=1, doc="""
    Maximum number of attempts allowed in case of task failure.

    :type: :obj:`int`
    """)

    retry_interval = Column(Float, default=0, doc="""
    Interval between task retry attemps (in seconds).

    :type: :obj:`float`
    """)

    ignore_failure = Column(Boolean, default=False, doc="""
    Set to ``True`` to ignore failures.

    :type: :obj:`bool`
    """)

    interface_name = Column(String, doc="""
    Name of interface on node or relationship.

    :type: :obj:`basestring`
    """)

    operation_name = Column(String, doc="""
    Name of operation in interface on node or relationship.

    :type: :obj:`basestring`
    """)

    _api_id = Column(String)
    _executor = Column(PickleType)
    _context_cls = Column(PickleType)
    _stub_type = Column(Enum(*STUB_TYPES))

    @property
    def actor(self):
        """
        Actor of the task (node or relationship).
        """
        return self.node or self.relationship

    @orm.validates('max_attempts')
    def validate_max_attempts(self, _, value):                                                      # pylint: disable=no-self-use
        """
        Validates that max attempts is either -1 or a positive number.
        """
        if value < 1 and value != TaskBase.INFINITE_RETRIES:
            raise ValueError('Max attempts can be either -1 (infinite) or any positive number. '
                             'Got {value}'.format(value=value))
        return value

    @staticmethod
    def abort(message=None):
        raise TaskAbortException(message)

    @staticmethod
    def retry(message=None, retry_interval=None):
        raise TaskRetryException(message, retry_interval=retry_interval)

    @declared_attr
    def dependencies(cls):
        return relationship.many_to_many(cls, self=True)

    def has_ended(self):
        return self.status in (self.SUCCESS, self.FAILED)

    def is_waiting(self):
        if self._stub_type:
            return not self.has_ended()
        else:
            return self.status in (self.PENDING, self.RETRYING)

    @classmethod
    def from_api_task(cls, api_task, executor, **kwargs):
        instantiation_kwargs = {}

        if hasattr(api_task.actor, 'outbound_relationships'):
            instantiation_kwargs['node'] = api_task.actor
        elif hasattr(api_task.actor, 'source_node'):
            instantiation_kwargs['relationship'] = api_task.actor
        else:
            raise RuntimeError('No operation context could be created for {actor.model_cls}'
                               .format(actor=api_task.actor))

        instantiation_kwargs.update(
            {
                'name': api_task.name,
                'status': cls.PENDING,
                'max_attempts': api_task.max_attempts,
                'retry_interval': api_task.retry_interval,
                'ignore_failure': api_task.ignore_failure,
                'execution': api_task._workflow_context.execution,
                'interface_name': api_task.interface_name,
                'operation_name': api_task.operation_name,

                # Only non-stub tasks have these fields
                'plugin': api_task.plugin,
                'function': api_task.function,
                'arguments': api_task.arguments,
                '_context_cls': api_task._context_cls,
                '_executor': executor,
            }
        )

        instantiation_kwargs.update(**kwargs)

        return cls(**instantiation_kwargs)


class LogBase(mixins.ModelMixin):
    """
    Single log message.
    """

    __tablename__ = 'log'

    __private_fields__ = ('execution_fk',
                          'task_fk')

    # region many_to_one relationships

    @declared_attr
    def execution(cls):
        """
        Containing execution.

        :type: :class:`Execution`
        """
        return relationship.many_to_one(cls, 'execution')

    @declared_attr
    def task(cls):
        """
        Containing task (can be ``None``).

        :type: :class:`Task`
        """
        return relationship.many_to_one(cls, 'task')

    # endregion

    # region foreign keys

    @declared_attr
    def execution_fk(cls):
        return relationship.foreign_key('execution')

    @declared_attr
    def task_fk(cls):
        return relationship.foreign_key('task', nullable=True)

    # endregion

    level = Column(String, doc="""
    Log level.

    :type: :obj:`basestring`
    """)

    msg = Column(String, doc="""
    Log message.

    :type: :obj:`basestring`
    """)

    created_at = Column(DateTime, index=True, doc="""
    Creation timestamp.

    :type: :class:`~datetime.datetime`
    """)

    traceback = Column(Text, doc="""
    Error traceback in case of failure.

    :type: :class:`~datetime.datetime`
    """)

    def __str__(self):
        return self.msg

    def __repr__(self):
        name = (self.task.actor if self.task else self.execution).name
        return '{name}: {self.msg}'.format(name=name, self=self)


class PluginBase(mixins.ModelMixin):
    """
    Installed plugin.

    Plugins are usually packaged as `wagons <https://github.com/cloudify-cosmo/wagon>`__, which
    are archives of one or more `wheels <https://packaging.python.org/distributing/#wheels>`__.
    Most of these fields are indeed extracted from the installed wagon's metadata.
    """

    __tablename__ = 'plugin'

    # region one_to_many relationships

    @declared_attr
    def tasks(cls):
        """
        Associated Tasks.

        :type: [:class:`Task`]
        """
        return relationship.one_to_many(cls, 'task')

    # endregion

    archive_name = Column(Text, nullable=False, index=True, doc="""
    Filename (not the full path) of the wagon's archive, often with a ``.wgn`` extension.

    :type: :obj:`basestring`
    """)

    distribution = Column(Text, doc="""
    Name of the operating system on which the wagon was installed (e.g. ``ubuntu``).

    :type: :obj:`basestring`
    """)

    distribution_release = Column(Text, doc="""
    Release of the operating system on which the wagon was installed (e.g. ``trusty``).

    :type: :obj:`basestring`
    """)

    distribution_version = Column(Text, doc="""
    Version of the operating system on which the wagon was installed (e.g. ``14.04``).

    :type: :obj:`basestring`
    """)

    package_name = Column(Text, nullable=False, index=True, doc="""
    Primary Python package name used when the wagon was installed, which is one of the wheels in the
    wagon (e.g. ``cloudify-script-plugin``).

    :type: :obj:`basestring`
    """)

    package_source = Column(Text, doc="""
    Full install string for the primary Python package name used when the wagon was installed (e.g.
    ``cloudify-script-plugin==1.2``).

    :type: :obj:`basestring`
    """)

    package_version = Column(Text, doc="""
    Version for the primary Python package name used when the wagon was installed (e.g. ``1.2``).

    :type: :obj:`basestring`
    """)

    supported_platform = Column(Text, doc="""
    If the wheels are *all* pure Python then this would be "any", otherwise it would be the
    installed platform name (e.g. ``linux_x86_64``).

    :type: :obj:`basestring`
    """)

    supported_py_versions = Column(modeling_types.StrictList(basestring), doc="""
    Python versions supported by all the wheels (e.g. ``["py26", "py27"]``)

    :type: [:obj:`basestring`]
    """)

    wheels = Column(modeling_types.StrictList(basestring), nullable=False, doc="""
    Filenames of the wheels archived in the wagon, often with a ``.whl`` extension.

    :type: [:obj:`basestring`]
    """)

    uploaded_at = Column(DateTime, nullable=False, index=True, doc="""
    Timestamp for when the wagon was installed.

    :type: :class:`~datetime.datetime`
    """)


class ArgumentBase(mixins.ParameterMixin):
    """
    Python function argument parameter.
    """

    __tablename__ = 'argument'

    # region many_to_one relationships

    @declared_attr
    def task(cls):
        """
        Containing task (can be ``None``);

        :type: :class:`Task`
        """
        return relationship.many_to_one(cls, 'task')

    @declared_attr
    def operation(cls):
        """
        Containing operation (can be ``None``);

        :type: :class:`Operation`
        """
        return relationship.many_to_one(cls, 'operation')

    # endregion

    # region foreign keys

    @declared_attr
    def task_fk(cls):
        return relationship.foreign_key('task', nullable=True)

    @declared_attr
    def operation_fk(cls):
        return relationship.foreign_key('operation', nullable=True)

    # endregion
