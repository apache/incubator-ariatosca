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

import json
from datetime import datetime

import pytest

from aria.storage import Model, Field
from aria.exceptions import StorageError
from aria.storage.models import (
    DeploymentUpdateStep,
    Relationship,
    RelationshipInstance,
    Node,
    NodeInstance,
    Blueprint,
    Execution,
    Task
)
from tests.mock import models

# TODO: add tests per model


def test_base_model_without_fields():
    with pytest.raises(StorageError, message="Id field has to be in model fields"):
        Model()


def test_base_model_members():
    _test_field = Field()

    class TestModel1(Model):
        test_field = _test_field
        id = Field(default='test_id')

    assert _test_field is TestModel1.test_field

    test_model = TestModel1(test_field='test_field_value', id='test_id')

    assert repr(test_model) == "TestModel1(fields=['id', 'test_field'])"
    expected = {'test_field': 'test_field_value', 'id': 'test_id'}
    assert json.loads(test_model.json) == expected
    assert test_model.fields_dict == expected

    with pytest.raises(StorageError):
        TestModel1()

    with pytest.raises(StorageError):
        TestModel1(test_field='test_field_value', id='test_id', unsupported_field='value')

    class TestModel2(Model):
        test_field = Field()
        id = Field()

    with pytest.raises(StorageError):
        TestModel2()


def test_blueprint_model():
    Blueprint(
        plan={},
        id='id',
        description='description',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        main_file_name='/path',
    )
    with pytest.raises(TypeError):
        Blueprint(
            plan=None,
            id='id',
            description='description',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            main_file_name='/path',
        )
    with pytest.raises(TypeError):
        Blueprint(
            plan={},
            id=999,
            description='description',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            main_file_name='/path',
        )
    with pytest.raises(TypeError):
        Blueprint(
            plan={},
            id='id',
            description=999,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            main_file_name='/path',
        )
    with pytest.raises(TypeError):
        Blueprint(
            plan={},
            id='id',
            description='description',
            created_at='error',
            updated_at=datetime.utcnow(),
            main_file_name='/path',
        )
    with pytest.raises(TypeError):
        Blueprint(
            plan={},
            id='id',
            description='description',
            created_at=datetime.utcnow(),
            updated_at=None,
            main_file_name='/path',
        )
    with pytest.raises(TypeError):
        Blueprint(
            plan={},
            id='id',
            description='description',
            created_at=datetime.utcnow(),
            updated_at=None,
            main_file_name=88,
        )
    Blueprint(
        plan={},
        description='description',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        main_file_name='/path',
    )


def test_deployment_update_step_model():
    add_node = DeploymentUpdateStep(
        id='add_step',
        action='add',
        entity_type='node',
        entity_id='node_id')

    modify_node = DeploymentUpdateStep(
        id='modify_step',
        action='modify',
        entity_type='node',
        entity_id='node_id')

    remove_node = DeploymentUpdateStep(
        id='remove_step',
        action='remove',
        entity_type='node',
        entity_id='node_id')

    for step in (add_node, modify_node, remove_node):
        assert hash((step.id, step.entity_id)) == hash(step)

    assert remove_node < modify_node < add_node
    assert not remove_node > modify_node > add_node

    add_rel = DeploymentUpdateStep(
        id='add_step',
        action='add',
        entity_type='relationship',
        entity_id='relationship_id')

    # modify_rel = DeploymentUpdateStep(
    #     id='modify_step',
    #     action='modify',
    #     entity_type='relationship',
    #     entity_id='relationship_id')

    remove_rel = DeploymentUpdateStep(
        id='remove_step',
        action='remove',
        entity_type='relationship',
        entity_id='relationship_id')

    assert remove_rel < remove_node < add_node < add_rel
    assert not add_node < None
    # TODO fix logic here so that pylint is happy
    # assert not modify_node < modify_rel and not modify_rel < modify_node


def _relationship(id=''):
    return Relationship(
        id='rel{0}'.format(id),
        target_id='target{0}'.format(id),
        source_interfaces={},
        source_operations={},
        target_interfaces={},
        target_operations={},
        type='type{0}'.format(id),
        type_hierarchy=[],
        properties={})


