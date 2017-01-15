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
    sql_mapi,
    model,
    type,
    exceptions
)

from ..storage import get_sqlite_api_kwargs, release_sqlite_storage, structure
from . import MockModel
from ..mock import (
    models,
    operations,
    context as mock_context
)


@pytest.fixture
def storage():
    base_storage = ModelStorage(sql_mapi.SQLAlchemyModelAPI, api_kwargs=get_sqlite_api_kwargs())
    base_storage.register(MockModel)
    yield base_storage
    release_sqlite_storage(base_storage)


@pytest.fixture(scope='module', autouse=True)
def module_cleanup():
    model.DeclarativeBase.metadata.remove(MockModel.__table__)  #pylint: disable=no-member


@pytest.fixture
def context():
    return mock_context.simple(get_sqlite_api_kwargs())


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


def test_relationship_model_ordering(context):
    deployment = context.model.deployment.get_by_name(models.DEPLOYMENT_NAME)
    source_node = context.model.node.get_by_name(models.DEPENDENT_NODE_NAME)
    source_node_instance = context.model.node_instance.get_by_name(
        models.DEPENDENT_NODE_INSTANCE_NAME)
    target_node = context.model.node.get_by_name(models.DEPENDENCY_NODE_NAME)
    target_node_instance = context.model.node_instance.get_by_name(
        models.DEPENDENCY_NODE_INSTANCE_NAME)
    new_node = model.Node(
        name='new_node',
        type='test_node_type',
        type_hierarchy=[],
        number_of_instances=1,
        planned_number_of_instances=1,
        deploy_number_of_instances=1,
        properties={},
        operations=dict((key, {}) for key in operations.NODE_OPERATIONS),
        min_number_of_instances=1,
        max_number_of_instances=1,
        deployment=deployment
    )
    source_to_new_relationship = model.Relationship(
        source_node=source_node,
        target_node=new_node,
        source_interfaces={},
        source_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        target_interfaces={},
        target_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        type='rel_type',
        type_hierarchy=[],
        properties={},
    )
    new_node_instance = model.NodeInstance(
        name='new_node_instance',
        runtime_properties={},
        version=None,
        node=new_node,
        state='',
        scaling_groups=[]
    )
    source_to_new_relationship_instance = model.RelationshipInstance(
        relationship=source_to_new_relationship,
        source_node_instance=source_node_instance,
        target_node_instance=new_node_instance,
    )

    new_to_target_relationship = model.Relationship(
        source_node=new_node,
        target_node=target_node,
        source_interfaces={},
        source_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        target_interfaces={},
        target_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        type='rel_type',
        type_hierarchy=[],
        properties={},
    )
    new_to_target_relationship_instance = model.RelationshipInstance(
        relationship=new_to_target_relationship,
        source_node_instance=new_node_instance,
        target_node_instance=target_node_instance,
    )


    context.model.node.put(new_node)
    context.model.node_instance.put(new_node_instance)
    context.model.relationship.put(source_to_new_relationship)
    context.model.relationship.put(new_to_target_relationship)
    context.model.relationship_instance.put(source_to_new_relationship_instance)
    context.model.relationship_instance.put(new_to_target_relationship_instance)

    def flip_and_assert(node_instance, direction):
        """
        Reversed the order of relationships and assert effects took place.
        :param node_instance: the node instance to operatate on
        :param direction: the type of relationships to flip (inbound/outbount)
        :return:
        """
        assert direction in ('inbound', 'outbound')

        relationships = getattr(node_instance.node, direction + '_relationships')
        relationship_instances = getattr(node_instance, direction + '_relationship_instances')
        assert len(relationships) == 2
        assert len(relationship_instances) == 2

        first_rel, second_rel = relationships
        first_rel_instance, second_rel_instance = relationship_instances
        assert getattr(first_rel, relationships.ordering_attr) == 0
        assert getattr(second_rel, relationships.ordering_attr) == 1
        assert getattr(first_rel_instance, relationship_instances.ordering_attr) == 0
        assert getattr(second_rel_instance, relationship_instances.ordering_attr) == 1

        reversed_relationships = list(reversed(relationships))
        reversed_relationship_instances = list(reversed(relationship_instances))

        assert relationships != reversed_relationships
        assert relationship_instances != reversed_relationship_instances

        relationships[:] = reversed_relationships
        relationship_instances[:] = reversed_relationship_instances
        context.model.node_instance.update(node_instance)

        assert relationships == reversed_relationships
        assert relationship_instances == reversed_relationship_instances

        assert getattr(first_rel, relationships.ordering_attr) == 1
        assert getattr(second_rel, relationships.ordering_attr) == 0
        assert getattr(first_rel_instance, relationship_instances.ordering_attr) == 1
        assert getattr(second_rel_instance, relationship_instances.ordering_attr) == 0

    flip_and_assert(source_node_instance, 'outbound')
    flip_and_assert(target_node_instance, 'inbound')


class StrictClass(model.DeclarativeBase, structure.ModelMixin):
    __tablename__ = 'strict_class'

    strict_dict = sqlalchemy.Column(type.StrictDict(basestring, basestring))
    strict_list = sqlalchemy.Column(type.StrictList(basestring))


def test_strict_dict():

    strict_class = StrictClass()

    def assert_strict(sc):
        with pytest.raises(exceptions.StorageError):
            sc.strict_dict = {'key': 1}

        with pytest.raises(exceptions.StorageError):
            sc.strict_dict = {1: 'value'}

        with pytest.raises(exceptions.StorageError):
            sc.strict_dict = {1: 1}

    assert_strict(strict_class)
    strict_class.strict_dict = {'key': 'value'}
    assert strict_class.strict_dict == {'key': 'value'}

    assert_strict(strict_class)
    with pytest.raises(exceptions.StorageError):
        strict_class.strict_dict['key'] = 1
    with pytest.raises(exceptions.StorageError):
        strict_class.strict_dict[1] = 'value'
    with pytest.raises(exceptions.StorageError):
        strict_class.strict_dict[1] = 1


def test_strict_list():
    strict_class = StrictClass()

    def assert_strict(sc):
        with pytest.raises(exceptions.StorageError):
            sc.strict_list = [1]

    assert_strict(strict_class)
    strict_class.strict_list = ['item']
    assert strict_class.strict_list == ['item']

    assert_strict(strict_class)
    with pytest.raises(exceptions.StorageError):
        strict_class.strict_list[0] = 1
