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

from uuid import uuid4

from networkx import DiGraph, topological_sort

from aria.tools.validation import ValidatorMixin


class TaskNotFoundError(Exception):
    pass


class TaskNotInGraphError(Exception):
    pass


class TaskGraph(ValidatorMixin):
    """
    A task graph builder.
    Build a operations flow graph
    """

    def __init__(self, name):
        self.name = name
        self.id = str(uuid4())
        self.graph = DiGraph()

    def __getattr__(self, attr):
        try:
            return getattr(self.graph, attr)
        except AttributeError:
            return super(TaskGraph, self).__getattribute__(attr)

    def __repr__(self):
        return '{name}(id={self.id}, name={self.name}, graph={self.graph!r})'.format(
            name=self.__class__.__name__, self=self)

    @property
    def tasks(self):
        """
        An iterator on tasks added to the graph
        """
        for _, data in self.graph.nodes_iter(data=True):
            yield data['task']

    @property
    def leaf_tasks(self):
        for task in self.tasks_in_order():
            if not self.graph.predecessors(task.id):
                yield task

    def task_tree(self, reverse=False):
        """
        Iterates over the tasks to be executed in topological order and their dependencies.
        :param reverse: reverse the order
        """
        for task in self.tasks_in_order(reverse=reverse):
            yield task, self.task_dependencies(task)

    def tasks_in_order(self, reverse=False):
        """
        Iterates over the tasks to be executed in topological order
        :param reverse: reverse the order
        """
        for task_id in topological_sort(self.graph, reverse=reverse):
            yield self.graph.node[task_id]['task']

    def has_dependencies(self, task):
        return len(self.task_dependencies(task)) > 0

    def task_dependencies(self, task):
        """
        Iterates over the task dependencies
        """
        for task_ids in self.graph.edges_iter(task.id):
            for task_id in task_ids:
                if task.id != task_id:
                    yield self.get_task(task_id)

    def add_task(self, task):
        """
        Add a task to this graph
        :param WorkflowTask|TaskGraph task: The task
        """
        self.graph.add_node(task.id, task=task)

    def get_task(self, task_id):
        """
        Get a task instance that was inserted to this graph by its id

        :param basestring task_id: the task id
        :return: requested task
        :rtype: WorkflowTask|TaskGraph
        :raise: TaskNotFoundError if no task found with given id
        """
        try:
            data = self.graph.node[task_id]
            return data['task']
        except KeyError:
            raise TaskNotFoundError('Task id: {0}'.format(task_id))

    def remove_task(self, task):
        """
        Remove the provided task from the graph
        :param WorkflowTask|graph task: The task
        """
        self.graph.remove_node(task.id)

    def dependency(self, source_task, after):
        """
        Add a dependency between tasks.
        The source task will only be executed after the target task terminates.
        A source task may depend on several tasks,
        In which case it will only be executed after all its target tasks will terminate.

        tasks flow order:
        after -> source_task

        :param WorkflowTask|TaskGraph source_task: The source task
        :type source_task: WorkflowTask
        :param list after: The target task
        :raise TaskNotInGraphError
        """
        if not self.graph.has_node(source_task.id):
            raise TaskNotInGraphError(
                'source task {0!r} is not in graph (task id: {0.id})'.format(source_task))
        for target_task in after:
            if not self.graph.has_node(target_task.id):
                raise TaskNotInGraphError(
                    'target task {0!r} is not in graph (task id: {0.id})'.format(target_task))
            self.graph.add_edge(source_task.id, target_task.id)

    # workflow creation helper methods
    def chain(self, tasks, after=()):
        """
        create a chain of tasks.
        tasks will be added to the graph with a dependency between
        the tasks by order.

        tasks flow order:
        if tasks = (task0, task1, ..., taskn)
        after -> task0 -> task1 -> ... -> taskn

        :param tasks: list of WorkflowTask instances.
        :param after: target to the sequence
        """
        for source_task in tasks:
            self.add_task(source_task)
            self.dependency(source_task, after=after)
            after = (source_task,)

    def fan_out(self, tasks, after=()):
        """
        create a fan-out.
        tasks will be added to the graph with a dependency to
        the target task.

        tasks flow order:
        if tasks = (task0, task1, ..., taskn)
        after      -> task0
                   |-> task1
                   |...
                   \-> taskn

        :param tasks: list of WorkflowTask instances.
        :param after: target to the tasks
        """
        for source_task in tasks:
            self.add_task(source_task)
            self.dependency(source_task, after=after)

    def fan_in(self, source_task, after=None):
        """
        create a fan-in.
        source task will be added to the graph with a dependency to
        the tasks.

        tasks flow order:
        if after = (task0, task1, ..., taskn)
        task0\
        task1|-> source_task
        ...  |
        taskn/

        :param source_task: source to the tasks
        :param after: list of WorkflowTask instances.
        """
        self.add_task(source_task)
        self.dependency(source_task, after=after)
