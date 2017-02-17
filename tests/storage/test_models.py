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
from aria.modeling.model import (
    ServiceTemplate,
    ServiceInstance,
    ServiceInstanceUpdate,
    ServiceInstanceUpdateStep,
    ServiceInstanceModification,
    Execution,
    Task,
    Plugin,
    Relationship,
    NodeTemplate,
    Node,
    Parameter
)

from tests import mock
from ..storage import release_sqlite_storage, init_inmemory_model_storage


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
                                     initiator=init_inmemory_model_storage)


def _service_template_storage():
    storage = _empty_storage()
    service_template = mock.models.get_blueprint()
    storage.service_template.put(service_template)
    return storage


def _service_instance_storage():
    storage = _service_template_storage()
    service_instance = mock.models.get_deployment(
        storage.service_template.get_by_name(mock.models.BLUEPRINT_NAME))
    storage.service_instance.put(service_instance)
    return storage


def _service_instance_update_storage():
    storage = _service_instance_storage()
    service_instance_update = ServiceInstanceUpdate(
        service_instance=storage.service_instance.list()[0],
        created_at=now,
        service_instance_plan={},
    )
    storage.service_instance_update.put(service_instance_update)
    return storage


def _node_template_storage():
    storage = _service_instance_storage()
    node_template = mock.models.get_dependency_node(storage.service_instance.list()[0])
    storage.node_template.put(node_template)
    return storage


def _nodes_storage():
    storage = _nodes_storage()
    service_instance = storage.service_instance.get_by_name(mock.models.DEPLOYMENT_NAME)
    dependent_node_template = storage.node_template.get_by_name(mock.models.DEPENDENT_NODE_NAME)
    dependency_node_template = storage.node_template.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    dependency_node = mock.models.get_dependency_node_instance(dependency_node_template,
                                                               service_instance)
    dependent_node = mock.models.get_dependent_node_instance(dependent_node_template,
                                                             service_instance)
    storage.node.put(dependency_node)
    storage.node.put(dependent_node)
    return storage


def _execution_storage():
    storage = _service_instance_storage()
    execution = mock.models.get_execution(storage.service_instance.list()[0])
    plugin = mock.models.get_plugin()
    storage.execution.put(execution)
    storage.plugin.put(plugin)
    return storage


@pytest.fixture
def empty_storage():
    with sql_storage(_empty_storage) as storage:
        yield storage


@pytest.fixture
def service_template_storage():
    with sql_storage(_service_template_storage) as storage:
        yield storage


@pytest.fixture
def service_instance_storage():
    with sql_storage(_service_instance_storage) as storage:
        yield storage


@pytest.fixture
def service_instance_update_storage():
    with sql_storage(_service_instance_update_storage) as storage:
        yield storage


@pytest.fixture
def node_template_storage():
    with sql_storage(_node_template_storage) as storage:
        yield storage


@pytest.fixture
def nodes_storage():
    with sql_storage(_nodes_storage) as storage:
        yield storage


@pytest.fixture
def execution_storage():
    with sql_storage(_execution_storage) as storage:
        yield storage


m_cls = type('MockClass')
now = datetime.utcnow()


def _test_model(is_valid, storage, model_cls, model_kwargs):
    if is_valid:
        model = model_cls(**model_kwargs)
        getattr(storage, model_cls.__modelname__).put(model)
        return model
    else:
        with pytest.raises((exceptions.StorageError, TypeError),):
            getattr(storage, model_cls.__modelname__).put(model_cls(**model_kwargs))


class TestServiceTemplate(object):

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
                    model_cls=ServiceTemplate,
                    model_kwargs=dict(
                        plan=plan,
                        description=description,
                        created_at=created_at,
                        updated_at=updated_at,
                        main_file_name=main_file_name)
                   )


