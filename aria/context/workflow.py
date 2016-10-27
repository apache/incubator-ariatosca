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

from aria import exceptions

from .common import BaseContext


class ContextException(exceptions.AriaError):
    """
    Context based exception
    """
    pass


class WorkflowContext(BaseContext):
    """
    Context object used during workflow creation and execution
    """
    def __init__(self, parameters=None, *args, **kwargs):
        super(WorkflowContext, self).__init__(*args, **kwargs)
        self.parameters = parameters or {}
        # TODO: execution creation should happen somewhere else
        # should be moved there, when such logical place exists
        try:
            self.model.execution.get(self._execution_id)
        except exceptions.StorageError:
            self._create_execution()

    def __repr__(self):
        return (
            '{name}(deployment_id={self._deployment_id}, '
            'workflow_id={self._workflow_id}, '
            'execution_id={self._execution_id})'.format(
                name=self.__class__.__name__, self=self))

    def _create_execution(self):
        execution_cls = self.model.execution.model_cls
        execution = self.model.execution.model_cls(
            id=self._execution_id,
            deployment_id=self.deployment.id,
            workflow_id=self._workflow_id,
            blueprint_id=self.blueprint.id,
            status=execution_cls.PENDING,
            parameters=self.parameters,
        )
        self.model.execution.store(execution)

    @property
    def nodes(self):
        """
        Iterator over nodes
        """
        return self.model.node.iter(filters={'blueprint_id': self.blueprint.id})

    @property
    def node_instances(self):
        """
        Iterator over node instances
        """
        return self.model.node_instance.iter(filters={'deployment_id': self.deployment.id})


class _CurrentContext(threading.local):
    """
    Provides thread-level context, which sugarcoats the task api.
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
