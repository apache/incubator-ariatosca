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
from aria.orchestrator.workflows.builtin.install import install

from tests import mock
from tests import storage

from . import assert_node_install_operations


@pytest.fixture
def ctx(tmpdir):
    context = mock.context.simple(str(tmpdir),
                                  topology=mock.topology.create_simple_topology_three_nodes)
    yield context
    storage.release_sqlite_storage(context.model)


def test_install(ctx):

    install_tasks = list(task.WorkflowTask(install, ctx=ctx).topological_order(True))

    assert len(install_tasks) == 3
    dependency_node_subgraph1, dependency_node_subgraph2, dependent_node_subgraph = install_tasks
    dependent_node_tasks = list(dependent_node_subgraph.topological_order(reverse=True))
    dependency_node1_tasks = list(dependency_node_subgraph1.topological_order(reverse=True))
    dependency_node2_tasks = list(dependency_node_subgraph2.topological_order(reverse=True))

    assert_node_install_operations(dependency_node1_tasks)
    assert_node_install_operations(dependency_node2_tasks)
    assert_node_install_operations(dependent_node_tasks, relationships=2)
