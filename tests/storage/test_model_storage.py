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

from sqlalchemy import (
    Column,
    Integer,
    Text
)

from aria import (
    application_model_storage,
    modeling
)
from aria.storage import (
    ModelStorage,
    exceptions,
    sql_mapi,
)

from tests import (
    mock,
    storage as tests_storage,
    modeling as tests_modeling
)


@pytest.fixture
def storage():
    base_storage = ModelStorage(sql_mapi.SQLAlchemyModelAPI,
                                initiator=tests_storage.init_inmemory_model_storage)
    base_storage.register(tests_modeling.MockModel)
    yield base_storage
    tests_storage.release_sqlite_storage(base_storage)


@pytest.fixture(scope='module', autouse=True)
def module_cleanup():
    modeling.models.aria_declarative_base.metadata.remove(tests_modeling.MockModel.__table__)  #pylint: disable=no-member


def test_storage_base(storage):
    with pytest.raises(AttributeError):
        storage.non_existent_attribute()


def test_model_storage(storage):
    mock_model = tests_modeling.MockModel(value=0, name='model_name')
    storage.mock_model.put(mock_model)

    assert storage.mock_model.get_by_name('model_name') == mock_model

    assert [mm_from_storage for mm_from_storage in storage.mock_model.iter()] == [mock_model]
    assert [mm_from_storage for mm_from_storage in storage.mock_model] == [mock_model]

    storage.mock_model.delete(mock_model)
    with pytest.raises(exceptions.StorageError):
        storage.mock_model.get(mock_model.id)


def test_application_storage_factory():
    storage = application_model_storage(sql_mapi.SQLAlchemyModelAPI,
                                        initiator=tests_storage.init_inmemory_model_storage)

    assert storage.service_template
    assert storage.node_template
    assert storage.group_template
    assert storage.policy_template
    assert storage.substitution_template
    assert storage.substitution_template_mapping
    assert storage.requirement_template
    assert storage.relationship_template
    assert storage.capability_template
    assert storage.interface_template
    assert storage.operation_template
    assert storage.artifact_template

    assert storage.service
    assert storage.node
    assert storage.group
    assert storage.policy
    assert storage.substitution
    assert storage.substitution_mapping
    assert storage.relationship
    assert storage.capability
    assert storage.interface
    assert storage.operation
    assert storage.artifact

    assert storage.execution
    assert storage.service_update
    assert storage.service_update_step
    assert storage.service_modification
    assert storage.plugin
    assert storage.task

    assert storage.input
    assert storage.output
    assert storage.property
    assert storage.attribute

    assert storage.type
    assert storage.metadata

    tests_storage.release_sqlite_storage(storage)


def test_cascade_deletion(context):
    service = context.model.service.list()[0]

    assert len(context.model.service_template.list()) == 1
    assert len(service.nodes) == len(context.model.node.list()) == 2

    context.model.service.delete(service)

    assert len(context.model.service_template.list()) == 1
    assert len(context.model.service.list()) == 0
    assert len(context.model.node.list()) == 0


@pytest.fixture
def context(tmpdir):
    result = mock.context.simple(str(tmpdir))
    yield result
    tests_storage.release_sqlite_storage(result.model)


def test_mapi_include(context):
    service1 = context.model.service.list()[0]
    service1.name = 'service1'
    service1.service_template.name = 'service_template1'
    context.model.service.update(service1)

    service_template2 = mock.models.create_service_template('service_template2')
    service2 = mock.models.create_service(service_template2, 'service2')
    context.model.service.put(service2)

    assert service1 != service2
    assert service1.service_template != service2.service_template

    def assert_include(service):
        st_name = context.model.service.get(service.id, include=('service_template_name',))
        st_name_list = context.model.service.list(filters={'id': service.id},
                                                  include=('service_template_name', ))
        assert len(st_name) == len(st_name_list) == 1
        assert st_name[0] == st_name_list[0][0] == service.service_template.name

    assert_include(service1)
    assert_include(service2)


class MockModel(modeling.models.aria_declarative_base, modeling.mixins.ModelMixin): #pylint: disable=abstract-method
    __tablename__ = 'op_mock_model'

    name = Column(Text)
    value = Column(Integer)


class TestFilterOperands(object):

    @pytest.fixture()
    def storage(self):
        model_storage = application_model_storage(
            sql_mapi.SQLAlchemyModelAPI, initiator=tests_storage.init_inmemory_model_storage)
        model_storage.register(MockModel)
        for value in (1, 2, 3, 4):
            model_storage.op_mock_model.put(MockModel(value=value))
        yield model_storage
        tests_storage.release_sqlite_storage(model_storage)

    def test_gt(self, storage):
        assert len(storage.op_mock_model.list(filters=dict(value=dict(gt=3)))) == 1
        assert len(storage.op_mock_model.list(filters=dict(value=dict(gt=4)))) == 0

    def test_ge(self, storage):
        assert len(storage.op_mock_model.list(filters=dict(value=dict(ge=3)))) == 2
        assert len(storage.op_mock_model.list(filters=dict(value=dict(ge=5)))) == 0

    def test_lt(self, storage):
        assert len(storage.op_mock_model.list(filters=dict(value=dict(lt=2)))) == 1
        assert len(storage.op_mock_model.list(filters=dict(value=dict(lt=1)))) == 0

    def test_le(self, storage):
        assert len(storage.op_mock_model.list(filters=dict(value=dict(le=2)))) == 2
        assert len(storage.op_mock_model.list(filters=dict(value=dict(le=0)))) == 0

    def test_eq(self, storage):
        assert len(storage.op_mock_model.list(filters=dict(value=dict(eq=2)))) == 1
        assert len(storage.op_mock_model.list(filters=dict(value=dict(eq=0)))) == 0

    def test_neq(self, storage):
        assert len(storage.op_mock_model.list(filters=dict(value=dict(ne=2)))) == 3

    def test_gt_and_lt(self, storage):
        assert len(storage.op_mock_model.list(filters=dict(value=dict(gt=1, lt=3)))) == 1
        assert len(storage.op_mock_model.list(filters=dict(value=dict(gt=2, lt=2)))) == 0

    def test_eq_and_ne(self, storage):
        assert len(storage.op_mock_model.list(filters=dict(value=dict(eq=1, ne=3)))) == 1
        assert len(storage.op_mock_model.list(filters=dict(value=dict(eq=1, ne=1)))) == 0
