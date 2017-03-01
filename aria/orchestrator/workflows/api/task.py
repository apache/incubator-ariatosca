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

from ....modeling import models
from ....utils.collections import OrderedDict
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

    SOURCE_OPERATION = 'source'
    TARGET_OPERATION = 'target'

    def __init__(self,
                 name,
                 actor,
                 implementation,
                 max_attempts=None,
                 retry_interval=None,
                 ignore_failure=None,
                 inputs=None,
                 plugin=None,
                 runs_on=None,
                 dry=False):
        """
        Creates an operation task using the name, details, node instance and any additional kwargs.

        :param name: the name of the operation.
        :param actor: the operation host on which this operation is registered.
        :param inputs: operation inputs.
        """

        assert isinstance(actor, (models.Node, models.Relationship))
        super(OperationTask, self).__init__()

        if dry:
            from ..dry import convert_to_dry
            plugin, implementation, inputs = convert_to_dry(plugin, implementation, inputs)

        # Coerce inputs
        if inputs is None:
            inputs = {}
        else:
            for k, v in inputs.iteritems():
                if not isinstance(v, models.Parameter):
                    inputs[k] = models.Parameter(name=k,
                                                 type_name='str',
                                                 str_value=str(v))

        self.name = name
        self.actor = actor
        self.implementation = implementation
        self.inputs = inputs
        self.plugin = plugin
        self.max_attempts = (self.workflow_context._task_max_attempts
                             if max_attempts is None else max_attempts)
        self.retry_interval = (self.workflow_context._task_retry_interval
                               if retry_interval is None else retry_interval)
        self.ignore_failure = (self.workflow_context._task_ignore_failure
                               if ignore_failure is None else ignore_failure)
        self.runs_on = runs_on

    @classmethod
    def for_node(cls, node, interface_name, operation_name, inputs=None, *args, **kwargs):
        """
        Creates an operation on a node.

        :param node: the node of which this operation belongs to.
        :param interface_name: the name of the interface.
        :param operation_name: the name of the operation.
        :param inputs: any additional inputs to the operation
        """

        assert isinstance(node, models.Node)
        operation = _get_operation(node.interfaces, interface_name, operation_name)
        if operation is None:
            raise exceptions.TaskException(
                'Could not find operation "{0}" on interface "{1}" for node "{2}"'.format(
                    operation_name, interface_name, node.name))

        return cls(
            actor=node,
            name='{0}.{1}@{2}'.format(interface_name, operation_name, node.name),
            plugin=operation.plugin,
            implementation=operation.implementation,
            inputs=cls._merge_inputs(operation.inputs, inputs),
            runs_on=models.Task.RUNS_ON_NODE,
            *args,
            **kwargs)

    @classmethod
    def for_relationship(cls, relationship, interface_name, operation_name, inputs=None,
                         runs_on=models.Task.RUNS_ON_SOURCE, *args, **kwargs):
        """
        Creates an operation on a relationship edge.

        :param relationship: the relationship of which this operation belongs to.
        :param interface_name: the name of the interface.
        :param operation_name: the name of the operation.
        :param inputs: any additional inputs to the operation
        :param runs_on: where to run the operation ("source" or "target"); defaults to "source"
        """

        assert isinstance(relationship, models.Relationship)
        assert runs_on in models.Task.RUNS_ON
        operation = _get_operation(relationship.interfaces, interface_name, operation_name)
        if operation is None:
            raise exceptions.TaskException(
                'Could not find operation "{0}" on interface "{1}" for relationship "{2}"'.format(
                    operation_name, interface_name, relationship.name))

        return cls(
            actor=relationship,
            name='{0}.{1}@{2}->{3}'.format(interface_name,
                                           operation_name,
                                           relationship.source_node.name,
                                           relationship.target_node.name),
            plugin=operation.plugin,
            implementation=operation.implementation,
            inputs=cls._merge_inputs(operation.inputs, inputs),
            runs_on=runs_on,
            *args,
            **kwargs)

    @classmethod
    def _merge_inputs(cls, operation_inputs, override_inputs=None):
        final_inputs = OrderedDict(operation_inputs)
        if override_inputs:
            final_inputs.update(override_inputs)
        return final_inputs


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


def _get_operation(interfaces, interface_name, operation_name):
    interface = interfaces.get(interface_name)
    if interface is not None:
        return interface.operations.get(operation_name)
    return None
