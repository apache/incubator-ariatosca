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
Workflow and operation contexts
"""

import threading
from contextlib import contextmanager
from datetime import datetime

from .exceptions import ContextException
from .common import BaseContext


class WorkflowContext(BaseContext):
    """
    Context object used during workflow creation and execution
    """
    def __init__(self,
                 workflow_name,
                 parameters=None,
                 execution_id=None,
                 task_max_attempts=1,
                 task_retry_interval=0,
                 task_ignore_failure=False,
                 *args, **kwargs):
        super(WorkflowContext, self).__init__(*args, **kwargs)
        self._workflow_name = workflow_name
        self.parameters = parameters or {}
        self._task_max_attempts = task_max_attempts
        self._task_retry_interval = task_retry_interval
        self._task_ignore_failure = task_ignore_failure
        # TODO: execution creation should happen somewhere else
        # should be moved there, when such logical place exists
        self._execution_id = self._create_execution() if execution_id is None else execution_id

    def __repr__(self):
        return (
            '{name}(deployment_id={self._service_id}, '
            'workflow_name={self._workflow_name}'.format(
                name=self.__class__.__name__, self=self))

    def _create_execution(self):
        now = datetime.utcnow()
        execution = self.model.execution.model_cls(
            service=self.service,
            workflow_name=self._workflow_name,
            created_at=now,
            parameters=self.parameters,
        )
        self.model.execution.put(execution)
        return execution.id

    @property
    def execution(self):
        """
        The execution model
        """
        return self.model.execution.get(self._execution_id)

    @execution.setter
    def execution(self, value):
        """
        Store the execution in the model storage
        """
        self.model.execution.put(value)

    @property
    def node_templates(self):
        """
        Iterator over nodes
        """
        key = 'service_{0}'.format(self.model.node_template.model_cls.name_column_name())

        return self.model.node_template.iter(
            filters={
                key: getattr(self.service, self.service.name_column_name())
            }
        )

    @property
    def nodes(self):
        """
        Iterator over node instances
        """
        key = 'service_{0}'.format(self.model.node.model_cls.name_column_name())
        return self.model.node.iter(
            filters={
                key: getattr(self.service, self.service.name_column_name())
            }
        )


class _CurrentContext(threading.local):
    """
    Provides thread-level context, which sugarcoats the task mapi.
    """

    def __init__(self):
        super(_CurrentContext, self).__init__()
        self._workflow_context = None

    def _set(self, value):
        self._workflow_context = value

    def get(self):
        """
        Retrieves the current workflow context
        :return: the workflow context
        :rtype: WorkflowContext
        """
        if self._workflow_context is not None:
            return self._workflow_context
        raise ContextException("No context was set")

    @contextmanager
    def push(self, workflow_context):
        """
        Switches the current context to the provided context
        :param workflow_context: the context to switch to.
        :yields: the current context
        """
        prev_workflow_context = self._workflow_context
        self._set(workflow_context)
        try:
            yield self
        finally:
            self._set(prev_workflow_context)

current = _CurrentContext()
