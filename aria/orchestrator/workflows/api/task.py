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

from ... import context
from ....modeling import models
from ....modeling import utils as modeling_utils
from ....utils.uuid import generate_uuid
from .. import exceptions


class BaseTask(object):
    """
    Abstract task graph task
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
    Represents an operation task in the task graph
    """

    NAME_FORMAT = '{interface}:{operation}@{type}:{name}'

    def __init__(self,
                 actor,
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
        assert isinstance(actor, (models.Node, models.Relationship))
        super(OperationTask, self).__init__()
        self.actor = actor
        self.interface_name = interface_name
        self.operation_name = operation_name
        self.max_attempts = max_attempts or self.workflow_context._task_max_attempts
        self.retry_interval = retry_interval or self.workflow_context._task_retry_interval
        self.ignore_failure = \
            self.workflow_context._task_ignore_failure if ignore_failure is None else ignore_failure
        self.name = OperationTask.NAME_FORMAT.format(type=type(actor).__name__.lower(),
                                                     name=actor.name,
                                                     interface=self.interface_name,
                                                     operation=self.operation_name)
        # Creating OperationTask directly should raise an error when there is no
        # interface/operation.

        if not has_operation(self.actor, self.interface_name, self.operation_name):
            raise exceptions.OperationNotFoundException(
                'Could not find operation "{self.operation_name}" on interface '
                '"{self.interface_name}" for {actor_type} "{actor.name}"'.format(
                    self=self,
                    actor_type=type(actor).__name__.lower(),
                    actor=actor)
            )

        operation = self.actor.interfaces[self.interface_name].operations[self.operation_name]
        self.plugin = operation.plugin
        self.inputs = modeling_utils.create_inputs(inputs or {}, operation.inputs)
        self.implementation = operation.implementation

    def __repr__(self):
        return self.name


class StubTask(BaseTask):
    """
    Enables creating empty tasks.
    """


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


def create_task(actor, interface_name, operation_name, **kwargs):
    """
    This helper function enables safe creation of OperationTask, if the supplied interface or
    operation do not exist, None is returned.
    :param actor: the actor for this task
    :param interface_name: the name of the interface
    :param operation_name: the name of the operation
    :param kwargs: any additional kwargs to be passed to the task OperationTask
    :return: and OperationTask or None (if the interface/operation does not exists)
    """
    try:
        return OperationTask(
            actor,
            interface_name=interface_name,
            operation_name=operation_name,
            **kwargs
        )
    except exceptions.OperationNotFoundException:
        return None


def create_relationships_tasks(
        node, interface_name, source_operation_name=None, target_operation_name=None, **kwargs):
    """
    Creates a relationship task (source and target) for all of a node_instance relationships.
    :param basestring source_operation_name: the relationship operation name.
    :param basestring interface_name: the name of the interface.
    :param source_operation_name:
    :param target_operation_name:
    :param NodeInstance node: the source_node
    :return:
    """
    sub_tasks = []
    for relationship in node.outbound_relationships:
        relationship_operations = create_relationship_tasks(
            relationship,
            interface_name,
            source_operation_name=source_operation_name,
            target_operation_name=target_operation_name,
            **kwargs)
        sub_tasks.append(relationship_operations)
    return sub_tasks


def create_relationship_tasks(relationship, interface_name, source_operation_name=None,
                              target_operation_name=None, **kwargs):
    """
    Creates a relationship task source and target.
    :param Relationship relationship: the relationship instance itself
    :param source_operation_name:
    :param target_operation_name:

    :return:
    """
    operations = []
    if source_operation_name:
        operations.append(
            create_task(
                relationship,
                interface_name=interface_name,
                operation_name=source_operation_name,
                **kwargs
            )
        )
    if target_operation_name:
        operations.append(
            create_task(
                relationship,
                interface_name=interface_name,
                operation_name=target_operation_name,
                **kwargs
            )
        )

    return [o for o in operations if o]


def has_operation(actor, interface_name, operation_name):
    interface = actor.interfaces.get(interface_name, None)
    return interface and interface.operations.get(operation_name, False)
