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
Workflow tasks
"""

from contextlib import contextmanager
from datetime import datetime
from functools import (
    partial,
    wraps,
)


from ....modeling import models
from ...context import operation as operation_context
from .. import exceptions


def _locked(func=None):
    if func is None:
        return partial(_locked, func=_locked)

    @wraps(func)
    def _wrapper(self, value, **kwargs):
        if self._update_fields is None:
            raise exceptions.TaskException('Task is not in update mode')
        return func(self, value, **kwargs)
    return _wrapper


class BaseTask(object):
    """
    Base class for Task objects
    """

    def __init__(self, id, executor, *args, **kwargs):
        super(BaseTask, self).__init__(*args, **kwargs)
        self._id = id
        self._executor = executor

    def execute(self):
        return self._executor.execute(self)

    @property
    def id(self):
        """
        :return: the task's id
        """
        return self._id


class StubTask(BaseTask):
    """
    Base stub task for marker user tasks that only mark the start/end of a workflow
    or sub-workflow
    """
    STARTED = models.Task.STARTED
    SUCCESS = models.Task.SUCCESS

    def __init__(self, *args, **kwargs):
        super(StubTask, self).__init__(*args, **kwargs)
        self.status = models.Task.PENDING
        self.due_at = datetime.utcnow()

    def has_ended(self):
        return self.status == self.SUCCESS

    def is_waiting(self):
        return not self.has_ended()


class StartWorkflowTask(StubTask):
    """
    Task marking a workflow start
    """
    pass


class EndWorkflowTask(StubTask):
    """
    Task marking a workflow end
    """
    pass


class StartSubWorkflowTask(StubTask):
    """
    Task marking a subworkflow start
    """
    pass


class EndSubWorkflowTask(StubTask):
    """
    Task marking a subworkflow end
    """
    pass


class OperationTask(BaseTask):
    """
    Operation task
    """
    def __init__(self, api_task, *args, **kwargs):
        # If no executor is provided, we infer that this is an empty task which does not need to be
        # executed.
        super(OperationTask, self).__init__(id=api_task.id, *args, **kwargs)
        self._workflow_context = api_task._workflow_context
        self.interface_name = api_task.interface_name
        self.operation_name = api_task.operation_name
        model_storage = api_task._workflow_context.model

        actor = getattr(api_task.actor, '_wrapped', api_task.actor)

        base_task_model = model_storage.task.model_cls
        if isinstance(actor, models.Node):
            context_cls = operation_context.NodeOperationContext
            create_task_model = base_task_model.for_node
        elif isinstance(actor, models.Relationship):
            context_cls = operation_context.RelationshipOperationContext
            create_task_model = base_task_model.for_relationship
        else:
            raise RuntimeError('No operation context could be created for {actor.model_cls}'
                               .format(actor=actor))

        task_model = create_task_model(
            name=api_task.name,
            actor=actor,
            status=base_task_model.PENDING,
            max_attempts=api_task.max_attempts,
            retry_interval=api_task.retry_interval,
            ignore_failure=api_task.ignore_failure,
            execution=self._workflow_context.execution,

            # Only non-stub tasks have these fields
            plugin=api_task.plugin,
            function=api_task.function,
            arguments=api_task.arguments
        )
        self._workflow_context.model.task.put(task_model)

        self._ctx = context_cls(name=api_task.name,
                                model_storage=self._workflow_context.model,
                                resource_storage=self._workflow_context.resource,
                                service_id=self._workflow_context._service_id,
                                task_id=task_model.id,
                                actor_id=actor.id,
                                execution_id=self._workflow_context._execution_id,
                                workdir=self._workflow_context._workdir)
        self._task_id = task_model.id
        self._update_fields = None

    @contextmanager
    def _update(self):
        """
        A context manager which puts the task into update mode, enabling fields update.
        :yields: None
        """
        self._update_fields = {}
        try:
            yield
            for key, value in self._update_fields.items():
                setattr(self.model_task, key, value)
            self.model_task = self.model_task
        finally:
            self._update_fields = None

    @property
    def model_task(self):
        """
        Returns the task model in storage
        :return: task in storage
        """
        return self._workflow_context.model.task.get(self._task_id)

    @model_task.setter
    def model_task(self, value):
        self._workflow_context.model.task.put(value)

    @property
    def context(self):
        """
        Contexts for the operation
        :return:
        """
        return self._ctx

    @property
    def status(self):
        """
        Returns the task status
        :return: task status
        """
        return self.model_task.status

    @status.setter
    @_locked
    def status(self, value):
        self._update_fields['status'] = value

    @property
    def started_at(self):
        """
        Returns when the task started
        :return: when task started
        """
        return self.model_task.started_at

    @started_at.setter
    @_locked
    def started_at(self, value):
        self._update_fields['started_at'] = value

    @property
    def ended_at(self):
        """
        Returns when the task ended
        :return: when task ended
        """
        return self.model_task.ended_at

    @ended_at.setter
    @_locked
    def ended_at(self, value):
        self._update_fields['ended_at'] = value

    @property
    def attempts_count(self):
        """
        Returns the attempts count for the task
        :return: attempts count
        """
        return self.model_task.attempts_count

    @attempts_count.setter
    @_locked
    def attempts_count(self, value):
        self._update_fields['attempts_count'] = value

    @property
    def due_at(self):
        """
        Returns the minimum datetime in which the task can be executed
        :return: eta
        """
        return self.model_task.due_at

    @due_at.setter
    @_locked
    def due_at(self, value):
        self._update_fields['due_at'] = value

    def __getattr__(self, attr):
        try:
            return getattr(self.model_task, attr)
        except AttributeError:
            return super(OperationTask, self).__getattribute__(attr)
