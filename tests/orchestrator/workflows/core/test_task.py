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
from datetime import (
    datetime,
    timedelta
)

import pytest

from aria.orchestrator.context import workflow as workflow_context
from aria.orchestrator.workflows import (
    api,
    core,
    exceptions,
)

from tests import mock


@pytest.fixture
def ctx():
    simple_context = mock.context.simple()

    blueprint = mock.models.get_blueprint()
    deployment = mock.models.get_deployment()
    node = mock.models.get_dependency_node()
    node_instance = mock.models.get_dependency_node_instance(node)
    execution = mock.models.get_execution()

    simple_context.model.blueprint.store(blueprint)
    simple_context.model.deployment.store(deployment)
    simple_context.model.node.store(node)
    simple_context.model.node_instance.store(node_instance)
    simple_context.model.execution.store(execution)

    return simple_context


class TestOperationTask(object):

    def _create_operation_task(self, ctx, node_instance):
        with workflow_context.current.push(ctx):
            api_task = api.task.OperationTask.node_instance(
                instance=node_instance,
                name='aria.interfaces.lifecycle.create',
            )

            core_task = core.task.OperationTask(api_task=api_task)

        return api_task, core_task

    def test_operation_task_creation(self, ctx):
        node_instance = ctx.model.node_instance.get(mock.models.DEPENDENCY_NODE_INSTANCE_ID)
        api_task, core_task = self._create_operation_task(ctx, node_instance)
        storage_task = ctx.model.task.get(core_task.id)

        assert core_task.model_task == storage_task
        assert core_task.name == api_task.name
        assert core_task.operation_mapping == api_task.operation_mapping
        assert core_task.actor == api_task.actor == node_instance
        assert core_task.inputs == api_task.inputs == storage_task.inputs

    def test_operation_task_edit_locked_attribute(self, ctx):
        node_instance = ctx.model.node_instance.get(mock.models.DEPENDENCY_NODE_INSTANCE_ID)

        _, core_task = self._create_operation_task(ctx, node_instance)
        now = datetime.utcnow()
        with pytest.raises(exceptions.TaskException):
            core_task.status = core_task.STARTED
        with pytest.raises(exceptions.TaskException):
            core_task.started_at = now
        with pytest.raises(exceptions.TaskException):
            core_task.ended_at = now
        with pytest.raises(exceptions.TaskException):
            core_task.retry_count = 2
        with pytest.raises(exceptions.TaskException):
            core_task.due_at = now

    def test_operation_task_edit_attributes(self, ctx):
        node_instance = ctx.model.node_instance.get(mock.models.DEPENDENCY_NODE_INSTANCE_ID)

        _, core_task = self._create_operation_task(ctx, node_instance)
        future_time = datetime.utcnow() + timedelta(seconds=3)

        with core_task._update():
            core_task.status = core_task.STARTED
            core_task.started_at = future_time
            core_task.ended_at = future_time
            core_task.retry_count = 2
            core_task.eta = future_time
            assert core_task.status != core_task.STARTED
            assert core_task.started_at != future_time
            assert core_task.ended_at != future_time
            assert core_task.retry_count != 2
            assert core_task.due_at != future_time

        assert core_task.status == core_task.STARTED
        assert core_task.started_at == future_time
        assert core_task.ended_at == future_time
        assert core_task.retry_count == 2
        assert core_task.eta == future_time
