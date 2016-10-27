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

from ... import logger
from ...storage import models
from ...context import operation as operation_context
from .. import exceptions


def _locked(func=None):
    if func is None:
        return partial(_locked, func=_locked)

    @wraps(func)
    def _wrapper(self, value, **kwargs):
        if self._update_fields is None:
            raise exceptions.TaskException("Task is not in update mode")
        return func(self, value, **kwargs)
    return _wrapper


class BaseTask(logger.LoggerMixin):
    """
    Base class for Task objects
    """

    def __init__(self, id, *args, **kwargs):
        super(BaseTask, self).__init__(*args, **kwargs)
        self._id = id

    @property
    def id(self):
        """
        :return: the task's id
        """
        return self._id


class StubTask(BaseTask):
    """
    Base stub task for all tasks that don't actually run anything
    """

    def __init__(self, *args, **kwargs):
        super(StubTask, self).__init__(*args, **kwargs)
        self.status = models.Task.PENDING
        self.due_at = datetime.utcnow()


class StartWorkflowTask(StubTask):
    """
    Tasks marking a workflow start
    """
    pass


class EndWorkflowTask(StubTask):
    """
    Tasks marking a workflow end
    """
    pass


class StartSubWorkflowTask(StubTask):
    """
    Tasks marking a subworkflow start
    """
    pass


class EndSubWorkflowTask(StubTask):
    """
    Tasks marking a subworkflow end
    """
    pass


class OperationTask(BaseTask):
    """
    Operation tasks
    """

    def __init__(self, api_task, *args, **kwargs):
        super(OperationTask, self).__init__(id=api_task.id, **kwargs)
        self._workflow_context = api_task._workflow_context
        task_model = api_task._workflow_context.model.task.model_cls
        operation_task = task_model(
            id=api_task.id,
            name=api_task.name,
            operation_mapping=api_task.operation_mapping,
            actor=api_task.actor,
            inputs=api_task.inputs,
            status=task_model.PENDING,
            execution_id=self._workflow_context._execution_id,
            max_attempts=api_task.max_attempts,
            retry_interval=api_task.retry_interval,
            ignore_failure=api_task.ignore_failure
        )

        if isinstance(api_task.actor, models.NodeInstance):
            context_class = operation_context.NodeOperationContext
        elif isinstance(api_task.actor, models.RelationshipInstance):
            context_class = operation_context.RelationshipOperationContext
        else:
            raise RuntimeError('No operation context could be created for {0}'
                               .format(api_task.actor.model_cls))

        self._ctx = context_class(name=api_task.name,
                                  workflow_context=self._workflow_context,
                                  task=operation_task)
        self._workflow_context.model.task.store(operation_task)
        self._task_id = operation_task.id
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
            task = self.model_task
            for key, value in self._update_fields.items():
                setattr(task, key, value)
            self.model_task = task
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
        self._workflow_context.model.task.store(value)

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
    def retry_count(self):
        """
        Returns the retry count for the task
        :return: retry count
        """
        return self.model_task.retry_count

    @retry_count.setter
    @_locked
    def retry_count(self, value):
        self._update_fields['retry_count'] = value

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
