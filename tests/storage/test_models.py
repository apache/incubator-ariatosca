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
from contextlib import contextmanager

import pytest

from aria import application_model_storage
from aria.storage import (
    exceptions,
    sql_mapi,
)
from aria.storage.model import (
    DeploymentUpdateStep,
    Blueprint,
    Execution,
    Task,
    Plugin,
    Deployment,
    Node,
    NodeInstance,
    Relationship,
    RelationshipInstance,
    DeploymentUpdate,
    DeploymentModification,
)


from tests import mock
from tests.storage import get_sqlite_api_kwargs, release_sqlite_storage


@contextmanager
def sql_storage(storage_func):
    storage = None
    try:
        storage = storage_func()
        yield storage
    finally:
        if storage:
            release_sqlite_storage(storage)


def _empty_storage():
    return application_model_storage(sql_mapi.SQLAlchemyModelAPI,
                                     api_kwargs=get_sqlite_api_kwargs())


def _blueprint_storage():
    storage = _empty_storage()
    blueprint = mock.models.get_blueprint()
    storage.blueprint.put(blueprint)
    return storage


def _deployment_storage():
    storage = _blueprint_storage()
    deployment = mock.models.get_deployment(storage.blueprint.list()[0])
    storage.deployment.put(deployment)
    return storage


def _deployment_update_storage():
    storage = _deployment_storage()
    deployment_update = DeploymentUpdate(
        deployment=storage.deployment.list()[0],
        created_at=now,
        deployment_plan={},
    )
    storage.deployment_update.put(deployment_update)
    return storage


def _node_storage():
    storage = _deployment_storage()
    node = mock.models.get_dependency_node(storage.deployment.list()[0])
    storage.node.put(node)
    return storage


def _nodes_storage():
    storage = _deployment_storage()
    dependent_node = mock.models.get_dependent_node(storage.deployment.list()[0])
    dependency_node = mock.models.get_dependency_node(storage.deployment.list()[0])
    storage.node.put(dependent_node)
    storage.node.put(dependency_node)
    return storage


def _node_instances_storage():
    storage = _nodes_storage()
    dependent_node = storage.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)
    dependency_node = storage.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    dependency_node_instance = mock.models.get_dependency_node_instance(dependency_node)
    dependent_node_instance = mock.models.get_dependent_node_instance(dependent_node)
    storage.node_instance.put(dependency_node_instance)
    storage.node_instance.put(dependent_node_instance)
    return storage


def _execution_storage():
    storage = _deployment_storage()
    execution = mock.models.get_execution(storage.deployment.list()[0])
    plugin = mock.models.get_plugin()
    storage.execution.put(execution)
    storage.plugin.put(plugin)
    return storage


@pytest.fixture
def empty_storage():
    with sql_storage(_empty_storage) as storage:
        yield storage


@pytest.fixture
def blueprint_storage():
    with sql_storage(_blueprint_storage) as storage:
        yield storage


@pytest.fixture
def deployment_storage():
    with sql_storage(_deployment_storage) as storage:
        yield storage


@pytest.fixture
def deployment_update_storage():
    with sql_storage(_deployment_update_storage) as storage:
        yield storage


@pytest.fixture
def node_storage():
    with sql_storage(_node_storage) as storage:
        yield storage


@pytest.fixture
def nodes_storage():
    with sql_storage(_nodes_storage) as storage:
        yield storage


@pytest.fixture
def node_instances_storage():
    with sql_storage(_node_instances_storage) as storage:
        yield storage


@pytest.fixture
def execution_storage():
    with sql_storage(_execution_storage) as storage:
        yield storage


m_cls = type('MockClass')
now = datetime.utcnow()


def _test_model(is_valid, storage, model_name, model_cls, model_kwargs):
    if is_valid:
        model = model_cls(**model_kwargs)
        getattr(storage, model_name).put(model)
        return model
    else:
        with pytest.raises(exceptions.StorageError):
            getattr(storage, model_name).put(model_cls(**model_kwargs))


