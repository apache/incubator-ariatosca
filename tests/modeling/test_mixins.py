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

import sqlalchemy

from aria.storage import (
    ModelStorage,
    sql_mapi
)
from aria import modeling
from aria.modeling.exceptions import ValueFormatException

from ..storage import (
    release_sqlite_storage,
    init_inmemory_model_storage
)
from . import MockModel
from ..mock import (
    models,
    context as mock_context
)


@pytest.fixture
def storage():
    base_storage = ModelStorage(sql_mapi.SQLAlchemyModelAPI,
                                initiator=init_inmemory_model_storage)
    base_storage.register(MockModel)
    yield base_storage
    release_sqlite_storage(base_storage)


@pytest.fixture(scope='module', autouse=True)
def module_cleanup():
    modeling.models.aria_declarative_base.metadata.remove(MockModel.__table__)                      # pylint: disable=no-member


@pytest.fixture
def context(tmpdir):
    ctx = mock_context.simple(str(tmpdir))
    yield ctx
    release_sqlite_storage(ctx.model)


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


def test_model_to_dict(context):
    service = context.service
    service = service.to_dict()

    expected_keys = [
        'description',
        'created_at',
        'permalink',
        'scaling_groups',
        'updated_at'
    ]

    for expected_key in expected_keys:
        assert expected_key in service


def test_relationship_model_ordering(context):
    service = context.model.service.get_by_name(models.SERVICE_NAME)
    source_node = context.model.node.get_by_name(models.DEPENDENT_NODE_NAME)
    target_node = context.model.node.get_by_name(models.DEPENDENCY_NODE_NAME)

    new_node_template = modeling.models.NodeTemplate(
        name='new_node_template',
        type=source_node.type,
        default_instances=1,
        min_instances=1,
        max_instances=1,
        service_template=service.service_template
    )

    new_node = modeling.models.Node(
        name='new_node',
        type=source_node.type,
        runtime_properties={},
        service=service,
        version=None,
        node_template=new_node_template,
        state=modeling.models.Node.INITIAL,
        scaling_groups=[]
    )

    source_node.outbound_relationships.append(modeling.models.Relationship(
        source_node=source_node,
        target_node=new_node,
    ))

    new_node.outbound_relationships.append(modeling.models.Relationship(                            # pylint: disable=no-member
        source_node=new_node,
        target_node=target_node,
    ))

    context.model.node_template.put(new_node_template)
    context.model.node.put(new_node)
    context.model.node.refresh(source_node)
    context.model.node.refresh(target_node)

    def flip_and_assert(node, direction):
        """
        Reversed the order of relationships and assert effects took place.
        :param node: the node instance to operate on
        :param direction: the type of relationships to flip (inbound/outbound)
        :return:
        """
        assert direction in ('inbound', 'outbound')

        def get_relationships():
            return getattr(node, direction + '_relationships')

        relationships = get_relationships()
        assert len(relationships) == 2

        reversed_relationship = list(reversed(relationships))
        assert relationships != reversed_relationship

        relationships[:] = reversed_relationship
        context.model.node.update(node)
        assert get_relationships() == reversed_relationship

    flip_and_assert(source_node, 'outbound')
    flip_and_assert(target_node, 'inbound')


class StrictClass(modeling.models.aria_declarative_base, modeling.mixins.ModelMixin):
    __tablename__ = 'strict_class'

    strict_dict = sqlalchemy.Column(modeling.types.StrictDict(basestring, basestring))
    strict_list = sqlalchemy.Column(modeling.types.StrictList(basestring))


def test_strict_dict():

    strict_class = StrictClass()

    def assert_strict(sc):
        with pytest.raises(ValueFormatException):
            sc.strict_dict = {'key': 1}

        with pytest.raises(ValueFormatException):
            sc.strict_dict = {1: 'value'}

        with pytest.raises(ValueFormatException):
            sc.strict_dict = {1: 1}

    assert_strict(strict_class)
    strict_class.strict_dict = {'key': 'value'}
    assert strict_class.strict_dict == {'key': 'value'}

    assert_strict(strict_class)
    with pytest.raises(ValueFormatException):
        strict_class.strict_dict['key'] = 1
    with pytest.raises(ValueFormatException):
        strict_class.strict_dict[1] = 'value'
    with pytest.raises(ValueFormatException):
        strict_class.strict_dict[1] = 1


def test_strict_list():
    strict_class = StrictClass()

    def assert_strict(sc):
        with pytest.raises(ValueFormatException):
            sc.strict_list = [1]

    assert_strict(strict_class)
    strict_class.strict_list = ['item']
    assert strict_class.strict_list == ['item']

    assert_strict(strict_class)
    with pytest.raises(ValueFormatException):
        strict_class.strict_list[0] = 1
