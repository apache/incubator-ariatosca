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

from aria import workflow
from aria.orchestrator import operation
from aria.orchestrator.workflows.api.task import OperationTask
from aria.orchestrator.runner import Runner

from tests import mock

import pytest


OPERATION_RESULTS = {}


@operation
def mock_create_operation(ctx, key, value, **kwargs): # pylint: disable=unused-argument
    OPERATION_RESULTS[key] = value


@pytest.fixture(autouse=True)
def cleanup():
    OPERATION_RESULTS.clear()


def test_runner_no_tasks():
    @workflow
    def workflow_fn(ctx, graph): # pylint: disable=unused-argument
        pass

    _test_runner(workflow_fn)


def test_runner_tasks():
    @workflow
    def workflow_fn(ctx, graph):
        for node in ctx.model.node:
            graph.add_tasks(
                OperationTask.for_node(node=node,
                                       name='tosca.interfaces.node.lifecycle.Standard.create'))

    _test_runner(workflow_fn)

    assert OPERATION_RESULTS.get('create') is True


def _initialize_model_storage_fn(model_storage):
    mock.topology.create_simple_topology_single_node(
        model_storage,
        '{0}.{1}'.format(__name__, mock_create_operation.__name__)
    )


def _test_runner(workflow_fn):
    runner = Runner(workflow_name='runner workflow',
                    workflow_fn=workflow_fn,
                    inputs={},
                    initialize_model_storage_fn=_initialize_model_storage_fn,
                    service_instance_id=1)
    runner.run()
