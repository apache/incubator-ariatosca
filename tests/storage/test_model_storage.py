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

from aria.storage import (
    ModelStorage,
    models,
    exceptions,
    sql_mapi,
)
from aria import application_model_storage
from tests.storage import get_sqlite_api_kwargs, release_sqlite_storage


@pytest.fixture
def storage():
    base_storage = ModelStorage(sql_mapi.SQLAlchemyModelAPI, api_kwargs=get_sqlite_api_kwargs())
    yield base_storage
    release_sqlite_storage(base_storage)


def test_storage_base(storage):
    with pytest.raises(AttributeError):
        storage.non_existent_attribute()


def test_model_storage(storage):
    storage.register(models.ProviderContext)

    pc = models.ProviderContext(context={}, name='context_name')
    storage.provider_context.put(pc)

    assert storage.provider_context.get_by_name('context_name') == pc

    assert [pc_from_storage for pc_from_storage in storage.provider_context.iter()] == [pc]
    assert [pc_from_storage for pc_from_storage in storage.provider_context] == [pc]

    new_context = {'update_key': 0}
    pc.context = new_context
    storage.provider_context.update(pc)
    assert storage.provider_context.get(pc.id).context == new_context

    storage.provider_context.delete(pc)
    with pytest.raises(exceptions.StorageError):
        storage.provider_context.get(pc.id)


def test_storage_driver(storage):
    storage.register(models.ProviderContext)

    pc = models.ProviderContext(context={}, name='context_name')
    storage.registered['provider_context'].put(entry=pc)

    assert storage.registered['provider_context'].get_by_name('context_name') == pc

    assert next(i for i in storage.registered['provider_context'].iter()) == pc
    assert [i for i in storage.provider_context] == [pc]

    storage.registered['provider_context'].delete(pc)

    with pytest.raises(exceptions.StorageError):
        storage.registered['provider_context'].get(pc.id)


def test_application_storage_factory():
    storage = application_model_storage(sql_mapi.SQLAlchemyModelAPI,
                                        api_kwargs=get_sqlite_api_kwargs())
    assert storage.node
    assert storage.node_instance
    assert storage.plugin
    assert storage.blueprint
    assert storage.deployment
    assert storage.deployment_update
    assert storage.deployment_update_step
    assert storage.deployment_modification
    assert storage.execution
    assert storage.provider_context

    release_sqlite_storage(storage)