class TestBlueprint(object):

    @pytest.mark.parametrize(
        'is_valid, plan, description, created_at, updated_at, main_file_name',
        [
            (False, None, 'description', now, now, '/path'),
            (False, {}, {}, now, now, '/path'),
            (False, {}, 'description', 'error', now, '/path'),
            (False, {}, 'description', now, 'error', '/path'),
            (False, {}, 'description', now, now, {}),
            (True, {}, 'description', now, now, '/path'),
        ]
    )
    def test_blueprint_model_creation(self, empty_storage, is_valid, plan, description, created_at,
                                      updated_at, main_file_name):
        _test_model(is_valid=is_valid,
                    storage=empty_storage,
                    model_name='blueprint',
                    model_cls=Blueprint,
                    model_kwargs=dict(plan=plan,
                                      description=description,
                                      created_at=created_at,
                                      updated_at=updated_at,
                                      main_file_name=main_file_name))


class TestDeployment(object):

    @pytest.mark.parametrize(
        'is_valid, name, created_at, description, inputs, groups, permalink, policy_triggers, '
        'policy_types, outputs, scaling_groups, updated_at, workflows',
        [
            (False, m_cls, now, 'desc', {}, {}, 'perlnk', {}, {}, {}, {}, now, {}),
            (False, 'name', m_cls, 'desc', {}, {}, 'perlnk', {}, {}, {}, {}, now, {}),
            (False, 'name', now, m_cls, {}, {}, 'perlnk', {}, {}, {}, {}, now, {}),
            (False, 'name', now, 'desc', m_cls, {}, 'perlnk', {}, {}, {}, {}, now, {}),
            (False, 'name', now, 'desc', {}, m_cls, 'perlnk', {}, {}, {}, {}, now, {}),
            (False, 'name', now, 'desc', {}, {}, m_cls, {}, {}, {}, {}, now, {}),
            (False, 'name', now, 'desc', {}, {}, 'perlnk', m_cls, {}, {}, {}, now, {}),
            (False, 'name', now, 'desc', {}, {}, 'perlnk', {}, m_cls, {}, {}, now, {}),
            (False, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, m_cls, {}, now, {}),
            (False, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, {}, m_cls, now, {}),
            (False, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, {}, {}, m_cls, {}),
            (False, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, {}, {}, now, m_cls),

            (True, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, {}, {}, now, {}),
            (True, None, now, 'desc', {}, {}, 'perlnk', {}, {}, {}, {}, now, {}),
            (True, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, {}, {}, now, {}),
            (True, 'name', now, None, {}, {}, 'perlnk', {}, {}, {}, {}, now, {}),
            (True, 'name', now, 'desc', None, {}, 'perlnk', {}, {}, {}, {}, now, {}),
            (True, 'name', now, 'desc', {}, None, 'perlnk', {}, {}, {}, {}, now, {}),
            (True, 'name', now, 'desc', {}, {}, None, {}, {}, {}, {}, now, {}),
            (True, 'name', now, 'desc', {}, {}, 'perlnk', None, {}, {}, {}, now, {}),
            (True, 'name', now, 'desc', {}, {}, 'perlnk', {}, None, {}, {}, now, {}),
            (True, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, None, {}, now, {}),
            (True, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, {}, None, now, {}),
            (True, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, {}, {}, None, {}),
            (True, 'name', now, 'desc', {}, {}, 'perlnk', {}, {}, {}, {}, now, None),
        ]
    )
    def test_deployment_model_creation(self, deployment_storage, is_valid, name, created_at,
                                       description, inputs, groups, permalink, policy_triggers,
                                       policy_types, outputs, scaling_groups, updated_at,
                                       workflows):
        deployment = _test_model(is_valid=is_valid,
                                 storage=deployment_storage,
                                 model_name='deployment',
                                 model_cls=Deployment,
                                 model_kwargs=dict(
                                     name=name,
                                     blueprint=deployment_storage.blueprint.list()[0],
                                     created_at=created_at,
                                     description=description,
                                     inputs=inputs,
                                     groups=groups,
                                     permalink=permalink,
                                     policy_triggers=policy_triggers,
                                     policy_types=policy_types,
                                     outputs=outputs,
                                     scaling_groups=scaling_groups,
                                     updated_at=updated_at,
                                     workflows=workflows
                                 ))
        if is_valid:
            assert deployment.blueprint == deployment_storage.blueprint.list()[0]


