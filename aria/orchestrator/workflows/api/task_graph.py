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
Task graph.
"""

from collections import Iterable

from networkx import DiGraph, topological_sort

from ....utils.uuid import generate_uuid
from . import task as api_task


class TaskNotInGraphError(Exception):
    """
    An error representing a scenario where a given task is not in the graph as expected.
    """
    pass


def _filter_out_empty_tasks(func=None):
    if func is None:
        return lambda f: _filter_out_empty_tasks(func=f)

    def _wrapper(task, *tasks, **kwargs):
        return func(*(t for t in (task,) + tuple(tasks) if t), **kwargs)
    return _wrapper


class TaskGraph(object):
    """
    Task graph builder.
    """

    def __init__(self, name):
        self.name = name
        self._id = generate_uuid(variant='uuid')
        self._graph = DiGraph()

    def __repr__(self):
        return '{name}(id={self._id}, name={self.name}, graph={self._graph!r})'.format(
            name=self.__class__.__name__, self=self)

    @property
    def id(self):
        """
        ID of the graph
        """
        return self._id

    # graph traversal methods

    @property
    def tasks(self):
        """
        Iterator over tasks in the graph.
        """
        for _, data in self._graph.nodes_iter(data=True):
            yield data['task']

    def topological_order(self, reverse=False):
        """
        Topological sort of the graph.

        :param reverse: whether to reverse the sort
        :return: list which represents the topological sort
        """
        for task_id in topological_sort(self._graph, reverse=reverse):
            yield self.get_task(task_id)

    def get_dependencies(self, dependent_task):
        """
        Iterates over the task's dependencies.

        :param dependent_task: task whose dependencies are requested
        :raises ~aria.orchestrator.workflows.api.task_graph.TaskNotInGraphError: if
         ``dependent_task`` is not in the graph
        """
        if not self.has_tasks(dependent_task):
            raise TaskNotInGraphError('Task id: {0}'.format(dependent_task.id))
        for _, dependency_id in self._graph.out_edges_iter(dependent_task.id):
            yield self.get_task(dependency_id)

    def get_dependents(self, dependency_task):
        """
        Iterates over the task's dependents.

        :param dependency_task: task whose dependents are requested
        :raises ~aria.orchestrator.workflows.api.task_graph.TaskNotInGraphError: if
         ``dependency_task`` is not in the graph
        """
        if not self.has_tasks(dependency_task):
            raise TaskNotInGraphError('Task id: {0}'.format(dependency_task.id))
        for dependent_id, _ in self._graph.in_edges_iter(dependency_task.id):
            yield self.get_task(dependent_id)

    # task methods

    def get_task(self, task_id):
        """
        Get a task instance that's been inserted to the graph by the task's ID.

        :param basestring task_id: task ID
        :raises ~aria.orchestrator.workflows.api.task_graph.TaskNotInGraphError: if no task found in
         the graph with the given ID
        """
        if not self._graph.has_node(task_id):
            raise TaskNotInGraphError('Task id: {0}'.format(task_id))
        data = self._graph.node[task_id]
        return data['task']

    @_filter_out_empty_tasks
    def add_tasks(self, *tasks):
        """
        Adds a task to the graph.

        :param task: task
        :return: list of added tasks
        :rtype: list
        """
        assert all([isinstance(task, (api_task.BaseTask, Iterable)) for task in tasks])
        return_tasks = []

        for task in tasks:
            if isinstance(task, Iterable):
                return_tasks += self.add_tasks(*task)
            elif not self.has_tasks(task):
                self._graph.add_node(task.id, task=task)
                return_tasks.append(task)

        return return_tasks

    @_filter_out_empty_tasks
    def remove_tasks(self, *tasks):
        """
        Removes the provided task from the graph.

        :param task: task
        :return: list of removed tasks
        :rtype: list
        """
        return_tasks = []

        for task in tasks:
            if isinstance(task, Iterable):
                return_tasks += self.remove_tasks(*task)
            elif self.has_tasks(task):
                self._graph.remove_node(task.id)
                return_tasks.append(task)

        return return_tasks

    @_filter_out_empty_tasks
    def has_tasks(self, *tasks):
        """
        Checks whether a task is in the graph.

        :param task: task
        :return: ``True`` if all tasks are in the graph, otherwise ``False``
        :rtype: list
        """
        assert all(isinstance(t, (api_task.BaseTask, Iterable)) for t in tasks)
        return_value = True

        for task in tasks:
            if isinstance(task, Iterable):
                return_value &= self.has_tasks(*task)
            else:
                return_value &= self._graph.has_node(task.id)

        return return_value

    def add_dependency(self, dependent, dependency):
        """
        Adds a dependency for one item (task, sequence or parallel) on another.

        The dependent will only be executed after the dependency terminates. If either of the items
        is either a sequence or a parallel, multiple dependencies may be added.

        :param dependent: dependent (task, sequence or parallel)
        :param dependency: dependency (task, sequence or parallel)
        :return: ``True`` if the dependency between the two hadn't already existed, otherwise
         ``False``
        :rtype: bool
        :raises ~aria.orchestrator.workflows.api.task_graph.TaskNotInGraphError: if either the
         dependent or dependency are tasks which are not in the graph
        """
        if not (self.has_tasks(dependent) and self.has_tasks(dependency)):
            raise TaskNotInGraphError()

        if self.has_dependency(dependent, dependency):
            return

        if isinstance(dependent, Iterable):
            for dependent_task in dependent:
                self.add_dependency(dependent_task, dependency)
        else:
            if isinstance(dependency, Iterable):
                for dependency_task in dependency:
                    self.add_dependency(dependent, dependency_task)
            else:
                self._graph.add_edge(dependent.id, dependency.id)

    def has_dependency(self, dependent, dependency):
        """
        Checks whether one item (task, sequence or parallel) depends on another.

        Note that if either of the items is either a sequence or a parallel, and some of the
        dependencies exist in the graph but not all of them, this method will return ``False``.

        :param dependent: dependent (task, sequence or parallel)
        :param dependency: dependency (task, sequence or parallel)
        :return: ``True`` if the dependency between the two exists, otherwise ``False``
        :rtype: bool
        :raises ~aria.orchestrator.workflows.api.task_graph.TaskNotInGraphError: if either the
         dependent or dependency are tasks which are not in the graph
        """
        if not (dependent and dependency):
            return False
        elif not (self.has_tasks(dependent) and self.has_tasks(dependency)):
            raise TaskNotInGraphError()

        return_value = True

        if isinstance(dependent, Iterable):
            for dependent_task in dependent:
                return_value &= self.has_dependency(dependent_task, dependency)
        else:
            if isinstance(dependency, Iterable):
                for dependency_task in dependency:
                    return_value &= self.has_dependency(dependent, dependency_task)
            else:
                return_value &= self._graph.has_edge(dependent.id, dependency.id)

        return return_value

    def remove_dependency(self, dependent, dependency):
        """
        Removes a dependency for one item (task, sequence or parallel) on another.

        Note that if either of the items is either a sequence or a parallel, and some of the
        dependencies exist in the graph but not all of them, this method will not remove any of the
        dependencies and return ``False``.

        :param dependent: dependent (task, sequence or parallel)
        :param dependency: dependency (task, sequence or parallel)
        :return: ``False`` if the dependency between the two hadn't existed, otherwise ``True``
        :rtype: bool
        :raises ~aria.orchestrator.workflows.api.task_graph.TaskNotInGraphError: if either the
         dependent or dependency are tasks which are not in the graph
        """
        if not (self.has_tasks(dependent) and self.has_tasks(dependency)):
            raise TaskNotInGraphError()

        if not self.has_dependency(dependent, dependency):
            return

        if isinstance(dependent, Iterable):
            for dependent_task in dependent:
                self.remove_dependency(dependent_task, dependency)
        elif isinstance(dependency, Iterable):
            for dependency_task in dependency:
                self.remove_dependency(dependent, dependency_task)
        else:
            self._graph.remove_edge(dependent.id, dependency.id)

    @_filter_out_empty_tasks
    def sequence(self, *tasks):
        """
        Creates and inserts a sequence into the graph, effectively each task i depends on i-1.

        :param tasks: iterable of dependencies
        :return: provided tasks
        """
        if tasks:
            self.add_tasks(*tasks)

            for i in xrange(1, len(tasks)):
                self.add_dependency(tasks[i], tasks[i-1])

        return tasks
