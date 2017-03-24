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
import copy

from ....modeling import models
from ....utils.collections import (OrderedDict, FrozenDict)
from ....utils.uuid import generate_uuid
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
        self._id = generate_uuid(variant='uuid')

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
    Represents an operation task in the task graph.
    """

    NAME_FORMAT = '{interface}:{operation}@{type}:{name}'

    def __init__(self,
                 actor,
                 actor_type,
                 interface_name,
                 operation_name,
                 inputs=None,
                 max_attempts=None,
                 retry_interval=None,
                 ignore_failure=None):
        """
        Do not call this constructor directly. Instead, use :meth:`for_node` or
        :meth:`for_relationship`.
        """

        assert interface_name and operation_name
        super(OperationTask, self).__init__()

        operation = None
        interface = actor.interfaces.get(interface_name)
        if interface is not None:
            operation = interface.operations.get(operation_name)

        if operation is None:
            raise exceptions.OperationNotFoundException(
                'Could not find operation "{0}" on interface "{1}" for {2} "{3}"'
                .format(operation_name, interface_name, actor_type, actor.name))

        if operation.implementation is None:
            raise exceptions.OperationNotFoundException(
                'Empty operation "{0}" on interface "{1}" for {2} "{3}"'
                .format(operation_name, interface_name, actor_type, actor.name))

        self.actor = actor
        self.actor_type = actor_type
        self.interface_name = interface_name
        self.operation_name = operation_name

        self.name = OperationTask.NAME_FORMAT.format(type=actor_type,
                                                     name=actor.name,
                                                     interface=interface_name,
                                                     operation=operation_name)
        self.max_attempts = (self.workflow_context._task_max_attempts
                             if max_attempts is None else max_attempts)
        self.retry_interval = (self.workflow_context._task_retry_interval
                               if retry_interval is None else retry_interval)
        self.ignore_failure = (self.workflow_context._task_ignore_failure
                               if ignore_failure is None else ignore_failure)
        self.implementation = operation.implementation
        self.plugin = operation.plugin

        # Wrap inputs
        inputs = copy.deepcopy(inputs) if inputs else {}
        for k, v in inputs.iteritems():
            if not isinstance(v, models.Parameter):
                inputs[k] = models.Parameter.wrap(k, v)

        self.inputs = OrderedDict(operation.inputs)
        if inputs:
            self.inputs.update(inputs)
        self.inputs = FrozenDict(self.inputs)

    @classmethod
    def for_node(cls,
                 node,
                 interface_name,
                 operation_name,
                 inputs=None,
                 max_attempts=None,
                 retry_interval=None,
                 ignore_failure=None):
        """
        Creates an operation on a node.

        :param node: The node on which to run the operation
        :param interface_name: The interface name
        :param operation_name: The operation name within the interface
        :param inputs: Override the operation's inputs
        :param max_attempts: The maximum number of attempts in case the operation fails
                             (if not specified the defaults is taken from the workflow context)
        :param retry_interval: The interval in seconds between attempts when the operation fails
                               (if not specified the defaults is taken from the workflow context)
        :param ignore_failure: Whether to ignore failures
                               (if not specified the defaults is taken from the workflow context)
        """

        assert isinstance(node, models.Node)
        return cls(
            actor=node,
            actor_type='node',
            interface_name=interface_name,
            operation_name=operation_name,
            inputs=inputs,
            max_attempts=max_attempts,
            retry_interval=retry_interval,
            ignore_failure=ignore_failure)

    @classmethod
    def for_relationship(cls,
                         relationship,
                         interface_name,
                         operation_name,
                         inputs=None,
                         max_attempts=None,
                         retry_interval=None,
                         ignore_failure=None):
        """
        Creates an operation on a relationship.

        :param relationship: The relationship on which to run the operation
        :param interface_name: The interface name
        :param operation_name: The operation name within the interface
        :param inputs: Override the operation's inputs
        :param max_attempts: The maximum number of attempts in case the operation fails
                             (if not specified the defaults is taken from the workflow context)
        :param retry_interval: The interval in seconds between attempts when the operation fails
                               (if not specified the defaults is taken from the workflow context)
        :param ignore_failure: Whether to ignore failures
                               (if not specified the defaults is taken from the workflow context)
        """

        assert isinstance(relationship, models.Relationship)
        return cls(
            actor=relationship,
            actor_type='relationship',
            interface_name=interface_name,
            operation_name=operation_name,
            inputs=inputs,
            max_attempts=max_attempts,
            retry_interval=retry_interval,
            ignore_failure=ignore_failure)


class WorkflowTask(BaseTask):
    """
    Represents a workflow task in the task graph
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
