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

import aria
from aria.storage.sql_mapi import SQLAlchemyModelAPI
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.core import engine
from aria.orchestrator.workflows.executor import process
from aria.orchestrator import workflow, operation
from aria.orchestrator.context import serialization

import tests
from tests import mock
from tests import storage

TEST_FILE_CONTENT = 'CONTENT'
TEST_FILE_ENTRY_ID = 'entry'
TEST_FILE_NAME = 'test_file'


def test_serialize_operation_context(context, executor, tmpdir):
    test_file = tmpdir.join(TEST_FILE_NAME)
    test_file.write(TEST_FILE_CONTENT)
    resource = context.resource
    resource.blueprint.upload(TEST_FILE_ENTRY_ID, str(test_file))
    graph = _mock_workflow(ctx=context)  # pylint: disable=no-value-for-parameter
    eng = engine.Engine(executor=executor, workflow_context=context, tasks_graph=graph)
    eng.execute()


def test_illegal_serialize_of_memory_model_storage(memory_model_storage):
    with pytest.raises(AssertionError):
        serialization._serialize_sql_mapi_kwargs(memory_model_storage)


@workflow
def _mock_workflow(ctx, graph):
    node_instance = ctx.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
    node_instance.node.operations['test.op'] = {'operation': _operation_mapping()}
    task = api.task.OperationTask.node_instance(instance=node_instance, name='test.op')
    graph.add_tasks(task)
    return graph


@operation
def _mock_operation(ctx):
    # We test several things in this operation
    # ctx.task, ctx.node, etc... tell us that the model storage was properly re-created
    # a correct ctx.task.operation_mapping tells us we kept the correct task_id
    assert ctx.task.operation_mapping == _operation_mapping()
    # a correct ctx.node.name tells us we kept the correct actor_id
    assert ctx.node.name == mock.models.DEPENDENCY_NODE_NAME
    # a correct ctx.name tells us we kept the correct name
    assert ctx.name is not None
    assert ctx.name == ctx.task.name
    # a correct ctx.deployment.name tells us we kept the correct deployment_id
    assert ctx.deployment.name == mock.models.DEPLOYMENT_NAME
    # Here we test that the resource storage was properly re-created
    test_file_content = ctx.resource.blueprint.read(TEST_FILE_ENTRY_ID, TEST_FILE_NAME)
    assert test_file_content == TEST_FILE_CONTENT


def _operation_mapping():
    return '{name}.{func.__name__}'.format(name=__name__, func=_mock_operation)


@pytest.fixture
def executor():
    result = process.ProcessExecutor(python_path=[tests.ROOT_DIR])
    yield result
    result.close()


@pytest.fixture
def context(tmpdir):
    result = mock.context.simple(storage.get_sqlite_api_kwargs(str(tmpdir)),
                                 resources_dir=str(tmpdir.join('resources')))
    yield result
    storage.release_sqlite_storage(result.model)


@pytest.fixture
def memory_model_storage():
    result = aria.application_model_storage(
        SQLAlchemyModelAPI, api_kwargs=storage.get_sqlite_api_kwargs())
    yield result
    storage.release_sqlite_storage(result)
