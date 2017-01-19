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

"""
Convenience storage related tools.
# TODO rename module name
"""

import json
import os
import shutil
import tarfile
import tempfile
from datetime import datetime

from aria.storage.exceptions import StorageError
from aria.logger import LoggerMixin


class StorageManager(LoggerMixin):
    """
    Convenience wrapper to simplify work with the lower level storage mechanism
    """

    def __init__(
            self,
            model_storage,
            resource_storage,
            blueprint_path,
            blueprint_id,
            blueprint_plan,
            deployment_id,
            deployment_plan,
            **kwargs):
        super(StorageManager, self).__init__(**kwargs)
        self.model_storage = model_storage
        self.resource_storage = resource_storage
        self.blueprint_path = blueprint_path
        self.blueprint_id = blueprint_id
        self.blueprint_plan = blueprint_plan
        self.deployment_id = deployment_id
        self.deployment_plan = deployment_plan

    @classmethod
    def from_deployment(
            cls,
            model_storage,
            resource_storage,
            deployment_id,
            deployment_plan):
        """
        Create a StorageManager from a deployment
        """
        return cls(
            model_storage=model_storage,
            resource_storage=resource_storage,
            deployment_id=deployment_id,
            deployment_plan=deployment_plan,
            blueprint_path=None,
            blueprint_plan=None,
            blueprint_id=None
        )

    @classmethod
    def from_blueprint(
            cls,
            model_storage,
            resource_storage,
            blueprint_path,
            blueprint_id,
            blueprint_plan):
        """
        Create a StorageManager from a blueprint
        """
        return cls(
            model_storage=model_storage,
            resource_storage=resource_storage,
            blueprint_path=blueprint_path,
            blueprint_plan=blueprint_plan,
            blueprint_id=blueprint_id,
            deployment_id=None,
            deployment_plan=None)

    def create_blueprint_storage(self, source, main_file_name=None):
        """
        create blueprint model & resource
        """
        assert self.blueprint_path and self.blueprint_id
        assert hasattr(self.resource_storage, 'blueprint')
        assert hasattr(self.model_storage, 'blueprint')

        self.logger.debug('creating blueprint resource storage entry')
        self.resource_storage.service_template.upload(
            entry_id=self.blueprint_id,
            source=os.path.dirname(source))
        self.logger.debug('created blueprint resource storage entry')

        self.logger.debug('creating blueprint model storage entry')
        now = datetime.utcnow()
        blueprint = self.model_storage.service_template.model_cls(
            plan=self.blueprint_plan,
            id=self.blueprint_id,
            description=self.blueprint_plan.get('description'),
            created_at=now,
            updated_at=now,
            main_file_name=main_file_name,
        )
        self.model_storage.service_template.put(blueprint)
        self.logger.debug('created blueprint model storage entry')

    def create_nodes_storage(self):
        """
        create nodes model
        """
        assert self.blueprint_path and self.blueprint_id
        assert hasattr(self.model_storage, 'node')
        assert hasattr(self.model_storage, 'relationship')

        for node in self.blueprint_plan['nodes']:
            node_copy = node.copy()
            for field in ('name',
                          'deployment_plugins_to_install',
                          'interfaces',
                          'instances'):
                node_copy.pop(field)
            scalable = node_copy.pop('capabilities')['scalable']['properties']
            for index, relationship in enumerate(node_copy['relationships']):
                relationship = self.model_storage.relationship.model_cls(**relationship)
                self.model_storage.relationship.put(relationship)
                node_copy['relationships'][index] = relationship

            node_copy = self.model_storage.node.model_cls(
                blueprint_id=self.blueprint_id,
                planned_number_of_instances=scalable['current_instances'],
                deploy_number_of_instances=scalable['default_instances'],
                min_number_of_instances=scalable['min_instances'],
                max_number_of_instances=scalable['max_instances'],
                number_of_instances=scalable['current_instances'],
                **node_copy)
            self.model_storage.node.put(node_copy)

    def create_deployment_storage(self):
        """
        create deployment model & resource
        """
        assert self.deployment_id and self.deployment_plan

        assert hasattr(self.resource_storage, 'blueprint')
        assert hasattr(self.resource_storage, 'deployment')
        assert hasattr(self.model_storage, 'deployment')

        self.logger.debug('creating deployment resource storage entry')
        temp_dir = tempfile.mkdtemp()
        try:
            self.resource_storage.service_template.download(
                entry_id=self.blueprint_id,
                destination=temp_dir)
            self.resource_storage.service_instance.upload(
                entry_id=self.deployment_id,
                source=temp_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        self.logger.debug('created deployment resource storage entry')

        self.logger.debug('creating deployment model storage entry')
        now = datetime.utcnow()
        deployment = self.model_storage.service_instance.model_cls(
            id=self.deployment_id,
            blueprint_id=self.blueprint_id,
            description=self.deployment_plan['description'],
            workflows=self.deployment_plan['workflows'],
            inputs=self.deployment_plan['inputs'],
            policy_types=self.deployment_plan['policy_types'],
            policy_triggers=self.deployment_plan['policy_triggers'],
            groups=self.deployment_plan['groups'],
            scaling_groups=self.deployment_plan['scaling_groups'],
            outputs=self.deployment_plan['outputs'],
            created_at=now,
            updated_at=now
        )
        self.model_storage.service_instance.put(deployment)
        self.logger.debug('created deployment model storage entry')

    def create_node_instances_storage(self):
        """
        create node_instances model
        """
        assert self.deployment_id and self.deployment_plan
        assert hasattr(self.model_storage, 'node_instance')
        assert hasattr(self.model_storage, 'relationship_instance')

        self.logger.debug('creating node-instances model storage entries')
        for node_instance in self.deployment_plan['node_instances']:
            node_model = self.model_storage.node.get(node_instance['node_id'])
            relationship_instances = []

            for index, relationship_instance in enumerate(node_instance['relationships']):
                relationship_instance_model = self.model_storage.relationship.model_cls(
                    relationship=node_model.relationships[index],
                    target_name=relationship_instance['target_name'],
                    type=relationship_instance['type'],
                    target_id=relationship_instance['target_id'])
                relationship_instances.append(relationship_instance_model)
                self.model_storage.relationship.put(relationship_instance_model)

            node_instance_model = self.model_storage.node.model_cls(
                node=node_model,
                id=node_instance['id'],
                runtime_properties={},
                state=self.model_storage.node.model_cls.UNINITIALIZED,
                deployment_id=self.deployment_id,
                version='1.0',
                relationship_instances=relationship_instances)

            self.model_storage.node.put(node_instance_model)
        self.logger.debug('created node-instances model storage entries')

    def create_plugin_storage(self, plugin_id, source):
        """
        create plugin model & resource
        """
        assert hasattr(self.model_storage, 'plugin')
        assert hasattr(self.resource_storage, 'plugin')

        self.logger.debug('creating plugin resource storage entry')
        self.resource_storage.plugin.upload(entry_id=plugin_id, source=source)
        self.logger.debug('created plugin resource storage entry')

        self.logger.debug('creating plugin model storage entry')
        plugin = _load_plugin_from_archive(source)
        build_props = plugin.get('build_server_os_properties')
        now = datetime.utcnow()

        plugin = self.model_storage.plugin.model_cls(
            id=plugin_id,
            package_name=plugin.get('package_name'),
            package_version=plugin.get('package_version'),
            archive_name=plugin.get('archive_name'),
            package_source=plugin.get('package_source'),
            supported_platform=plugin.get('supported_platform'),
            distribution=build_props.get('distribution'),
            distribution_version=build_props.get('distribution_version'),
            distribution_release=build_props.get('distribution_release'),
            wheels=plugin.get('wheels'),
            excluded_wheels=plugin.get('excluded_wheels'),
            supported_py_versions=plugin.get('supported_python_versions'),
            uploaded_at=now
        )
        self.model_storage.plugin.put(plugin)
        self.logger.debug('created plugin model storage entry')


def _load_plugin_from_archive(tar_source):
    if not tarfile.is_tarfile(tar_source):
        # TODO: go over the exceptions
        raise StorageError(
            'the provided tar archive can not be read.')

    with tarfile.open(tar_source) as tar:
        tar_members = tar.getmembers()
        # a wheel plugin will contain exactly one sub directory
        if not tar_members:
            raise StorageError(
                'archive file structure malformed. expecting exactly one '
                'sub directory; got none.')
        package_json_path = os.path.join(tar_members[0].name,
                                         'package.json')
        try:
            package_member = tar.getmember(package_json_path)
        except KeyError:
            raise StorageError("'package.json' was not found under {0}"
                               .format(package_json_path))
        try:
            package_json = tar.extractfile(package_member)
        except tarfile.ExtractError as e:
            raise StorageError(str(e))
        try:
            return json.load(package_json)
        except ValueError as e:
            raise StorageError("'package.json' is not a valid json: "
                               "{json_str}. error is {error}"
                               .format(json_str=package_json.read(), error=str(e)))
