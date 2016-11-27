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

from aria.orchestrator.workflows.api import task
from aria.orchestrator.workflows.builtin.heal import heal

from tests import mock, storage

from . import (assert_node_install_operations,
               assert_node_uninstall_operations)


@pytest.fixture
def ctx(tmpdir):
    context = mock.context.simple(storage.get_sqlite_api_kwargs(str(tmpdir)))
    yield context
    storage.release_sqlite_storage(context.model)


def test_heal_dependent_node(ctx):
    dependent_node_instance = \
        ctx.model.node_instance.get_by_name(mock.models.DEPENDENT_NODE_INSTANCE_NAME)
    dependent_node_instance.host_id = dependent_node_instance.id
    ctx.model.node_instance.update(dependent_node_instance)
    heal_graph = task.WorkflowTask(heal, ctx=ctx, node_instance_id=dependent_node_instance.id)

    assert len(list(heal_graph.tasks)) == 2
    uninstall_subgraph, install_subgraph = list(heal_graph.topological_order(reverse=True))

    assert len(list(uninstall_subgraph.tasks)) == 2
    dependent_node_subgraph_uninstall, dependency_node_subgraph_uninstall = \
        list(uninstall_subgraph.topological_order(reverse=True))

    assert len(list(install_subgraph.tasks)) == 2
    dependency_node_subgraph_install, dependent_node_subgraph_install = \
        list(install_subgraph.topological_order(reverse=True))

    dependent_node_uninstall_tasks = \
        list(dependent_node_subgraph_uninstall.topological_order(reverse=True))
    assert isinstance(dependency_node_subgraph_uninstall, task.StubTask)
    dependent_node_install_tasks = \
        list(dependent_node_subgraph_install.topological_order(reverse=True))
    assert isinstance(dependency_node_subgraph_install, task.StubTask)

    assert_node_uninstall_operations(dependent_node_uninstall_tasks, with_relationships=True)
    assert_node_install_operations(dependent_node_install_tasks, with_relationships=True)


def test_heal_dependency_node(ctx):
    dependency_node_instance = \
        ctx.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
    dependency_node_instance.host_id = dependency_node_instance.id
    ctx.model.node_instance.update(dependency_node_instance)
    heal_graph = task.WorkflowTask(heal, ctx=ctx, node_instance_id=dependency_node_instance.id)
    # both subgraphs should contain un\install for both the dependent and the dependency
    assert len(list(heal_graph.tasks)) == 2
    uninstall_subgraph, install_subgraph = list(heal_graph.topological_order(reverse=True))

    uninstall_tasks = list(uninstall_subgraph.topological_order(reverse=True))
    assert len(uninstall_tasks) == 4
    unlink_source, unlink_target = uninstall_tasks[:2]
    dependent_node_subgraph_uninstall, dependency_node_subgraph_uninstall = uninstall_tasks[2:]

    install_tasks = list(install_subgraph.topological_order(reverse=True))
    assert len(install_tasks) == 4
    dependency_node_subgraph_install, dependent_node_subgraph_install = install_tasks[:2]
    establish_source, establish_target = install_tasks[2:]

    assert isinstance(dependent_node_subgraph_uninstall, task.StubTask)
    dependency_node_uninstall_tasks = \
        list(dependency_node_subgraph_uninstall.topological_order(reverse=True))
    assert isinstance(dependent_node_subgraph_install, task.StubTask)
    dependency_node_install_tasks = \
        list(dependency_node_subgraph_install.topological_order(reverse=True))

    assert unlink_source.name.startswith('aria.interfaces.relationship_lifecycle.unlink')
    assert unlink_target.name.startswith('aria.interfaces.relationship_lifecycle.unlink')
    assert_node_uninstall_operations(dependency_node_uninstall_tasks)

    assert_node_install_operations(dependency_node_install_tasks)
    assert establish_source.name.startswith('aria.interfaces.relationship_lifecycle.establish')
    assert establish_target.name.startswith('aria.interfaces.relationship_lifecycle.establish')


# TODO: add tests for contained in scenario