class TestExecution(object):

    @pytest.mark.parametrize(
        'is_valid, created_at, started_at, ended_at, error, is_system_workflow, parameters, '
        'status, workflow_name',
        [
            (False, m_cls, now, now, 'error', False, {}, Execution.STARTED, 'wf_name'),
            (False, now, m_cls, now, 'error', False, {}, Execution.STARTED, 'wf_name'),
            (False, now, now, m_cls, 'error', False, {}, Execution.STARTED, 'wf_name'),
            (False, now, now, now, m_cls, False, {}, Execution.STARTED, 'wf_name'),
            (False, now, now, now, 'error', False, m_cls, Execution.STARTED, 'wf_name'),
            (False, now, now, now, 'error', False, {}, m_cls, 'wf_name'),
            (False, now, now, now, 'error', False, {}, Execution.STARTED, m_cls),

            (True, now, now, now, 'error', False, {}, Execution.STARTED, 'wf_name'),
            (True, now, None, now, 'error', False, {}, Execution.STARTED, 'wf_name'),
            (True, now, now, None, 'error', False, {}, Execution.STARTED, 'wf_name'),
            (True, now, now, now, None, False, {}, Execution.STARTED, 'wf_name'),
            (True, now, now, now, 'error', False, None, Execution.STARTED, 'wf_name'),
        ]
    )
    def test_execution_model_creation(self, deployment_storage, is_valid, created_at, started_at,
                                      ended_at, error, is_system_workflow, parameters, status,
                                      workflow_name):
        execution = _test_model(is_valid=is_valid,
                                storage=deployment_storage,
                                model_name='execution',
                                model_cls=Execution,
                                model_kwargs=dict(
                                    deployment=deployment_storage.deployment.list()[0],
                                    created_at=created_at,
                                    started_at=started_at,
                                    ended_at=ended_at,
                                    error=error,
                                    is_system_workflow=is_system_workflow,
                                    parameters=parameters,
                                    status=status,
                                    workflow_name=workflow_name,
                                ))
        if is_valid:
            assert execution.deployment == deployment_storage.deployment.list()[0]
            assert execution.blueprint == deployment_storage.blueprint.list()[0]

    def test_execution_status_transition(self):
        def create_execution(status):
            execution = Execution(
                id='e_id',
                workflow_name='w_name',
                status=status,
                parameters={},
                created_at=now,
            )
            return execution

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


class TestDeploymentUpdate(object):
    @pytest.mark.parametrize(
        'is_valid, created_at, deployment_plan, deployment_update_node_instances, '
        'deployment_update_deployment, deployment_update_nodes, modified_entity_ids, state',
        [
            (False, m_cls, {}, {}, {}, [], {}, 'state'),
            (False, now, m_cls, {}, {}, [], {}, 'state'),
            (False, now, {}, m_cls, {}, [], {}, 'state'),
            (False, now, {}, {}, m_cls, [], {}, 'state'),
            (False, now, {}, {}, {}, m_cls, {}, 'state'),
            (False, now, {}, {}, {}, [], m_cls, 'state'),
            (False, now, {}, {}, {}, [], {}, m_cls),

            (True, now, {}, {}, {}, [], {}, 'state'),
            (True, now, {}, None, {}, [], {}, 'state'),
            (True, now, {}, {}, None, [], {}, 'state'),
            (True, now, {}, {}, {}, None, {}, 'state'),
            (True, now, {}, {}, {}, [], None, 'state'),
            (True, now, {}, {}, {}, [], {}, None),
        ]
    )
    def test_deployment_update_model_creation(self, deployment_storage, is_valid, created_at,
                                              deployment_plan, deployment_update_node_instances,
                                              deployment_update_deployment, deployment_update_nodes,
                                              modified_entity_ids, state):
        deployment_update = _test_model(
            is_valid=is_valid,
            storage=deployment_storage,
            model_name='deployment_update',
            model_cls=DeploymentUpdate,
            model_kwargs=dict(
                deployment=deployment_storage.deployment.list()[0],
                created_at=created_at,
                deployment_plan=deployment_plan,
                deployment_update_node_instances=deployment_update_node_instances,
                deployment_update_deployment=deployment_update_deployment,
                deployment_update_nodes=deployment_update_nodes,
                modified_entity_ids=modified_entity_ids,
                state=state,
            ))
        if is_valid:
            assert deployment_update.deployment == deployment_storage.deployment.list()[0]


