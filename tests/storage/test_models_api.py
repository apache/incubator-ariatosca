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

from aria.storage import _ModelApi, models
from aria.storage.exceptions import StorageError

from . import InMemoryModelDriver


def test_models_api_base():
    driver = InMemoryModelDriver()
    driver.create(name='provider_context', model_cls=models.ProviderContext)
    table = _ModelApi('provider_context', driver, models.ProviderContext)
    assert repr(table) == (
        '{table.name}(driver={table._driver}, '
        'model={table.model_cls})'.format(table=table))
    provider_context = models.ProviderContext(context={}, name='context_name', id='id')

    table.store(provider_context)
    assert table.get('id') == provider_context

    assert [i for i in table.iter()] == [provider_context]
    assert [i for i in table] == [provider_context]

    table.delete('id')

    with pytest.raises(StorageError):
        table.get('id')


def test_iterable_model_api():
    driver = InMemoryModelDriver()
    driver.create('deployment_update', model_cls=models.DeploymentUpdate)
    driver.create('deployment_update_step', model_cls=models.DeploymentUpdateStep)
    model_api = _ModelApi('deployment_update', driver, models.DeploymentUpdate)
    deployment_update = models.DeploymentUpdate(
        id='id',
        deployment_id='deployment_id',
        deployment_plan={},
        execution_id='execution_id',
        steps=[models.DeploymentUpdateStep(
            id='step_id',
            action='add',
            entity_type='node',
            entity_id='node_id'
        )]
    )

    model_api.store(deployment_update)
    assert [i for i in model_api.iter()] == [deployment_update]
    assert [i for i in model_api] == [deployment_update]

    model_api.delete('id')

    with pytest.raises(StorageError):
        model_api.get('id')