class TestServiceInstance(object):

    @pytest.mark.parametrize(
        'is_valid, name, created_at, description, inputs, permalink, policy_triggers, '
        'policy_types, outputs, scaling_groups, updated_at, workflows',
        [
            (False, m_cls, now, 'desc', [], 'perlnk', {}, {}, [], {}, now, {}),
            (False, 'name', m_cls, 'desc', [], 'perlnk', {}, {}, [], {}, now, {}),
            (False, 'name', now, m_cls, [], 'perlnk', {}, {}, [], {}, now, {}),
            (False, 'name', now, 'desc', [], m_cls, {}, {}, [], {}, now, {}),
            (False, 'name', now, 'desc', [], 'perlnk', m_cls, {}, [], {}, now, {}),
            (False, 'name', now, 'desc', [], 'perlnk', {}, m_cls, [], {}, now, {}),
            (False, 'name', now, 'desc', [], 'perlnk', {}, {}, m_cls, {}, now, {}),
            (False, 'name', now, 'desc', [], 'perlnk', {}, {}, [], m_cls, now, {}),
            (False, 'name', now, 'desc', [], 'perlnk', {}, {}, [], {}, m_cls, {}),
            (False, 'name', now, 'desc', [], 'perlnk', {}, {}, [], {}, now, m_cls),

            (True, 'name', now, 'desc', [], 'perlnk', {}, {}, [], {}, now, {}),
            (True, None, now, 'desc', [], 'perlnk', {}, {}, [], {}, now, {}),
            (True, 'name', now, 'desc', [], 'perlnk', {}, {}, [], {}, now, {}),
            (True, 'name', now, None, [], 'perlnk', {}, {}, [], {}, now, {}),
            (True, 'name', now, 'desc', [], 'perlnk', {}, {}, [], {}, now, {}),
            (True, 'name', now, 'desc', [], None, {}, {}, [], {}, now, {}),
            (True, 'name', now, 'desc', [], 'perlnk', None, {}, [], {}, now, {}),
            (True, 'name', now, 'desc', [], 'perlnk', {}, None, [], {}, now, {}),
            (True, 'name', now, 'desc', [], 'perlnk', {}, {}, [], None, now, {}),
            (True, 'name', now, 'desc', [], 'perlnk', {}, {}, [], {}, None, {}),
            (True, 'name', now, 'desc', [], 'perlnk', {}, {}, [], {}, now, None),
        ]
    )
    def test_deployment_model_creation(self, service_instance_storage, is_valid, name, created_at,
                                       description, inputs, permalink, policy_triggers,
                                       policy_types, outputs, scaling_groups, updated_at,
                                       workflows):
        service_instance = _test_model(
            is_valid=is_valid,
            storage=service_instance_storage,
            model_cls=ServiceInstance,
            model_kwargs=dict(
                name=name,
                service_template=service_instance_storage.service_template.list()[0],
                created_at=created_at,
                description=description,
                inputs=inputs,
                permalink=permalink,
                policy_triggers=policy_triggers,
                policy_types=policy_types,
                outputs=outputs,
                scaling_groups=scaling_groups,
                updated_at=updated_at,
                workflows=workflows
            ))
        if is_valid:
            assert service_instance.service_template == \
                   service_instance_storage.service_template.list()[0]


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
    def test_execution_model_creation(self, service_instance_storage, is_valid, created_at,
                                      started_at, ended_at, error, is_system_workflow, parameters,
                                      status, workflow_name):
        execution = _test_model(
            is_valid=is_valid,
            storage=service_instance_storage,
            model_cls=Execution,
            model_kwargs=dict(
                service_instance=service_instance_storage.service_instance.list()[0],
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
            assert execution.service_instance == service_instance_storage.service_instance.list()[0]
            assert execution.service_template == service_instance_storage.service_template.list()[0]

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


class TestServiceInstanceUpdate(object):
    @pytest.mark.parametrize(
        'is_valid, created_at, deployment_plan, service_instance_update_node_instances, '
        'service_instance_update_service_instance, service_instance_update_nodes, '
        'modified_entity_ids, state',
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
    def test_service_instance_update_model_creation(
            self, service_instance_storage, is_valid, created_at, deployment_plan,
            service_instance_update_node_instances, service_instance_update_service_instance,
            service_instance_update_nodes, modified_entity_ids, state):
        service_instance_update = _test_model(
            is_valid=is_valid,
            storage=service_instance_storage,
            model_cls=ServiceInstanceUpdate,
            model_kwargs=dict(
                service_instance=service_instance_storage.service_instance.list()[0],
                created_at=created_at,
                service_instance_plan=deployment_plan,
                service_instance_update_node_instances=service_instance_update_node_instances,
                service_instance_update_service_instance=service_instance_update_service_instance,
                service_instance_update_nodes=service_instance_update_nodes,
                modified_entity_ids=modified_entity_ids,
                state=state,
            ))
        if is_valid:
            assert service_instance_update.service_instance == \
                   service_instance_storage.service_instance.list()[0]


class TestServiceInstanceUpdateStep(object):

    @pytest.mark.parametrize(
        'is_valid, action, entity_id, entity_type',
        [
            (False, m_cls, 'id', ServiceInstanceUpdateStep.ENTITY_TYPES.NODE),
            (False, ServiceInstanceUpdateStep.ACTION_TYPES.ADD, m_cls,
             ServiceInstanceUpdateStep.ENTITY_TYPES.NODE),
            (False, ServiceInstanceUpdateStep.ACTION_TYPES.ADD, 'id', m_cls),

            (True, ServiceInstanceUpdateStep.ACTION_TYPES.ADD, 'id',
             ServiceInstanceUpdateStep.ENTITY_TYPES.NODE)
        ]
    )
    def test_deployment_update_step_model_creation(self, service_instance_update_storage, is_valid,
                                                   action, entity_id, entity_type):
        service_instance_update_step = _test_model(
            is_valid=is_valid,
            storage=service_instance_update_storage,
            model_cls=ServiceInstanceUpdateStep,
            model_kwargs=dict(
                service_instance_update=
                service_instance_update_storage.service_instance_update.list()[0],
                action=action,
                entity_id=entity_id,
                entity_type=entity_type
            ))
        if is_valid:
            assert service_instance_update_step.service_instance_update == \
                   service_instance_update_storage.service_instance_update.list()[0]

    def test_deployment_update_step_order(self):
        add_node = ServiceInstanceUpdateStep(
            id='add_step',
            action='add',
            entity_type='node',
            entity_id='node_id')

        modify_node = ServiceInstanceUpdateStep(
            id='modify_step',
            action='modify',
            entity_type='node',
            entity_id='node_id')

        remove_node = ServiceInstanceUpdateStep(
            id='remove_step',
            action='remove',
            entity_type='node',
            entity_id='node_id')

        for step in (add_node, modify_node, remove_node):
            assert hash((step.id, step.entity_id)) == hash(step)

        assert remove_node < modify_node < add_node
        assert not remove_node > modify_node > add_node

        add_rel = ServiceInstanceUpdateStep(
            id='add_step',
            action='add',
            entity_type='relationship',
            entity_id='relationship_id')

        remove_rel = ServiceInstanceUpdateStep(
            id='remove_step',
            action='remove',
            entity_type='relationship',
            entity_id='relationship_id')

        assert remove_rel < remove_node < add_node < add_rel
        assert not add_node < None


class TestDeploymentModification(object):
    @pytest.mark.parametrize(
        'is_valid, context, created_at, ended_at, modified_node_templates, nodes, status',
        [
            (False, m_cls, now, now, {}, {}, ServiceInstanceModification.STARTED),
            (False, {}, m_cls, now, {}, {}, ServiceInstanceModification.STARTED),
            (False, {}, now, m_cls, {}, {}, ServiceInstanceModification.STARTED),
            (False, {}, now, now, m_cls, {}, ServiceInstanceModification.STARTED),
            (False, {}, now, now, {}, m_cls, ServiceInstanceModification.STARTED),
            (False, {}, now, now, {}, {}, m_cls),

            (True, {}, now, now, {}, {}, ServiceInstanceModification.STARTED),
            (True, {}, now, None, {}, {}, ServiceInstanceModification.STARTED),
            (True, {}, now, now, None, {}, ServiceInstanceModification.STARTED),
            (True, {}, now, now, {}, None, ServiceInstanceModification.STARTED),
        ]
    )
    def test_deployment_modification_model_creation(
            self, service_instance_storage, is_valid, context, created_at, ended_at,
            modified_node_templates, nodes, status):
        deployment_modification = _test_model(
            is_valid=is_valid,
            storage=service_instance_storage,
            model_cls=ServiceInstanceModification,
            model_kwargs=dict(
                service_instance=service_instance_storage.service_instance.list()[0],
                context=context,
                created_at=created_at,
                ended_at=ended_at,
                modified_nodes=modified_node_templates,
                node_instances=nodes,
                status=status,
            ))
        if is_valid:
            assert deployment_modification.service_instance == \
                   service_instance_storage.service_instance.list()[0]


class TestNodeTemplate(object):
    @pytest.mark.parametrize(
        'is_valid, name, default_instances, max_instances, min_instances, plugins, properties, '
        'type_name, type_hierarchy',
        [
            (False, m_cls, 1, 1, 1, [], [], 'type', []),
            (False, 'name', m_cls, 1, 1, [], [], 'type', []),
            (False, 'name', 1, m_cls, 1, [], [], 'type', []),
            (False, 'name', 1, 1, m_cls, [], [], 'type', []),
            (False, 'name', 1, 1, 1, m_cls, [], 'type', []),
            (False, 'name', 1, 1, 1, [], [], m_cls, []),
            (False, 'name', 1, 1, 1, [], [], 'type', m_cls),
            #
            (True, 'name', 1, 1, 1, [], [], 'type', []),
            (True, 'name', 1, 1, 1, None, [], 'type', []),
            (True, 'name', 1, 1, 1, [], [], 'type', None),
        ]
    )
    def test_node_model_creation(self, service_instance_storage, is_valid, name,
                                 default_instances, max_instances, min_instances, plugins,
                                 properties, type_name, type_hierarchy):
        node_template = _test_model(
            is_valid=is_valid,
            storage=service_instance_storage,
            model_cls=NodeTemplate,
            model_kwargs=dict(
                name=name,
                default_instances=default_instances,
                max_instances=max_instances,
                min_instances=min_instances,
                plugins=plugins,
                properties=properties,
                type_name=type_name,
                type_hierarchy=type_hierarchy,
                service_template=service_instance_storage.service_template.list()[0]
            ))
        if is_valid:
            assert node_template.service_template == \
                   service_instance_storage.service_template.list()[0]


class TestNode(object):
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
    def test_node_instance_model_creation(self, node_template_storage, is_valid, name,
                                          runtime_properties, scaling_groups, state, version):
        node_instance = _test_model(
            is_valid=is_valid,
            storage=node_template_storage,
            model_cls=Node,
            model_kwargs=dict(
                node_template=node_template_storage.node_template.list()[0],
                name=name,
                runtime_properties=runtime_properties,
                scaling_groups=scaling_groups,
                state=state,
                version=version,
                service_instance=node_template_storage.service_instance.list()[0]
            ))
        if is_valid:
            assert node_instance.node_template == node_template_storage.node_template.list()[0]
            assert node_instance.service_instance == \
                   node_template_storage.service_instance.list()[0]


class TestNodeInstanceIP(object):

    ip = '1.1.1.1'

    def test_ip_on_none_hosted_node_instance(self, service_instance_storage):
        node_template = self._node_template(service_instance_storage, ip='not considered')
        node = self._node(service_instance_storage,
                          node_template,
                          is_host=False,
                          ip='not considered')
        assert node.ip is None

    def test_property_ip_on_host_node_instance(self, service_instance_storage):
        node_template = self._node_template(service_instance_storage, ip=self.ip)
        node = self._node(service_instance_storage, node_template, is_host=True, ip=None)
        assert node.ip == self.ip

    def test_runtime_property_ip_on_host_node_instance(self, service_instance_storage):
        node_template = self._node_template(service_instance_storage, ip='not considered')
        node = self._node(service_instance_storage, node_template, is_host=True, ip=self.ip)
        assert node.ip == self.ip

    def test_no_ip_configured_on_host_node_instance(self, service_instance_storage):
        node_template = self._node_template(service_instance_storage, ip=None)
        node = self._node(service_instance_storage, node_template, is_host=True, ip=None)
        assert node.ip is None

    def test_runtime_property_on_hosted_node_instance(self, service_instance_storage):
        host_node_template = self._node_template(service_instance_storage, ip=None)
        host_node = self._node(service_instance_storage,
                               host_node_template,
                               is_host=True,
                               ip=self.ip)
        node_template = self._node_template(service_instance_storage, ip=None)
        node = self._node(service_instance_storage,
                          node_template,
                          is_host=False,
                          ip=None,
                          host_fk=host_node.id)
        assert node.ip == self.ip

    def _node_template(self, storage, ip):
        kwargs = dict(
            name='node_template',
            default_instances=1,
            max_instances=1,
            min_instances=1,
            type_name='',
            service_template=storage.service_template.list()[0]
        )
        if ip:
            kwargs['properties'] = [Parameter(name='ip', type='str', str_value=str(ip))]
        node = NodeTemplate(**kwargs)
        storage.node_template.put(node)
        return node

    def _node(self, storage, node, is_host, ip, host_fk=None):
        kwargs = dict(
            name='node',
            node_template=node,
            runtime_properties={},
            state='',
            service_instance=storage.service_instance.list()[0]
        )
        if ip:
            kwargs['runtime_properties']['ip'] = ip
        if is_host:
            kwargs['host_fk'] = 1
        elif host_fk:
            kwargs['host_fk'] = host_fk
        node_instance = Node(**kwargs)
        storage.node.put(node_instance)
        return node_instance


@pytest.mark.skip('Should be reworked into relationship')
class TestRelationshipInstance(object):
    def test_relatiship_instance_model_creation(self, nodes_storage):
        relationship = mock.models.get_relationship(
            target=nodes_storage.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
        )
        nodes_storage.relationship.put(relationship)
        node_instances = nodes_storage.node
        source_node_instance = node_instances.get_by_name(mock.models.DEPENDENT_NODE_INSTANCE_NAME)
        target_node_instance = node_instances.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)

        relationship_instance = _test_model(
            is_valid=True,
            storage=nodes_storage,
            model_cls=Relationship,
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
                implementation=operation_mapping,
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
                 implementation='',
                 inputs={},
                 max_attempts=max_attempts)
        create_task(max_attempts=1)
        create_task(max_attempts=2)
        create_task(max_attempts=Task.INFINITE_RETRIES)
        with pytest.raises(ValueError):
            create_task(max_attempts=0)
        with pytest.raises(ValueError):
            create_task(max_attempts=-2)