class TestDeploymentUpdateStep(object):

    @pytest.mark.parametrize(
        'is_valid, action, entity_id, entity_type',
        [
            (False, m_cls, 'id', DeploymentUpdateStep.ENTITY_TYPES.NODE),
            (False, DeploymentUpdateStep.ACTION_TYPES.ADD, m_cls,
             DeploymentUpdateStep.ENTITY_TYPES.NODE),
            (False, DeploymentUpdateStep.ACTION_TYPES.ADD, 'id', m_cls),

            (True, DeploymentUpdateStep.ACTION_TYPES.ADD, 'id',
             DeploymentUpdateStep.ENTITY_TYPES.NODE)
        ]
    )
    def test_deployment_update_step_model_creation(self, deployment_update_storage, is_valid,
                                                   action, entity_id, entity_type):
        deployment_update_step = _test_model(
            is_valid=is_valid,
            storage=deployment_update_storage,
            model_name='deployment_update_step',
            model_cls=DeploymentUpdateStep,
            model_kwargs=dict(
                deployment_update=deployment_update_storage.deployment_update.list()[0],
                action=action,
                entity_id=entity_id,
                entity_type=entity_type
            ))
        if is_valid:
            assert deployment_update_step.deployment_update == \
                  deployment_update_storage.deployment_update.list()[0]

    def test_deployment_update_step_order(self):
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

        remove_rel = DeploymentUpdateStep(
            id='remove_step',
            action='remove',
            entity_type='relationship',
            entity_id='relationship_id')

        assert remove_rel < remove_node < add_node < add_rel
        assert not add_node < None


class TestDeploymentModification(object):
    @pytest.mark.parametrize(
        'is_valid, context, created_at, ended_at, modified_nodes, node_instances, status',
        [
            (False, m_cls, now, now, {}, {}, DeploymentModification.STARTED),
            (False, {}, m_cls, now, {}, {}, DeploymentModification.STARTED),
            (False, {}, now, m_cls, {}, {}, DeploymentModification.STARTED),
            (False, {}, now, now, m_cls, {}, DeploymentModification.STARTED),
            (False, {}, now, now, {}, m_cls, DeploymentModification.STARTED),
            (False, {}, now, now, {}, {}, m_cls),

            (True, {}, now, now, {}, {}, DeploymentModification.STARTED),
            (True, {}, now, None, {}, {}, DeploymentModification.STARTED),
            (True, {}, now, now, None, {}, DeploymentModification.STARTED),
            (True, {}, now, now, {}, None, DeploymentModification.STARTED),
        ]
    )
    def test_deployment_modification_model_creation(self, deployment_storage, is_valid, context,
                                                    created_at, ended_at, modified_nodes,
                                                    node_instances, status):
        deployment_modification = _test_model(
            is_valid=is_valid,
            storage=deployment_storage,
            model_name='deployment_modification',
            model_cls=DeploymentModification,
            model_kwargs=dict(
                deployment=deployment_storage.deployment.list()[0],
                context=context,
                created_at=created_at,
                ended_at=ended_at,
                modified_nodes=modified_nodes,
                node_instances=node_instances,
                status=status,
            ))
        if is_valid:
            assert deployment_modification.deployment == deployment_storage.deployment.list()[0]


class TestNode(object):
    @pytest.mark.parametrize(
        'is_valid, name, deploy_number_of_instances, max_number_of_instances, '
        'min_number_of_instances, number_of_instances, planned_number_of_instances, plugins, '
        'properties, operations, type, type_hierarchy',
        [
            (False, m_cls, 1, 1, 1, 1, 1, [], {}, {}, 'type', []),
            (False, 'name', m_cls, 1, 1, 1, 1, [], {}, {}, 'type', []),
            (False, 'name', 1, m_cls, 1, 1, 1, [], {}, {}, 'type', []),
            (False, 'name', 1, 1, m_cls, 1, 1, [], {}, {}, 'type', []),
            (False, 'name', 1, 1, 1, m_cls, 1, [], {}, {}, 'type', []),
            (False, 'name', 1, 1, 1, 1, m_cls, [], {}, {}, 'type', []),
            (False, 'name', 1, 1, 1, 1, 1, m_cls, {}, {}, 'type', []),
            (False, 'name', 1, 1, 1, 1, 1, [], m_cls, {}, 'type', []),
            (False, 'name', 1, 1, 1, 1, 1, [], {}, m_cls, 'type', []),
            (False, 'name', 1, 1, 1, 1, 1, [], {}, {}, m_cls, []),
            (False, 'name', 1, 1, 1, 1, 1, [], {}, {}, 'type', m_cls),

            (True, 'name', 1, 1, 1, 1, 1, [], {}, {}, 'type', []),
            (True, 'name', 1, 1, 1, 1, 1, None, {}, {}, 'type', []),
            (True, 'name', 1, 1, 1, 1, 1, [], None, {}, 'type', []),
            (True, 'name', 1, 1, 1, 1, 1, [], {}, None, 'type', []),
            (True, 'name', 1, 1, 1, 1, 1, [], {}, {}, 'type', None),
        ]
    )
    def test_node_model_creation(self, deployment_storage, is_valid, name,
                                 deploy_number_of_instances, max_number_of_instances,
                                 min_number_of_instances, number_of_instances,
                                 planned_number_of_instances, plugins,
                                 properties, operations, type, type_hierarchy):
        node = _test_model(
            is_valid=is_valid,
            storage=deployment_storage,
            model_name='node',
            model_cls=Node,
            model_kwargs=dict(
                name=name,
                deploy_number_of_instances=deploy_number_of_instances,
                max_number_of_instances=max_number_of_instances,
                min_number_of_instances=min_number_of_instances,
                number_of_instances=number_of_instances,
                planned_number_of_instances=planned_number_of_instances,
                plugins=plugins,
                properties=properties,
                operations=operations,
                type=type,
                type_hierarchy=type_hierarchy,
                deployment=deployment_storage.deployment.list()[0]
            ))
        if is_valid:
            assert node.deployment == deployment_storage.deployment.list()[0]


