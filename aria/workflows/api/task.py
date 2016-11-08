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
Provides the tasks to be entered into the task graph
"""
from uuid import uuid4

from ... import context


class BaseTask(object):
    """
    Abstract task_graph task
    """
    def __init__(self, ctx=None, **kwargs):
        if ctx is not None:
            self._workflow_context = ctx
        else:
            self._workflow_context = context.workflow.current.get()
        self._id = str(uuid4())

    @property
    def id(self):
        """
        uuid4 generated id
        :return:
        """
        return self._id

    @property
    def workflow_context(self):
        """
        the context of the current workflow
        :return:
        """
        return self._workflow_context


class OperationTask(BaseTask):
    """
    Represents an operation task in the task_graph
    """

    def __init__(self,
                 name,
                 operation_details,
                 node_instance,
                 max_retries=None,
                 retry_interval=None,
                 inputs=None):
        """
        Creates an operation task using the name, details, node instance and any additional kwargs.
        :param name: the operation of the name.
        :param operation_details: the details for the operation.
        :param node_instance: the node instance on which this operation is registered.
        :param inputs: operation inputs.
        """
        super(OperationTask, self).__init__()
        self.name = name
        self.operation_details = operation_details
        self.node_instance = node_instance
        self.inputs = inputs or {}
        self.max_retries = (self.workflow_context.task_max_retries
                            if max_retries is None else max_retries)
        self.retry_interval = (self.workflow_context.task_retry_interval
                               if retry_interval is None else retry_interval)


class WorkflowTask(BaseTask):
    """
    Represents an workflow task in the task_graph
    """
    def __init__(self, workflow_func, **kwargs):
        """
        Creates a workflow based task using the workflow_func provided, and its kwargs
        :param workflow_func: the function to run
        :param kwargs: the kwargs that would be passed to the workflow_func
        """
        super(WorkflowTask, self).__init__(**kwargs)
        kwargs['ctx'] = self.workflow_context
        self._graph = workflow_func(**kwargs)

    @property
    def graph(self):
        """
        The graph constructed by the sub workflow
        :return:
        """
        return self._graph

    def __getattr__(self, item):
        try:
            return getattr(self._graph, item)
        except AttributeError:
            return super(WorkflowTask, self).__getattribute__(item)


class StubTask(BaseTask):
    """
    Enables creating empty tasks.
    """
    pass
