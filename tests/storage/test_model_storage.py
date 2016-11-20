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
    Storage,
    ModelStorage,
    models,
)
from aria.storage import structures
from aria.storage.exceptions import StorageError
from aria.storage.structures import Model, Field, PointerField
from aria import application_model_storage

from . import InMemoryModelDriver


def test_storage_base():
    driver = InMemoryModelDriver()
    storage = Storage(driver)

    assert storage._driver == driver

    with pytest.raises(AttributeError):
        storage.non_existent_attribute()


def test_model_storage():
    storage = ModelStorage(InMemoryModelDriver())
    storage.register(models.ProviderContext)
    storage.setup()

    pc = models.ProviderContext(context={}, name='context_name', id='id1')
    storage.provider_context.store(pc)

    assert storage.provider_context.get('id1') == pc

    assert [pc_from_storage for pc_from_storage in storage.provider_context.iter()] == [pc]
    assert [pc_from_storage for pc_from_storage in storage.provider_context] == [pc]

    storage.provider_context.update('id1', context={'update_key': 0})
    assert storage.provider_context.get('id1').context == {'update_key': 0}

    storage.provider_context.delete('id1')
    with pytest.raises(StorageError):
        storage.provider_context.get('id1')


def test_storage_driver():
    storage = ModelStorage(InMemoryModelDriver())
    storage.register(models.ProviderContext)
    storage.setup()
    pc = models.ProviderContext(context={}, name='context_name', id='id2')
    storage._driver.store(name='provider_context', entry=pc, entry_id=pc.id)

    assert storage._driver.get(
        name='provider_context',
        entry_id='id2',
        model_cls=models.ProviderContext) == pc

    assert [i for i in storage._driver.iter(name='provider_context',
                                            model_cls=models.ProviderContext)] == [pc]
    assert [i for i in storage.provider_context] == [pc]

    storage.provider_context.delete('id2')

    with pytest.raises(StorageError):
        storage.provider_context.get('id2')


def test_application_storage_factory():
    driver = InMemoryModelDriver()
    storage = application_model_storage(driver)
    assert storage.node
    assert storage.node_instance
    assert storage.plugin
    assert storage.blueprint
    assert storage.snapshot
    assert storage.deployment
    assert storage.deployment_update
    assert storage.deployment_update_step
    assert storage.deployment_modification
    assert storage.execution
    assert storage.provider_context

    reused_storage = application_model_storage(driver)
    assert reused_storage == storage


def test_storage_pointers():
    class PointedModel(Model):
        id = Field()

    class PointingModel(Model):
        id = Field()
        pointing_field = PointerField(type=PointedModel)

    storage = ModelStorage(InMemoryModelDriver(), model_classes=[PointingModel, PointedModel])
    storage.setup()

    assert storage.pointed_model
    assert storage.pointing_model

    pointed_model = PointedModel(id='pointed_id')

    pointing_model = PointingModel(id='pointing_id', pointing_field=pointed_model)
    storage.pointing_model.store(pointing_model)

    assert storage.pointed_model.get('pointed_id') == pointed_model
    assert storage.pointing_model.get('pointing_id') == pointing_model

    storage.pointing_model.delete('pointing_id')

    with pytest.raises(StorageError):
        assert storage.pointed_model.get('pointed_id')
        assert storage.pointing_model.get('pointing_id')


def test_storage_iter_pointers():
    class PointedIterModel(models.Model):
        id = structures.Field()

    class PointingIterModel(models.Model):
        id = models.Field()
        pointing_field = structures.IterPointerField(type=PointedIterModel)

    storage = ModelStorage(InMemoryModelDriver(), model_classes=[PointingIterModel,
                                                                 PointedIterModel])
    storage.setup()

    assert storage.pointed_iter_model
    assert storage.pointing_iter_model

    pointed_iter_model1 = PointedIterModel(id='pointed_id1')
    pointed_iter_model2 = PointedIterModel(id='pointed_id2')

    pointing_iter_model = PointingIterModel(
        id='pointing_id',
        pointing_field=[pointed_iter_model1, pointed_iter_model2])
    storage.pointing_iter_model.store(pointing_iter_model)

    assert storage.pointed_iter_model.get('pointed_id1') == pointed_iter_model1
    assert storage.pointed_iter_model.get('pointed_id2') == pointed_iter_model2
    assert storage.pointing_iter_model.get('pointing_id') == pointing_iter_model

    storage.pointing_iter_model.delete('pointing_id')

    with pytest.raises(StorageError):
        assert storage.pointed_iter_model.get('pointed_id1')
        assert storage.pointed_iter_model.get('pointed_id2')
        assert storage.pointing_iter_model.get('pointing_id')