class TestRelationship(object):
    @pytest.mark.parametrize(
        'is_valid, source_interfaces, source_operations, target_interfaces, target_operations, '
        'type, type_hierarchy, properties',
        [
            (False, m_cls, {}, {}, {}, 'type', [], {}),
            (False, {}, m_cls, {}, {}, 'type', [], {}),
            (False, {}, {}, m_cls, {}, 'type', [], {}),
            (False, {}, {}, {}, m_cls, 'type', [], {}),
            (False, {}, {}, {}, {}, m_cls, [], {}),
            (False, {}, {}, {}, {}, 'type', m_cls, {}),
            (False, {}, {}, {}, {}, 'type', [], m_cls),

            (True, {}, {}, {}, {}, 'type', [], {}),
            (True, None, {}, {}, {}, 'type', [], {}),
            (True, {}, {}, None, {}, 'type', [], {}),
            (True, {}, {}, {}, {}, 'type', None, {}),
            (True, {}, {}, {}, {}, 'type', [], None),
        ]
        )
    def test_relationship_model_ceration(self, nodes_storage, is_valid, source_interfaces,
                                         source_operations, target_interfaces, target_operations,
                                         type, type_hierarchy, properties):
        relationship = _test_model(
            is_valid=is_valid,
            storage=nodes_storage,
            model_name='relationship',
            model_cls=Relationship,
            model_kwargs=dict(
                source_node=nodes_storage.node.list()[1],
                target_node=nodes_storage.node.list()[0],
                source_interfaces=source_interfaces,
                source_operations=source_operations,
                target_interfaces=target_interfaces,
                target_operations=target_operations,
                type=type,
                type_hierarchy=type_hierarchy,
                properties=properties,
            ))
        if is_valid:
            assert relationship.source_node == nodes_storage.node.list()[1]
            assert relationship.target_node == nodes_storage.node.list()[0]


class TestNodeInstance(object):
    @pytest.mark.parametrize(
        'is_valid, name, runtime_properties, scaling_groups, state, version',
        [
            (False, m_cls, {}, [], 'state', 1),
            (False, 'name', m_cls, [], 'state', 1),
            (False, 'name', {}, m_cls, 'state', 1),
            (False, 'name', {}, [], m_cls, 1),
            (False, m_cls, {}, [], 'state', m_cls),

            (True, 'name', {}, [], 'state', 1),
            (True, None, {}, [], 'state', 1),
            (True, 'name', None, [], 'state', 1),
            (True, 'name', {}, None, 'state', 1),
            (True, 'name', {}, [], 'state', None),
        ]
    )
    def test_node_instance_model_creation(self, node_storage, is_valid, name, runtime_properties,
                                          scaling_groups, state, version):
        node_instance = _test_model(
            is_valid=is_valid,
            storage=node_storage,
            model_name='node_instance',
            model_cls=NodeInstance,
            model_kwargs=dict(
                node=node_storage.node.list()[0],
                name=name,
                runtime_properties=runtime_properties,
                scaling_groups=scaling_groups,
                state=state,
                version=version,
            ))
        if is_valid:
            assert node_instance.node == node_storage.node.list()[0]
            assert node_instance.deployment == node_storage.deployment.list()[0]


