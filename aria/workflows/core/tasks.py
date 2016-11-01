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

from datetime import datetime

from aria import logger
from aria.storage import models


class BaseTask(logger.LoggerMixin):
    """
    Base class for Task objects
    """

    def __init__(self, id, name, context, *args, **kwargs):
        super(BaseTask, self).__init__(*args, **kwargs)
        self._id = id
        self._name = name
        self._context = context

    @property
    def id(self):
        """
        :return: the task's id
        """
        return self._id

    @property
    def name(self):
        """
        :return: the task's name
        """
        return self._name

    @property
    def context(self):
        """
        :return: the task's context
        """
        return self._context


class BaseWorkflowTask(BaseTask):
    """
    Base class for all workflow wrapping tasks
    """

    def __init__(self, *args, **kwargs):
        super(BaseWorkflowTask, self).__init__(*args, **kwargs)
        self.status = models.Operation.PENDING
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


class OperationTask(BaseTask):
    """
    Operation tasks
    """

    def __init__(self, *args, **kwargs):
        super(OperationTask, self).__init__(*args, **kwargs)
        self._create_operation_in_storage()

    def _create_operation_in_storage(self):
        operation_cls = self.context.model.operation.model_cls
        operation = operation_cls(
            id=self.context.id,
            execution_id=self.context.execution_id,
            max_retries=self.context.parameters.get('max_retries', 1),
            status=operation_cls.PENDING,
        )
        self.context.operation = operation

    def __getattr__(self, attr):
        try:
            return getattr(self.context.operation, attr)
        except AttributeError:
            return super(OperationTask, self).__getattribute__(attr)
