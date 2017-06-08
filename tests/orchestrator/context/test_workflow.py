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

from datetime import datetime

import pytest

from aria import application_model_storage, workflow
from aria.orchestrator import context
from aria.storage import sql_mapi
from aria.orchestrator.workflows.executor import thread, process

from tests import storage as test_storage, ROOT_DIR
from ... import mock
from . import execute


class TestWorkflowContext(object):

    def test_execution_creation_on_workflow_context_creation(self, storage):
        ctx = self._create_ctx(storage)
        execution = storage.execution.get(ctx.execution.id)             # pylint: disable=no-member
        assert execution.service == storage.service.get_by_name(
            mock.models.SERVICE_NAME)
        assert execution.workflow_name == mock.models.WORKFLOW_NAME
        assert execution.service_template == storage.service_template.get_by_name(
            mock.models.SERVICE_TEMPLATE_NAME)
        assert execution.status == storage.execution.model_cls.PENDING
        assert execution.inputs == {}
        assert execution.created_at <= datetime.utcnow()

    def test_subsequent_workflow_context_creation_do_not_fail(self, storage):
        self._create_ctx(storage)
        self._create_ctx(storage)

    @staticmethod
    def _create_ctx(storage):
        """

        :param storage:
        :return WorkflowContext:
        """
        service = storage.service.get_by_name(mock.models.SERVICE_NAME)
        return context.workflow.WorkflowContext(
            name='simple_context',
            model_storage=storage,
            resource_storage=None,
            service_id=service,
            execution_id=storage.execution.list(filters=dict(service=service))[0].id,
            workflow_name=mock.models.WORKFLOW_NAME,
            task_max_attempts=mock.models.TASK_MAX_ATTEMPTS,
            task_retry_interval=mock.models.TASK_RETRY_INTERVAL
        )

    @pytest.fixture
    def storage(self):
        workflow_storage = application_model_storage(
            sql_mapi.SQLAlchemyModelAPI, initiator=test_storage.init_inmemory_model_storage)
        workflow_storage.service_template.put(mock.models.create_service_template())
        service_template = workflow_storage.service_template.get_by_name(
            mock.models.SERVICE_TEMPLATE_NAME)
        service = mock.models.create_service(service_template)
        workflow_storage.service.put(service)
        workflow_storage.execution.put(mock.models.create_execution(service))
        yield workflow_storage
        test_storage.release_sqlite_storage(workflow_storage)


@pytest.fixture
def ctx(tmpdir):
    context = mock.context.simple(
        str(tmpdir),
        context_kwargs=dict(workdir=str(tmpdir.join('workdir')))
    )
    yield context
    test_storage.release_sqlite_storage(context.model)


@pytest.fixture(params=[
    (thread.ThreadExecutor, {}),
    (process.ProcessExecutor, {'python_path': [ROOT_DIR]}),
])
def executor(request):
    executor_cls, executor_kwargs = request.param
    result = executor_cls(**executor_kwargs)
    try:
        yield result
    finally:
        result.close()


def test_attribute_consumption(ctx, executor):

    node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)
    node.attributes['key'] = ctx.model.attribute.model_cls.wrap('key', 'value')
    node.attributes['key2'] = ctx.model.attribute.model_cls.wrap('key2', 'value_to_change')
    ctx.model.node.update(node)

    assert node.attributes['key'].value == 'value'
    assert node.attributes['key2'].value == 'value_to_change'

    @workflow
    def basic_workflow(ctx, **_):
        node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)
        node.attributes['new_key'] = 'new_value'
        node.attributes['key2'] = 'changed_value'

    execute(workflow_func=basic_workflow, workflow_context=ctx, executor=executor)
    node = ctx.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)

    assert len(node.attributes) == 3
    assert node.attributes['key'].value == 'value'
    assert node.attributes['new_key'].value == 'new_value'
    assert node.attributes['key2'].value == 'changed_value'