class TestRelationshipInstance(object):
    def test_relatiship_instance_model_creation(self, node_instances_storage):
        relationship = mock.models.get_relationship(
            source=node_instances_storage.node.get_by_name(mock.models.DEPENDENT_NODE_NAME),
            target=node_instances_storage.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
        )
        node_instances_storage.relationship.put(relationship)
        node_instances = node_instances_storage.node_instance
        source_node_instance = node_instances.get_by_name(mock.models.DEPENDENT_NODE_INSTANCE_NAME)
        target_node_instance = node_instances.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)

        relationship_instance = _test_model(
            is_valid=True,
            storage=node_instances_storage,
            model_name='relationship_instance',
            model_cls=RelationshipInstance,
            model_kwargs=dict(
                relationship=relationship,
                source_node_instance=source_node_instance,
                target_node_instance=target_node_instance
            ))
        assert relationship_instance.relationship == relationship
        assert relationship_instance.source_node_instance == source_node_instance
        assert relationship_instance.target_node_instance == target_node_instance


class TestPlugin(object):
    @pytest.mark.parametrize(
        'is_valid, archive_name, distribution, distribution_release, '
        'distribution_version, package_name, package_source, '
        'package_version, supported_platform, supported_py_versions, uploaded_at, wheels',
        [
            (False, m_cls, 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src', 'pak_ver',
             'sup_plat', [], now, []),
            (False, 'arc_name', m_cls, 'dis_rel', 'dis_ver', 'pak_name', 'pak_src', 'pak_ver',
             'sup_plat', [], now, []),
            (False, 'arc_name', 'dis_name', m_cls, 'dis_ver', 'pak_name', 'pak_src', 'pak_ver',
             'sup_plat', [], now, []),
            (False, 'arc_name', 'dis_name', 'dis_rel', m_cls, 'pak_name', 'pak_src', 'pak_ver',
             'sup_plat', [], now, []),
            (False, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', m_cls, 'pak_src', 'pak_ver',
             'sup_plat', [], now, []),
            (False, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', m_cls, 'pak_ver',
             'sup_plat', [], now, []),
            (False, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src', m_cls,
             'sup_plat', [], now, []),
            (False, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src',
             'pak_ver', m_cls, [], now, []),
            (False, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src',
             'pak_ver', 'sup_plat', m_cls, now, []),
            (False, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src',
             'pak_ver', 'sup_plat', [], m_cls, []),
            (False, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src',
             'pak_ver', 'sup_plat', [], now, m_cls),

            (True, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src', 'pak_ver',
             'sup_plat', [], now, []),
            (True, 'arc_name', None, 'dis_rel', 'dis_ver', 'pak_name', 'pak_src', 'pak_ver',
             'sup_plat', [], now, []),
            (True, 'arc_name', 'dis_name', None, 'dis_ver', 'pak_name', 'pak_src', 'pak_ver',
             'sup_plat', [], now, []),
            (True, 'arc_name', 'dis_name', 'dis_rel', None, 'pak_name', 'pak_src', 'pak_ver',
             'sup_plat', [], now, []),
            (True, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src',
             'pak_ver', 'sup_plat', [], now, []),
            (True, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', None, 'pak_ver',
             'sup_plat', [], now, []),
            (True, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src', None,
             'sup_plat', [], now, []),
            (True, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src',
             'pak_ver', None, [], now, []),
            (True, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src',
             'pak_ver', 'sup_plat', None, now, []),
            (True, 'arc_name', 'dis_name', 'dis_rel', 'dis_ver', 'pak_name', 'pak_src',
             'pak_ver', 'sup_plat', [], now, []),
        ]
    )
    def test_plugin_model_creation(self, empty_storage, is_valid, archive_name, distribution,
                                   distribution_release, distribution_version,
                                   package_name, package_source, package_version,
                                   supported_platform, supported_py_versions, uploaded_at, wheels):
        _test_model(is_valid=is_valid,
                    storage=empty_storage,
                    model_name='plugin',
                    model_cls=Plugin,
                    model_kwargs=dict(
                        archive_name=archive_name,
                        distribution=distribution,
                        distribution_release=distribution_release,
                        distribution_version=distribution_version,
                        package_name=package_name,
                        package_source=package_source,
                        package_version=package_version,
                        supported_platform=supported_platform,
                        supported_py_versions=supported_py_versions,
                        uploaded_at=uploaded_at,
                        wheels=wheels,
                    ))