def test_relationships():
    relationships = [_relationship(index) for index in xrange(3)]

    node = Node(
        blueprint_id='blueprint_id',
        type='type',
        type_hierarchy=None,
        number_of_instances=1,
        planned_number_of_instances=1,
        deploy_number_of_instances=1,
        properties={},
        operations={},
        relationships=relationships,
        min_number_of_instances=1,
        max_number_of_instances=1)

    for index in xrange(3):
        assert relationships[index] is \
               next(node.relationships_by_target('target{0}'.format(index)))

    relationship = _relationship()

    node = Node(
        blueprint_id='blueprint_id',
        type='type',
        type_hierarchy=None,
        number_of_instances=1,
        planned_number_of_instances=1,
        deploy_number_of_instances=1,
        properties={},
        operations={},
        relationships=[relationship, relationship, relationship],
        min_number_of_instances=1,
        max_number_of_instances=1)

    for node_relationship in node.relationships_by_target('target'):
        assert relationship is node_relationship


def test_relationship_instance():
    relationship = _relationship()
    relationship_instances = [RelationshipInstance(
        id='rel{0}'.format(index),
        target_id='target_{0}'.format(index % 2),
        target_name='',
        relationship=relationship,
        type='type{0}'.format(index)) for index in xrange(3)]

    node_instance = NodeInstance(
        deployment_id='deployment_id',
        runtime_properties={},
        version='1',
        relationship_instances=relationship_instances,
        node=Node(
            blueprint_id='blueprint_id',
            type='type',
            type_hierarchy=None,
            number_of_instances=1,
            planned_number_of_instances=1,
            deploy_number_of_instances=1,
            properties={},
            operations={},
            relationships=[],
            min_number_of_instances=1,
            max_number_of_instances=1),
        scaling_groups=()
    )

    from itertools import chain

    assert set(relationship_instances) == set(chain(
        node_instance.relationships_by_target('target_0'),
        node_instance.relationships_by_target('target_1')))


def test_execution_status_transition():
    def create_execution(status):
        return Execution(
            id='e_id',
            deployment_id='d_id',
            workflow_id='w_id',
            blueprint_id='b_id',
            status=status,
            parameters={}
        )

    valid_transitions = {
        Execution.PENDING: [Execution.STARTED,
                            Execution.CANCELLED,
                            Execution.PENDING],
        Execution.STARTED: [Execution.FAILED,
                            Execution.TERMINATED,
                            Execution.CANCELLED,
                            Execution.CANCELLING,
                            Execution.STARTED],
        Execution.CANCELLING: [Execution.FAILED,
                               Execution.TERMINATED,
                               Execution.CANCELLED,
                               Execution.CANCELLING],
        Execution.FAILED: [Execution.FAILED],
        Execution.TERMINATED: [Execution.TERMINATED],
        Execution.CANCELLED: [Execution.CANCELLED]
    }

    invalid_transitions = {
        Execution.PENDING: [Execution.FAILED,
                            Execution.TERMINATED,
                            Execution.CANCELLING],
        Execution.STARTED: [Execution.PENDING],
        Execution.CANCELLING: [Execution.PENDING,
                               Execution.STARTED],
        Execution.FAILED: [Execution.PENDING,
                           Execution.STARTED,
                           Execution.TERMINATED,
                           Execution.CANCELLED,
                           Execution.CANCELLING],
        Execution.TERMINATED: [Execution.PENDING,
                               Execution.STARTED,
                               Execution.FAILED,
                               Execution.CANCELLED,
                               Execution.CANCELLING],
        Execution.CANCELLED: [Execution.PENDING,
                              Execution.STARTED,
                              Execution.FAILED,
                              Execution.TERMINATED,
                              Execution.CANCELLING],
    }

    for current_status, valid_transitioned_statues in valid_transitions.items():
        for transitioned_status in valid_transitioned_statues:
            execution = create_execution(current_status)
            execution.status = transitioned_status

    for current_status, invalid_transitioned_statues in invalid_transitions.items():
        for transitioned_status in invalid_transitioned_statues:
            execution = create_execution(current_status)
            with pytest.raises(ValueError):
                execution.status = transitioned_status


def test_task_max_attempts_validation():
    def create_task(max_attempts):
        Task(execution_id='eid',
             name='name',
             operation_details={},
             inputs={},
             node_instance=models.get_dependency_node_instance(),
             max_attempts=max_attempts)
    create_task(max_attempts=1)
    create_task(max_attempts=2)
    create_task(max_attempts=Task.INFINITE_RETRIES)
    with pytest.raises(ValueError):
        create_task(max_attempts=0)
    with pytest.raises(ValueError):
        create_task(max_attempts=-2)
