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
    Represents an operation task in the task graph.

    :ivar name: formatted name (includes actor type, actor name, and interface/operation names)
    :vartype name: basestring
    :ivar actor: node or relationship
    :vartype actor: :class:`aria.modeling.models.Node`|:class:`aria.modeling.models.Relationship`
    :ivar interface_name: interface name on actor
    :vartype interface_name: basestring
    :ivar operation_name: operation name on interface
    :vartype operation_name: basestring
    :ivar plugin: plugin (or None for default plugin)
    :vartype plugin: :class:`aria.modeling.models.Plugin`
    :ivar function: path to Python function
    :vartype function: basestring
    :ivar arguments: arguments to send to Python function
    :vartype arguments: {basestring, :class:`aria.modeling.models.Argument`}
    :ivar ignore_failure: whether to ignore failures
    :vartype ignore_failure: bool
    :ivar max_attempts: maximum number of attempts allowed in case of failure
    :vartype max_attempts: int
    :ivar retry_interval: interval between retries (in seconds)
    :vartype retry_interval: int
    """

    NAME_FORMAT = '{interface}:{operation}@{type}:{name}'

    def __init__(self,
                 actor,
                 interface_name,
                 operation_name,
                 arguments=None,
                 ignore_failure=None,
                 max_attempts=None,
                 retry_interval=None):
        """
        :param actor: node or relationship
        :type actor: :class:`aria.modeling.models.Node`|:class:`aria.modeling.models.Relationship`
        :param interface_name: interface name on actor
        :type interface_name: basestring
        :param operation_name: operation name on interface
        :type operation_name: basestring
        :param arguments: override argument values
        :type arguments: {basestring, object}
        :param ignore_failure: override whether to ignore failures
        :type ignore_failure: bool
        :param max_attempts: override maximum number of attempts allowed in case of failure
        :type max_attempts: int
        :param retry_interval: override interval between retries (in seconds)
        :type retry_interval: int
        :raises aria.orchestrator.workflows.exceptions.OperationNotFoundException: if
                ``interface_name`` and ``operation_name`` to not refer to an operation on the actor
        """

        # Creating OperationTask directly should raise an error when there is no
        # interface/operation.
        if not has_operation(actor, interface_name, operation_name):
            raise exceptions.OperationNotFoundException(
                'Could not find operation "{operation_name}" on interface '
                '"{interface_name}" for {actor_type} "{actor.name}"'.format(
                    operation_name=operation_name,
                    interface_name=interface_name,
                    actor_type=type(actor).__name__.lower(),
                    actor=actor)
            )

        super(OperationTask, self).__init__()

        self.name = OperationTask.NAME_FORMAT.format(type=type(actor).__name__.lower(),
                                                     name=actor.name,
                                                     interface=interface_name,
                                                     operation=operation_name)
        self.actor = actor
        self.interface_name = interface_name
        self.operation_name = operation_name
        self.ignore_failure = \
            self.workflow_context._task_ignore_failure if ignore_failure is None else ignore_failure
        self.max_attempts = max_attempts or self.workflow_context._task_max_attempts
        self.retry_interval = retry_interval or self.workflow_context._task_retry_interval

        operation = self.actor.interfaces[self.interface_name].operations[self.operation_name]
        self.plugin = operation.plugin
        self.function = operation.function
        self.arguments = modeling_utils.merge_parameter_values(arguments,
                                                               operation.arguments,
                                                               model_cls=models.Argument)
        if getattr(self.actor, 'outbound_relationships', None) is not None:
            self._context_cls = context.operation.NodeOperationContext
        elif getattr(self.actor, 'source_node', None) is not None:
            self._context_cls = context.operation.RelationshipOperationContext
        else:
            raise exceptions.TaskCreationException('Could not locate valid context for '
                                                   '{actor.__class__}'.format(actor=self.actor))

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
