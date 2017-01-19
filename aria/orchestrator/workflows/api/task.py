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

from aria.storage.modeling import model

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
                 runs_on=None):
        """
        Creates an operation task using the name, details, node instance and any additional kwargs.
        :param name: the operation of the name.
        :param actor: the operation host on which this operation is registered.
        :param inputs: operation inputs.
        """
        assert isinstance(actor, (model.Node,
                                  model.Relationship))
        super(OperationTask, self).__init__()
        self.actor = actor
        self.name = '{name}.{actor.id}'.format(name=name, actor=actor)
        self.implementation = implementation
        self.inputs = inputs or {}
        self.plugin = plugin or {}
        self.max_attempts = (self.workflow_context._task_max_attempts
                             if max_attempts is None else max_attempts)
        self.retry_interval = (self.workflow_context._task_retry_interval
                               if retry_interval is None else retry_interval)
        self.ignore_failure = (self.workflow_context._task_ignore_failure
                               if ignore_failure is None else ignore_failure)
        self.runs_on = runs_on

    @classmethod
    def _merge_inputs(cls, operation_inputs, additional_inputs=None):
        final_inputs = dict((p.name, p.as_raw['value']) for p in operation_inputs)
        final_inputs.update(additional_inputs or {})
        return final_inputs

    @classmethod
    def node(cls, instance, name, inputs=None, *args, **kwargs):
        """
        Represents a node based operation

        :param instance: the node of which this operation belongs to.
        :param name: the name of the operation.
        """
        assert isinstance(instance, model.Node)
        interface_name = _get_interface_name(name)
        interfaces = instance.interfaces.filter_by(name=interface_name)
        if interfaces.count() > 1:
            raise exceptions.TaskException(
                "More than one interface with the same name `{0}` found".format(name)
            )
        elif interfaces.count() == 0:
            raise exceptions.TaskException(
                "No Interface with the name `{interface_name}` found".format(
                    interface_name=interface_name)
            )

        operation_templates = interfaces[0].operations.filter_by(name=name)
        if operation_templates.count() > 1:
            raise exceptions.TaskException(
                "More than one operation with the same name `{0}` were found".format(name)
            )

        elif operation_templates.count() == 0:
            raise exceptions.TaskException(
                "No interface with the name `{operation_name}` found".format(
                    operation_name=name)
            )

        return cls._instance(
            instance=instance,
            name=name,
            operation_template=operation_templates[0],
            plugins=instance.plugins or [],
            runs_on=model.Task.RUNS_ON_NODE_INSTANCE,
            inputs=cls._merge_inputs(operation_templates[0].inputs, inputs),
            *args,
            **kwargs)

    @classmethod
    def relationship(cls, instance, name, edge, runs_on=None, inputs=None, *args,
                     **kwargs):
        """
        Represents a relationship based operation

        :param instance: the relationship of which this operation belongs to.
        :param name: the name of the operation.
        :param edge: the edge of the interface ("source" or "target").
        :param runs_on: where to run the operation ("source" or "target"); if None defaults to the
                        interface edge.
        :param inputs any additional inputs to the operation
        """
        assert isinstance(instance, model.Relationship)
        interface_name = _get_interface_name(name)
        interfaces = instance.interfaces.filter_by(name=interface_name, edge=edge)
        count = interfaces.count()
        if count > 1:
            raise exceptions.TaskException(
                "More than one interface with the same name `{interface_name}` found at `{edge}`"
                + " edge".format(
                    interface_name=interface_name, edge=edge)
            )
        elif count == 0:
            raise exceptions.TaskException(
                "No interface with the name `{interface_name}` found at `{edge}` edge".format(
                    interface_name=interface_name, edge=edge)
            )

        operations = interfaces.all()[0].operations.filter_by(name=name)
        count = operations.count()
        if count > 1:
            raise exceptions.TaskException(
                "More than one operation with the same name `{0}` found".format(name)
            )
        elif count == 0:
            raise exceptions.TaskException(
                "No operation with the name `{operation_name}` found".format(
                    operation_name=name)
            )

        if not runs_on:
            if edge == cls.SOURCE_OPERATION:
                runs_on = model.Task.RUNS_ON_SOURCE
            else:
                runs_on = model.Task.RUNS_ON_TARGET

        if runs_on == model.Task.RUNS_ON_SOURCE:
            plugins = instance.source_node.plugins
        else:
            plugins = instance.target_node.plugins

        return cls._instance(instance=instance,
                             name=name,
                             operation_template=operations[0],
                             plugins=plugins or [],
                             runs_on=runs_on,
                             inputs=cls._merge_inputs(operations[0].inputs, inputs),
                             *args,
                             **kwargs)

    @classmethod
    def _instance(cls,
                  instance,
                  name,
                  operation_template,
                  inputs,
                  plugins,
                  runs_on,
                  *args,
                  **kwargs):
        matching_plugins = [p for p in plugins if p['name'] == operation_template.plugin]
        # All matching plugins should have identical package_name/package_version, so it's safe to
        # take the first found.
        plugin = matching_plugins[0] if matching_plugins else {}
        return cls(actor=instance,
                   name=name,
                   implementation=operation_template.implementation,
                   inputs=inputs,
                   plugin=plugin,
                   runs_on=runs_on,
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


def _get_interface_name(operation_name):
    return operation_name.rsplit('.', 1)[0]
