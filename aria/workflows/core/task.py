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

from ... import logger
from ...storage import models
from .. import exceptions


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


class BaseWorkflowTask(BaseTask):
    """
    Base class for all workflow wrapping tasks
    """

    def __init__(self, *args, **kwargs):
        super(BaseWorkflowTask, self).__init__(*args, **kwargs)
        self.status = models.Task.PENDING
        self.eta = datetime.now()


class StartWorkflowTask(BaseWorkflowTask):
    """
    Tasks marking a workflow start
    """
    pass


class EndWorkflowTask(BaseWorkflowTask):
    """
    Tasks marking a workflow end
    """
    pass


class StartSubWorkflowTask(BaseWorkflowTask):
    """
    Tasks marking a subworkflow start
    """
    pass


class EndSubWorkflowTask(BaseWorkflowTask):
    """
    Tasks marking a subworkflow end
    """
    pass


class OperationTask(BaseTask, logger.LoggerMixin):
    """
    Operation tasks
    """

    def __init__(self, api_task, *args, **kwargs):
        super(OperationTask, self).__init__(id=api_task.id, **kwargs)
        self._workflow_ctx = api_task.workflow_context
        task_model = api_task.workflow_context.model.task.model_cls
        task = task_model(
            name=api_task.name,
            operation_details=api_task.operation_details,
            node_instance=api_task.node_instance,
            inputs=api_task.inputs,
            status=task_model.PENDING,
            execution_id=self.workflow_context.execution_id,
            max_retries=self.workflow_context.parameters.get('max_retries', 1),
        )
        self.workflow_context.model.task.store(task)
        self._task_id = task.id
        self._update_fields = None

    @contextmanager
    def update(self):
        """
        A context manager which puts the task into update mode, enabling fields update.
        :yields: None
        """
        self._update_fields = {}
        try:
            yield
            task = self.context
            for key, value in self._update_fields.items():
                setattr(task, key, value)
            self.context = task
        finally:
            self._update_fields = None

    @property
    def workflow_context(self):
        """
        :return: the task's name
        """
        return self._workflow_ctx

    @property
    def context(self):
        """
        Returns the task model in storage
        :return: task in storage
        """
        return self.workflow_context.model.task.get(self._task_id)

    @context.setter
    def context(self, value):
        self.workflow_context.model.task.store(value)

    @property
    def status(self):
        """
        Returns the task status
        :return: task status
        """
        return self.context.status

    @status.setter
    def status(self, value):
        if self._update_fields is None:
            raise exceptions.TaskException("Task is not in update mode")
        self._update_fields['status'] = value

    @property
    def started_at(self):
        """
        Returns when the task started
        :return: when task started
        """
        return self.context.started_at

    @started_at.setter
    def started_at(self, value):
        if self._update_fields is None:
            raise exceptions.TaskException("Task is not in update mode")
        self._update_fields['started_at'] = value

    @property
    def ended_at(self):
        """
        Returns when the task ended
        :return: when task ended
        """
        return self.context.ended_at

    @ended_at.setter
    def ended_at(self, value):
        if self._update_fields is None:
            raise exceptions.TaskException("Task is not in update mode")
        self._update_fields['ended_at'] = value

    @property
    def retry_count(self):
        """
        Returns the retry count for the task
        :return: retry count
        """
        return self.context.retry_count

    @retry_count.setter
    def retry_count(self, value):
        if self._update_fields is None:
            raise exceptions.TaskException("Task is not in update mode")
        self._update_fields['retry_count'] = value

    def __getattr__(self, attr):
        try:
            return getattr(self.context, attr)
        except AttributeError:
            return super(OperationTask, self).__getattribute__(attr)
