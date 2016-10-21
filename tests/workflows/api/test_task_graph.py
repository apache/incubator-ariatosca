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

import pytest

from aria.workflows.api import task_graph, task


class MockTask(task.BaseTask):
    def __init__(self):
        super(MockTask, self).__init__(ctx={})


@pytest.fixture
def graph():
    return task_graph.TaskGraph(name='mock-graph')


class TestTaskGraphTasks(object):

    def test_add_task(self, graph):
        task = MockTask()
        add_result = graph.add_tasks(task)
        assert add_result == [task]
        tasks = [t for t in graph.tasks]
        assert len(tasks) == 1
        assert tasks[0] == task

    def test_add_empty_group(self, graph):
        result = graph.add_tasks([])
        assert result == []

    def test_add_group(self, graph):
        tasks = [MockTask(), MockTask(), MockTask()]
        added_tasks = graph.add_tasks(*tasks)
        assert added_tasks == tasks

    def test_add_partially_existing_group(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        tasks = [MockTask(), task, MockTask()]
        added_tasks = graph.add_tasks(*tasks)
        assert added_tasks == [tasks[0], tasks[2]]

    def test_add_recursively_group(self, graph):
        recursive_group = [MockTask(), MockTask()]
        tasks = [MockTask(), recursive_group, MockTask()]
        added_tasks = graph.add_tasks(tasks)
        assert added_tasks == [tasks[0], recursive_group[0], recursive_group[1], tasks[2]]

    def test_add_existing_task(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        # adding a task already in graph - should have no effect, and return False
        add_result = graph.add_tasks(task)
        assert add_result == []
        tasks = [t for t in graph.tasks]
        assert len(tasks) == 1
        assert tasks[0] == task

    def test_remove_task(self, graph):
        task = MockTask()
        other_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(other_task)
        graph.remove_tasks(other_task)
        tasks = [t for t in graph.tasks]
        assert len(tasks) == 1
        assert tasks[0] == task

    def test_remove_tasks_with_dependency(self, graph):
        task = MockTask()
        dependent_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(dependent_task)
        graph.add_dependency(dependent_task, task)
        remove_result = graph.remove_tasks(dependent_task)
        assert remove_result == [dependent_task]
        tasks = [t for t in graph.tasks]
        assert len(tasks) == 1
        assert tasks[0] == task
        # asserting no dependencies are left for the dependent task
        assert len(list(graph.get_dependencies(task))) == 0

    def test_remove_empty_group(self, graph):
        result = graph.remove_tasks([])
        assert result == []

    def test_remove_group(self, graph):
        tasks = [MockTask(), MockTask(), MockTask()]
        graph.add_tasks(*tasks)
        removed_tasks = graph.remove_tasks(*tasks)
        assert removed_tasks == tasks

    def test_remove_partially_existing_group(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        tasks = [MockTask(), task, MockTask()]
        removed_tasks = graph.remove_tasks(*tasks)
        assert removed_tasks == [task]

    def test_remove_recursively_group(self, graph):
        recursive_group = [MockTask(), MockTask()]
        tasks = [MockTask(), recursive_group, MockTask()]
        graph.add_tasks(tasks)
        removed_tasks = graph.remove_tasks(tasks)
        assert removed_tasks == [tasks[0], recursive_group[0], recursive_group[1], tasks[2]]

    def test_remove_nonexistent_task(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        # removing a task not in graph - should have no effect, and return False
        remove_result = graph.remove_tasks(task_not_in_graph)
        assert remove_result == []
        tasks = [t for t in graph.tasks]
        assert len(tasks) == 1
        assert tasks[0] == task

    def test_has_task(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        assert graph.has_tasks(task) is True

    def test_has_nonexistent_task(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        assert graph.has_tasks(task_not_in_graph) is False

    def test_has_empty_group(self, graph):
        # the "empty task" is in the graph
        assert graph.has_tasks([]) is True

    def test_has_group(self, graph):
        tasks = [MockTask(), MockTask(), MockTask()]
        graph.add_tasks(*tasks)
        assert graph.has_tasks(*tasks) is True

    def test_has_partially_existing_group(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        tasks = [MockTask(), task, MockTask()]
        assert graph.has_tasks(tasks) is False

    def test_has_recursively_group(self, graph):
        recursive_group = [MockTask(), MockTask()]
        tasks = [MockTask(), recursive_group, MockTask()]
        graph.add_tasks(tasks)
        assert graph.has_tasks(tasks) is True

    def test_get_task(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        assert graph.get_task(task.id) == task

    def test_get_nonexistent_task(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        with pytest.raises(task_graph.TaskNotInGraphError):
            graph.get_task(task_not_in_graph.id)


class TestTaskGraphGraphTraversal(object):

    def test_tasks_iteration(self, graph):
        task = MockTask()
        other_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(other_task)
        tasks = [t for t in graph.tasks]
        assert set(tasks) == set([task, other_task])

    def test_get_dependents(self, graph):
        task = MockTask()
        dependent_task_1 = MockTask()
        dependent_task_2 = MockTask()
        transitively_dependent_task = MockTask()

        graph.add_tasks(task)
        graph.add_tasks(dependent_task_1)
        graph.add_tasks(dependent_task_2)
        graph.add_tasks(transitively_dependent_task)

        graph.add_dependency(dependent_task_1, task)
        graph.add_dependency(dependent_task_2, task)
        graph.add_dependency(transitively_dependent_task, dependent_task_2)

        dependent_tasks = list(graph.get_dependents(task))
        # transitively_dependent_task not expected to appear in the result
        assert set(dependent_tasks) == set([dependent_task_1, dependent_task_2])

    def test_get_task_empty_dependents(self, graph):
        task = MockTask()
        other_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(other_task)
        dependent_tasks = list(graph.get_dependents(task))
        assert len(dependent_tasks) == 0

    def test_get_nonexistent_task_dependents(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        with pytest.raises(task_graph.TaskNotInGraphError):
            list(graph.get_dependents(task_not_in_graph))

    def test_get_dependencies(self, graph):
        task = MockTask()
        dependency_task_1 = MockTask()
        dependency_task_2 = MockTask()
        transitively_dependency_task = MockTask()

        graph.add_tasks(task)
        graph.add_tasks(dependency_task_1)
        graph.add_tasks(dependency_task_2)
        graph.add_tasks(transitively_dependency_task)

        graph.add_dependency(task, dependency_task_1)
        graph.add_dependency(task, dependency_task_2)
        graph.add_dependency(dependency_task_2, transitively_dependency_task)

        dependency_tasks = list(graph.get_dependencies(task))
        # transitively_dependency_task not expected to appear in the result
        assert set(dependency_tasks) == set([dependency_task_1, dependency_task_2])

    def test_get_task_empty_dependencies(self, graph):
        task = MockTask()
        other_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(other_task)
        dependency_tasks = list(graph.get_dependencies(task))
        assert len(dependency_tasks) == 0

    def test_get_nonexistent_task_dependencies(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        with pytest.raises(task_graph.TaskNotInGraphError):
            list(graph.get_dependencies(task_not_in_graph))


class TestTaskGraphDependencies(object):

    def test_add_dependency(self, graph):
        task = MockTask()
        dependency_task = MockTask()
        unrelated_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(dependency_task)
        graph.add_tasks(unrelated_task)
        graph.add_dependency(task, dependency_task)
        add_result = graph.has_dependency(task, dependency_task)
        assert add_result is True
        dependency_tasks = list(graph.get_dependencies(task))
        assert len(dependency_tasks) == 1
        assert dependency_tasks[0] == dependency_task

    def test_add_existing_dependency(self, graph):
        task = MockTask()
        dependency_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(dependency_task)
        graph.add_dependency(task, dependency_task)
        add_result = graph.has_dependency(task, dependency_task)
        # adding a dependency already in graph - should have no effect, and return False
        assert add_result is True
        graph.add_dependency(task, dependency_task)
        add_result = graph.has_dependency(task, dependency_task)
        assert add_result is True
        dependency_tasks = list(graph.get_dependencies(task))
        assert len(dependency_tasks) == 1
        assert dependency_tasks[0] == dependency_task

    def test_add_dependency_nonexistent_dependent(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        with pytest.raises(task_graph.TaskNotInGraphError):
            graph.add_dependency(task_not_in_graph, task)

    def test_add_dependency_nonexistent_dependency(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        with pytest.raises(task_graph.TaskNotInGraphError):
            graph.add_dependency(task, task_not_in_graph)

    def test_add_dependency_empty_dependent(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        # expecting add_dependency result to be False - no dependency has been created
        assert set(graph.tasks) == set((task,))

    def test_add_dependency_empty_dependency(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        # expecting add_dependency result to be False - no dependency has been created
        assert set(graph.tasks) == set((task,))

    def test_add_dependency_dependent_group(self, graph):
        task = MockTask()
        group_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(task)
        graph.add_tasks(*group_tasks)
        graph.add_dependency(group_tasks, task)
        assert graph.has_dependency(group_tasks[0], task) is True
        assert graph.has_dependency(group_tasks[1], task) is True
        assert graph.has_dependency(group_tasks[2], task) is True

    def test_add_dependency_dependency_group(self, graph):
        task = MockTask()
        group_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(task)
        graph.add_tasks(*group_tasks)
        graph.add_dependency(task, group_tasks)
        assert graph.has_dependency(task, group_tasks[0]) is True
        assert graph.has_dependency(task, group_tasks[1]) is True
        assert graph.has_dependency(task, group_tasks[2]) is True

    def test_add_dependency_between_groups(self, graph):
        group_1_tasks = [MockTask() for _ in xrange(3)]
        group_2_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(*group_1_tasks)
        graph.add_tasks(*group_2_tasks)
        graph.add_dependency(group_1_tasks, group_2_tasks)
        for group_2_task in group_2_tasks:
            assert graph.has_dependency(group_1_tasks[0], group_2_task) is True
            assert graph.has_dependency(group_1_tasks[1], group_2_task) is True
            assert graph.has_dependency(group_1_tasks[2], group_2_task) is True

    def test_add_dependency_dependency_group_with_some_existing_dependencies(self, graph):
        task = MockTask()
        group_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(task)
        graph.add_tasks(*group_tasks)
        # adding a dependency on a specific task manually,
        # before adding a dependency on the whole parallel
        graph.add_dependency(task, group_tasks[1])
        graph.add_dependency(task, group_tasks)
        assert graph.has_dependency(task, group_tasks[0]) is True
        assert graph.has_dependency(task, group_tasks[1]) is True
        assert graph.has_dependency(task, group_tasks[2]) is True

    def test_add_existing_dependency_between_groups(self, graph):
        group_1_tasks = [MockTask() for _ in xrange(3)]
        group_2_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(*group_1_tasks)
        graph.add_tasks(*group_2_tasks)
        graph.add_dependency(group_1_tasks, group_2_tasks)
        add_result = graph.has_dependency(group_1_tasks, group_2_tasks)
        assert add_result is True
        # adding a dependency already in graph - should have no effect, and return False
        graph.add_dependency(group_1_tasks, group_2_tasks)
        add_result = graph.has_dependency(group_1_tasks, group_2_tasks)
        assert add_result is True
        for group_2_task in group_2_tasks:
            assert graph.has_dependency(group_1_tasks[0], group_2_task) is True
            assert graph.has_dependency(group_1_tasks[1], group_2_task) is True
            assert graph.has_dependency(group_1_tasks[2], group_2_task) is True

    def test_has_dependency(self, graph):
        task = MockTask()
        dependency_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(dependency_task)
        graph.add_dependency(task, dependency_task)
        assert graph.has_dependency(task, dependency_task) is True

    def test_has_nonexistent_dependency(self, graph):
        task = MockTask()
        other_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(other_task)
        assert graph.has_dependency(task, other_task) is False

    def test_has_dependency_nonexistent_dependent(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        with pytest.raises(task_graph.TaskNotInGraphError):
            graph.has_dependency(task_not_in_graph, task)

    def test_has_dependency_nonexistent_dependency(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        with pytest.raises(task_graph.TaskNotInGraphError):
            graph.has_dependency(task, task_not_in_graph)

    def test_has_dependency_empty_dependent(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        # expecting has_dependency result to be False - dependency in an empty form
        assert graph.has_dependency([], task) is False

    def test_has_dependency_empty_dependency(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        # expecting has_dependency result to be True - dependency in an empty form
        assert graph.has_dependency(task, []) is False

    def test_has_dependency_dependent_group(self, graph):
        task = MockTask()
        group_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(task)
        graph.add_tasks(*group_tasks)
        assert graph.has_dependency(group_tasks, task) is False
        graph.add_dependency(group_tasks, task)
        assert graph.has_dependency(group_tasks, task) is True

    def test_has_dependency_dependency_parallel(self, graph):
        task = MockTask()
        group_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(task)
        graph.add_tasks(*group_tasks)
        assert graph.has_dependency(task, group_tasks) is False
        graph.add_dependency(task, group_tasks)
        assert graph.has_dependency(task, group_tasks) is True

    def test_has_dependency_between_groups(self, graph):
        group_1_tasks = [MockTask() for _ in xrange(3)]
        group_2_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(*group_1_tasks)
        graph.add_tasks(*group_2_tasks)
        assert graph.has_dependency(group_2_tasks, group_1_tasks) is False
        graph.add_dependency(group_2_tasks, group_1_tasks)
        assert graph.has_dependency(group_2_tasks, group_1_tasks) is True

    def test_has_dependency_dependency_parallel_with_some_existing_dependencies(self, graph):
        task = MockTask()
        parallel_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(task)
        parallel = graph.add_tasks(*parallel_tasks)
        graph.add_dependency(task, parallel_tasks[1])
        # only a partial dependency exists - has_dependency is expected to return False
        assert graph.has_dependency(task, parallel) is False

    def test_has_nonexistent_dependency_between_groups(self, graph):
        group_1_tasks = [MockTask() for _ in xrange(3)]
        group_2_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(*group_1_tasks)
        graph.add_tasks(*group_2_tasks)
        assert graph.has_dependency(group_1_tasks, group_2_tasks) is False

    def test_remove_dependency(self, graph):
        task = MockTask()
        dependency_task = MockTask()
        another_dependent_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(dependency_task)
        graph.add_tasks(another_dependent_task)
        graph.add_dependency(task, dependency_task)
        graph.add_dependency(another_dependent_task, dependency_task)

        graph.remove_dependency(task, dependency_task)
        remove_result = graph.has_dependency(task, dependency_task)
        assert remove_result is False
        assert graph.has_dependency(task, dependency_task) is False
        assert graph.has_dependency(another_dependent_task, dependency_task) is True

    def test_remove_nonexistent_dependency(self, graph):
        task = MockTask()
        dependency_task = MockTask()
        graph.add_tasks(task)
        graph.add_tasks(dependency_task)
        # removing a dependency not in graph - should have no effect, and return False
        graph.remove_dependency(task, dependency_task)
        remove_result = graph.has_dependency(task, dependency_task)
        assert remove_result is False
        tasks = [t for t in graph.tasks]
        assert set(tasks) == set([task, dependency_task])

    def test_remove_dependency_nonexistent_dependent(self, graph):
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        with pytest.raises(task_graph.TaskNotInGraphError):
            graph.remove_dependency(task_not_in_graph, task)

    def test_remove_dependency_nonexistent_dependency(self, graph):
        # in this test the dependency *task* is not in the graph, not just the dependency itself
        task = MockTask()
        task_not_in_graph = MockTask()
        graph.add_tasks(task)
        with pytest.raises(task_graph.TaskNotInGraphError):
            graph.remove_dependency(task, task_not_in_graph)

    def test_remove_dependency_empty_dependent(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        # expecting remove_dependency result to be False - no dependency has been created
        graph.remove_dependency([], task)
        assert set(graph.tasks) == set((task,))

    def test_remove_dependency_empty_dependency(self, graph):
        task = MockTask()
        graph.add_tasks(task)
        # expecting remove_dependency result to be False - no dependency has been created
        graph.remove_dependency(task, [])
        assert set(graph.tasks) == set((task,))

    def test_remove_dependency_dependent_group(self, graph):
        task = MockTask()
        group_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(task)
        graph.add_tasks(*group_tasks)
        graph.add_dependency(group_tasks, task)
        graph.remove_dependency(group_tasks, task)
        remove_result = graph.has_dependency(group_tasks, task)
        assert remove_result is False
        assert graph.has_dependency(group_tasks[0], task) is False
        assert graph.has_dependency(group_tasks[1], task) is False
        assert graph.has_dependency(group_tasks[2], task) is False

    def test_remove_dependency_dependency_group(self, graph):
        task = MockTask()
        group_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(task)
        graph.add_tasks(*group_tasks)
        graph.add_dependency(task, group_tasks)
        graph.remove_dependency(task, group_tasks)
        remove_result = graph.has_dependency(task, group_tasks)
        assert remove_result is False
        assert graph.has_dependency(task, group_tasks[0]) is False
        assert graph.has_dependency(task, group_tasks[1]) is False
        assert graph.has_dependency(task, group_tasks[2]) is False

    def test_remove_dependency_between_groups(self, graph):
        group_1_tasks = [MockTask() for _ in xrange(3)]
        group_2_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(*group_1_tasks)
        graph.add_tasks(*group_2_tasks)
        graph.add_dependency(group_2_tasks, group_1_tasks)
        graph.remove_dependency(group_2_tasks, group_1_tasks)
        remove_result = graph.has_dependency(group_2_tasks, group_1_tasks)
        assert remove_result is False
        for group_2_task in group_2_tasks:
            assert graph.has_dependency(group_2_task, group_1_tasks[0]) is False
            assert graph.has_dependency(group_2_task, group_1_tasks[1]) is False
            assert graph.has_dependency(group_2_task, group_1_tasks[2]) is False

    def test_remove_dependency_dependency_group_with_some_existing_dependencies(self, graph):
        task = MockTask()
        group_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(task)
        graph.add_tasks(*group_tasks)
        graph.add_dependency(task, group_tasks[1])
        graph.remove_dependency(task, group_tasks)
        remove_result = graph.has_dependency(task, group_tasks)
        # only a partial dependency exists - remove_dependency is expected to return False
        assert remove_result is False
        # no dependencies are expected to have changed
        assert graph.has_dependency(task, group_tasks[0]) is False
        assert graph.has_dependency(task, group_tasks[1]) is True
        assert graph.has_dependency(task, group_tasks[2]) is False

    def test_remove_nonexistent_dependency_between_groups(self, graph):
        group_1_tasks = [MockTask() for _ in xrange(3)]
        group_2_tasks = [MockTask() for _ in xrange(3)]
        graph.add_tasks(*group_1_tasks)
        graph.add_tasks(*group_2_tasks)
        # removing a dependency not in graph - should have no effect, and return False
        graph.remove_dependency(group_2_tasks, group_1_tasks)
        remove_result = graph.has_dependency(group_2_tasks, group_1_tasks)
        assert remove_result is False

    # nested tests

    def test_group_with_nested_sequence(self, graph):
        all_tasks = [MockTask() for _ in xrange(5)]
        graph.add_tasks(all_tasks[0],
                        graph.sequence(all_tasks[1], all_tasks[2], all_tasks[3]),
                        all_tasks[4])
        assert set(graph.tasks) == set(all_tasks)

        # tasks[2] and tasks[3] should each have a single dependency; the rest should have none
        assert len(list(graph.get_dependencies(all_tasks[0]))) == 0
        assert len(list(graph.get_dependencies(all_tasks[1]))) == 0
        assert set(graph.get_dependencies(all_tasks[2])) == set([all_tasks[1]])
        assert set(graph.get_dependencies(all_tasks[3])) == set([all_tasks[2]])
        assert len(list(graph.get_dependencies(all_tasks[4]))) == 0

    def test_group_with_nested_group(self, graph):
        tasks = [MockTask() for _ in xrange(5)]
        graph.add_tasks(tasks[0], (tasks[1], tasks[2], tasks[3]), tasks[4])
        graph_tasks = [t for t in graph.tasks]
        assert set(graph_tasks) == set(tasks)
        # none of the tasks should have any dependencies
        for i in xrange(len(tasks)):
            assert len(list(graph.get_dependencies(tasks[i]))) == 0

    def test_group_with_recursively_nested_group(self, graph):
        recursively_nested_tasks = [MockTask(), MockTask(), MockTask()]
        nested_tasks = [MockTask(), MockTask(), MockTask(), recursively_nested_tasks]
        tasks = [MockTask(), MockTask(), MockTask(), nested_tasks]
        graph.add_tasks(*tasks)

        assert set(graph.tasks) == set(tasks[:3] + nested_tasks[:3] + recursively_nested_tasks)
        for tasks_list in [tasks, nested_tasks, recursively_nested_tasks]:
            for i in xrange(len(tasks_list[:3])):
                assert len(list(graph.get_dependencies(tasks_list[i]))) == 0

    def test_group_with_recursively_nested_group_and_interdependencies(self, graph):
        recursively_nested_tasks = [MockTask(), MockTask(), MockTask()]
        nested_tasks = [MockTask(), MockTask(), MockTask(), recursively_nested_tasks]
        tasks = [MockTask(), MockTask(), MockTask(), nested_tasks]
        graph.add_tasks(*tasks)

        graph.add_dependency(tasks[2], nested_tasks[2])
        graph.add_dependency(nested_tasks[1], recursively_nested_tasks[0])
        graph.add_dependency(recursively_nested_tasks[1], tasks[0])

        assert set(graph.tasks) == set(tasks[:3] + nested_tasks[:3] + recursively_nested_tasks)
        assert set(graph.get_dependencies(tasks[0])) == set()
        assert set(graph.get_dependencies(tasks[1])) == set()
        assert set(graph.get_dependencies(tasks[2])) == set([nested_tasks[2]])

        assert set(graph.get_dependencies(nested_tasks[0])) == set()
        assert set(graph.get_dependencies(nested_tasks[1])) == set([recursively_nested_tasks[0]])
        assert set(graph.get_dependencies(nested_tasks[2])) == set()

        assert set(graph.get_dependencies(recursively_nested_tasks[0])) == set()
        assert set(graph.get_dependencies(recursively_nested_tasks[1])) == set([tasks[0]])
        assert set(graph.get_dependencies(recursively_nested_tasks[2])) == set()


class TestTaskGraphSequence(object):

    def test_sequence(self, graph):
        tasks = [MockTask(), MockTask(), MockTask()]
        graph.sequence(*tasks)
        graph_tasks = [t for t in graph.tasks]
        assert set(graph_tasks) == set(tasks)
        assert len(list(graph.get_dependencies(tasks[0]))) == 0
        assert set(graph.get_dependencies(tasks[1])) == set([tasks[0]])
        assert set(graph.get_dependencies(tasks[2])) == set([tasks[1]])

    def test_sequence_with_some_tasks_and_dependencies_already_in_graph(self, graph):
        # tests both that tasks which werent previously in graph get inserted, and
        # that existing tasks don't get re-added to graph
        tasks = [MockTask(), MockTask(), MockTask()]
        # insert some tasks and dependencies to the graph
        graph.add_tasks(tasks[1])
        graph.add_tasks(tasks[2])
        graph.add_dependency(tasks[2], tasks[1])

        graph.sequence(*tasks)
        graph_tasks = [t for t in graph.tasks]
        assert set(graph_tasks) == set(tasks)
        assert len(list(graph.get_dependencies(tasks[0]))) == 0
        assert set(graph.get_dependencies(tasks[1])) == set([tasks[0]])
        assert set(graph.get_dependencies(tasks[2])) == set([tasks[1]])

    def test_sequence_with_nested_sequence(self, graph):
        tasks = [MockTask() for _ in xrange(5)]
        graph.sequence(tasks[0], graph.sequence(tasks[1], tasks[2], tasks[3]), tasks[4])
        graph_tasks = [t for t in graph.tasks]
        assert set(graph_tasks) == set(tasks)
        # first task should have no dependencies
        assert len(list(graph.get_dependencies(tasks[0]))) == 0
        assert len(list(graph.get_dependencies(tasks[1]))) == 1
        assert len(list(graph.get_dependencies(tasks[2]))) == 2
        assert len(list(graph.get_dependencies(tasks[3]))) == 2
        assert len(list(graph.get_dependencies(tasks[4]))) == 3

    def test_sequence_with_nested_group(self, graph):
        tasks = [MockTask() for _ in xrange(5)]
        graph.sequence(tasks[0], (tasks[1], tasks[2], tasks[3]), tasks[4])
        graph_tasks = [t for t in graph.tasks]
        assert set(graph_tasks) == set(tasks)
        # first task should have no dependencies
        assert len(list(graph.get_dependencies(tasks[0]))) == 0
        # rest of the tasks (except last) should have a single dependency - the first task
        for i in xrange(1, 4):
            assert set(graph.get_dependencies(tasks[i])) == set([tasks[0]])
        # last task should have have a dependency on all tasks except for the first one
        assert set(graph.get_dependencies(tasks[4])) == set([tasks[1], tasks[2], tasks[3]])

    def test_sequence_with_recursively_nested_group(self, graph):
        recursively_nested_group = [MockTask(), MockTask()]
        nested_group = [MockTask(), recursively_nested_group, MockTask()]
        sequence_tasks = [MockTask(), nested_group, MockTask()]

        graph.sequence(*sequence_tasks)
        graph_tasks = [t for t in graph.tasks]
        assert set(graph_tasks) == set([sequence_tasks[0], nested_group[0],
                                        recursively_nested_group[0], recursively_nested_group[1],
                                        nested_group[2], sequence_tasks[2]])

        assert list(graph.get_dependencies(nested_group[0])) == [sequence_tasks[0]]
        assert list(graph.get_dependencies(recursively_nested_group[0])) == [sequence_tasks[0]]
        assert list(graph.get_dependencies(recursively_nested_group[1])) == [sequence_tasks[0]]
        assert list(graph.get_dependencies(nested_group[2])) == [sequence_tasks[0]]

        assert list(graph.get_dependents(nested_group[0])) == [sequence_tasks[2]]
        assert list(graph.get_dependents(recursively_nested_group[0])) == [sequence_tasks[2]]
        assert list(graph.get_dependents(recursively_nested_group[1])) == [sequence_tasks[2]]
        assert list(graph.get_dependents(nested_group[2])) == [sequence_tasks[2]]

    def test_sequence_with_empty_group(self, graph):
        tasks = [MockTask(), [], MockTask()]
        graph.sequence(*tasks)
        graph_tasks = set([t for t in graph.tasks])
        assert graph_tasks == set([tasks[0], tasks[2]])
        assert list(graph.get_dependents(tasks[0])) == [tasks[2]]
        assert list(graph.get_dependencies(tasks[2])) == [tasks[0]]

    def test_sequence_with_recursively_nested_sequence_and_interdependencies(self, graph):
        recursively_nested_tasks = list(graph.sequence(MockTask(), MockTask(), MockTask()))
        nested_tasks = list(graph.sequence(MockTask(),
                                           MockTask(),
                                           MockTask(),
                                           recursively_nested_tasks))
        tasks = [MockTask(), MockTask(), MockTask(), nested_tasks]
        graph.sequence(*tasks)

        assert set(graph.tasks) == set(tasks[:3] + nested_tasks[:3] + recursively_nested_tasks)
        assert set(graph.get_dependencies(tasks[0])) == set()
        for i in xrange(1, len(tasks[:-1])):
            assert set(graph.get_dependencies(tasks[i])) == set([tasks[i - 1]])

        assert set(graph.get_dependencies(nested_tasks[0])) == set([tasks[2]])
        for i in xrange(1, len(nested_tasks[:-1])):
            assert set(graph.get_dependencies(nested_tasks[i])) == \
                   set([tasks[2], nested_tasks[i-1]])

        assert set(graph.get_dependencies(recursively_nested_tasks[0])) == \
               set([tasks[2], nested_tasks[2]])
        for i in xrange(1, len(recursively_nested_tasks[:-1])):
            assert set(graph.get_dependencies(recursively_nested_tasks[i])) == \
                   set([tasks[2], nested_tasks[2], recursively_nested_tasks[i-1]])