class TestTask(object):

    @pytest.mark.parametrize(
        'is_valid, status, due_at, started_at, ended_at, max_attempts, retry_count, '
        'retry_interval, ignore_failure, name, operation_mapping, inputs, plugin_id',
        [
            (False, m_cls, now, now, now, 1, 1, 1, True, 'name', 'map', {}, '1'),
            (False, Task.STARTED, m_cls, now, now, 1, 1, 1, True, 'name', 'map', {}, '1'),
            (False, Task.STARTED, now, m_cls, now, 1, 1, 1, True, 'name', 'map', {}, '1'),
            (False, Task.STARTED, now, now, m_cls, 1, 1, 1, True, 'name', 'map', {}, '1'),
            (False, Task.STARTED, now, now, now, m_cls, 1, 1, True, 'name', 'map', {}, '1'),
            (False, Task.STARTED, now, now, now, 1, m_cls, 1, True, 'name', 'map', {}, '1'),
            (False, Task.STARTED, now, now, now, 1, 1, m_cls, True, 'name', 'map', {}, '1'),
            (False, Task.STARTED, now, now, now, 1, 1, 1, True, m_cls, 'map', {}, '1'),
            (False, Task.STARTED, now, now, now, 1, 1, 1, True, 'name', m_cls, {}, '1'),
            (False, Task.STARTED, now, now, now, 1, 1, 1, True, 'name', 'map', m_cls, '1'),
            (False, Task.STARTED, now, now, now, 1, 1, 1, True, 'name', 'map', {}, m_cls),

            (True, Task.STARTED, now, now, now, 1, 1, 1, True, 'name', 'map', {}, '1'),
            (True, Task.STARTED, None, now, now, 1, 1, 1, True, 'name', 'map', {}, '1'),
            (True, Task.STARTED, now, None, now, 1, 1, 1, True, 'name', 'map', {}, '1'),
            (True, Task.STARTED, now, now, None, 1, 1, 1, True, 'name', 'map', {}, '1'),
            (True, Task.STARTED, now, now, now, 1, None, 1, True, 'name', 'map', {}, '1'),
            (True, Task.STARTED, now, now, now, 1, 1, None, True, 'name', 'map', {}, '1'),
            (True, Task.STARTED, now, now, now, 1, 1, 1, None, 'name', 'map', {}, '1'),
            (True, Task.STARTED, now, now, now, 1, 1, 1, True, None, 'map', {}, '1'),
            (True, Task.STARTED, now, now, now, 1, 1, 1, True, 'name', None, {}, '1'),
            (True, Task.STARTED, now, now, now, 1, 1, 1, True, 'name', 'map', None, '1'),
            (True, Task.STARTED, now, now, now, 1, 1, 1, True, 'name', 'map', {}, None),
        ]
    )
    def test_task_model_creation(self, execution_storage, is_valid, status, due_at, started_at,
                                 ended_at, max_attempts, retry_count, retry_interval,
                                 ignore_failure, name, operation_mapping, inputs, plugin_id):
        task = _test_model(
            is_valid=is_valid,
            storage=execution_storage,
            model_name='task',
            model_cls=Task,
            model_kwargs=dict(
                status=status,
                execution=execution_storage.execution.list()[0],
                due_at=due_at,
                started_at=started_at,
                ended_at=ended_at,
                max_attempts=max_attempts,
                retry_count=retry_count,
                retry_interval=retry_interval,
                ignore_failure=ignore_failure,
                name=name,
                operation_mapping=operation_mapping,
                inputs=inputs,
                plugin_fk=plugin_id,
            ))
        if is_valid:
            assert task.execution == execution_storage.execution.list()[0]
            if task.plugin:
                assert task.plugin == execution_storage.plugin.list()[0]

    def test_task_max_attempts_validation(self):
        def create_task(max_attempts):
            Task(execution_fk='eid',
                 name='name',
                 operation_mapping='',
                 inputs={},
                 max_attempts=max_attempts)
        create_task(max_attempts=1)
        create_task(max_attempts=2)
        create_task(max_attempts=Task.INFINITE_RETRIES)
        with pytest.raises(ValueError):
            create_task(max_attempts=0)
        with pytest.raises(ValueError):
            create_task(max_attempts=-2)
