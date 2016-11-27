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

from aria.storage import models

from ... import context
from .. import exceptions


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

    SOURCE_OPERATION = 'source_operations'
    TARGET_OPERATION = 'target_operations'

    def __init__(self,
                 name,
                 actor,
                 operation_mapping,
                 max_attempts=None,
                 retry_interval=None,
                 ignore_failure=None,
                 inputs=None):
        """
        Creates an operation task using the name, details, node instance and any additional kwargs.
        :param name: the operation of the name.
        :param operation_details: the details for the operation.
        :param actor: the operation host on which this operation is registered.
        :param inputs: operation inputs.
        """
        assert isinstance(actor, (models.NodeInstance,
                                  models.RelationshipInstance))
        super(OperationTask, self).__init__()
        self.actor = actor
        self.name = '{name}.{actor.id}'.format(name=name, actor=actor)
        self.operation_mapping = operation_mapping
        self.inputs = inputs or {}
        self.max_attempts = (self.workflow_context._task_max_attempts
                             if max_attempts is None else max_attempts)
        self.retry_interval = (self.workflow_context._task_retry_interval
                               if retry_interval is None else retry_interval)
        self.ignore_failure = (self.workflow_context._task_ignore_failure
                               if ignore_failure is None else ignore_failure)

    @classmethod
    def node_instance(cls, instance, name, inputs=None, *args, **kwargs):
        """
        Represents a node based operation

        :param instance: the node of which this operation belongs to.
        :param name: the name of the operation.
        """
        assert isinstance(instance, models.NodeInstance)
        operation_details = instance.node.operations[name]
        operation_inputs = operation_details.get('inputs', {})
        operation_inputs.update(inputs or {})
        return cls(name=name,
                   actor=instance,
                   operation_mapping=operation_details.get('operation', ''),
                   inputs=operation_inputs,
                   *args,
                   **kwargs)

    @classmethod
    def relationship_instance(cls, instance, name, operation_end, inputs=None, *args, **kwargs):
        """
        Represents a relationship based operation

        :param instance: the relationship of which this operation belongs to.
        :param name: the name of the operation.
        :param operation_end: source or target end of the relationship, this corresponds directly
        with 'source_operations' and 'target_operations'
        :param inputs any additional inputs to the operation
        """
        assert isinstance(instance, models.RelationshipInstance)
        if operation_end not in [cls.TARGET_OPERATION, cls.SOURCE_OPERATION]:
            raise exceptions.TaskException('The operation end should be {0} or {1}'.format(
                cls.TARGET_OPERATION, cls.SOURCE_OPERATION
            ))
        operation_details = getattr(instance.relationship, operation_end)[name]
        operation_inputs = operation_details.get('inputs', {})
        operation_inputs.update(inputs or {})
        return cls(actor=instance,
                   name=name,
                   operation_mapping=operation_details.get('operation'),
                   inputs=operation_inputs,
                   *args,
                   **kwargs)


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
