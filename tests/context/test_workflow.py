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

from aria import context, application_model_storage

from ..mock import models
from ..storage import InMemoryModelDriver


class TestWorkflowContext(object):

    def test_execution_creation_on_workflow_context_creation(self, storage):
        self._create_ctx(storage)
        execution = storage.execution.get(models.EXECUTION_ID)
        assert execution.id == models.EXECUTION_ID
        assert execution.deployment_id == models.DEPLOYMENT_ID
        assert execution.workflow_id == models.WORKFLOW_ID
        assert execution.blueprint_id == models.BLUEPRINT_ID
        assert execution.status == storage.execution.model_cls.PENDING
        assert execution.parameters == {}
        assert execution.created_at <= datetime.utcnow()

    def test_subsequent_workflow_context_creation_do_not_fail(self, storage):
        self._create_ctx(storage)
        self._create_ctx(storage)

    @staticmethod
    def _create_ctx(storage):
        return context.workflow.WorkflowContext(
            name='simple_context',
            model_storage=storage,
            resource_storage=None,
            deployment_id=models.DEPLOYMENT_ID,
            workflow_id=models.WORKFLOW_ID,
            execution_id=models.EXECUTION_ID,
            task_max_retries=models.TASK_MAX_RETRIES,
            task_retry_interval=models.TASK_RETRY_INTERVAL
        )


@pytest.fixture(scope='function')
def storage():
    result = application_model_storage(InMemoryModelDriver())
    result.setup()
    result.deployment.store(models.get_deployment())
    return result
