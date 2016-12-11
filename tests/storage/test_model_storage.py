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

from sqlalchemy import Column, Text, Integer

from aria.storage import (
    ModelStorage,
    model,
    exceptions,
    sql_mapi,
    structure,
    type as aria_type,
)
from aria import application_model_storage
from ..storage import get_sqlite_api_kwargs, release_sqlite_storage
from ..mock import context as mock_context


class MockModel(model.DeclarativeBase, structure.ModelMixin): #pylint: disable=abstract-method
    __tablename__ = 'mock_models'
    model_dict = Column(aria_type.Dict)
    model_list = Column(aria_type.List)
    value = Column(Integer)
    name = Column(Text)


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


def test_inner_dict_update(storage):
    inner_dict = {'inner_value': 1}

    mock_model = MockModel(model_dict={'inner_dict': inner_dict, 'value': 0})
    storage.mock_model.put(mock_model)

    storage_mm = storage.mock_model.get(mock_model.id)
    assert storage_mm == mock_model

    storage_mm.model_dict['inner_dict']['inner_value'] = 2
    storage_mm.model_dict['value'] = -1
    storage.mock_model.update(storage_mm)
    storage_mm = storage.mock_model.get(storage_mm.id)

    assert storage_mm.model_dict['inner_dict']['inner_value'] == 2
    assert storage_mm.model_dict['value'] == -1


def test_inner_list_update(storage):
    mock_model = MockModel(model_list=[0, [1]])
    storage.mock_model.put(mock_model)

    storage_mm = storage.mock_model.get(mock_model.id)
    assert storage_mm == mock_model

    storage_mm.model_list[1][0] = 'new_inner_value'
    storage_mm.model_list[0] = 'new_value'
    storage.mock_model.update(storage_mm)
    storage_mm = storage.mock_model.get(storage_mm.id)

    assert storage_mm.model_list[1][0] == 'new_inner_value'
    assert storage_mm.model_list[0] == 'new_value'


def test_model_to_dict():
    context = mock_context.simple(get_sqlite_api_kwargs())
    deployment = context.deployment
    deployment_dict = deployment.to_dict()

    expected_keys = [
        'created_at',
        'description',
        'inputs',
        'groups',
        'permalink',
        'policy_triggers',
        'policy_types',
        'outputs',
        'scaling_groups',
        'updated_at',
        'workflows',
        'blueprint_name',
    ]

    for expected_key in expected_keys:
        assert expected_key in deployment_dict

    assert 'blueprint_fk' not in deployment_dict


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
