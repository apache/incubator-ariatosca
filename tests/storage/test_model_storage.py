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
    model,
    exceptions,
    sql_mapi,
)
from aria import application_model_storage
from ..storage import get_sqlite_api_kwargs, release_sqlite_storage

from . import MockModel


@pytest.fixture
def storage():
    base_storage = ModelStorage(sql_mapi.SQLAlchemyModelAPI, api_kwargs=get_sqlite_api_kwargs())
    base_storage.register(MockModel)
    yield base_storage
    release_sqlite_storage(base_storage)


@pytest.fixture(scope='module', autouse=True)
def module_cleanup():
    model.DeclarativeBase.metadata.remove(MockModel.__table__)  #pylint: disable=no-member


def test_storage_base(storage):
    with pytest.raises(AttributeError):
        storage.non_existent_attribute()


def test_model_storage(storage):
    mock_model = MockModel(value=0, name='model_name')
    storage.mock_model.put(mock_model)

    assert storage.mock_model.get_by_name('model_name') == mock_model

    assert [mm_from_storage for mm_from_storage in storage.mock_model.iter()] == [mock_model]
    assert [mm_from_storage for mm_from_storage in storage.mock_model] == [mock_model]

    storage.mock_model.delete(mock_model)
    with pytest.raises(exceptions.StorageError):
        storage.mock_model.get(mock_model.id)


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

    release_sqlite_storage(storage)
