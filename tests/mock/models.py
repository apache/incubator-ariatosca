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

from aria.storage import models

from . import operations

DEPLOYMENT_NAME = 'test_deployment_id'
BLUEPRINT_NAME = 'test_blueprint_id'
WORKFLOW_NAME = 'test_workflow_id'
EXECUTION_NAME = 'test_execution_id'
TASK_RETRY_INTERVAL = 1
TASK_MAX_ATTEMPTS = 1

DEPENDENCY_NODE_NAME = 'dependency_node'
DEPENDENCY_NODE_INSTANCE_NAME = 'dependency_node_instance'
DEPENDENT_NODE_NAME = 'dependent_node'
DEPENDENT_NODE_INSTANCE_NAME = 'dependent_node_instance'
RELATIONSHIP_NAME = 'relationship'
RELATIONSHIP_INSTANCE_NAME = 'relationship_instance'


def get_dependency_node(deployment):
    return models.Node(
        name=DEPENDENCY_NODE_NAME,
        type='test_node_type',
        type_hierarchy=[],
        number_of_instances=1,
        planned_number_of_instances=1,
        deploy_number_of_instances=1,
        properties={},
        operations=dict((key, {}) for key in operations.NODE_OPERATIONS),
        min_number_of_instances=1,
        max_number_of_instances=1,
        deployment_id=deployment.id
    )


def get_dependency_node_instance(dependency_node):
    return models.NodeInstance(
        name=DEPENDENCY_NODE_INSTANCE_NAME,
        runtime_properties={'ip': '1.1.1.1'},
        version=None,
        node_id=dependency_node.id,
        deployment_id=dependency_node.deployment.id,
        state='',
        scaling_groups={}
    )


def get_relationship(source=None, target=None):
    return models.Relationship(
        source_node_id=source.id,
        target_node_id=target.id,
        source_interfaces={},
        source_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        target_interfaces={},
        target_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        type='rel_type',
        type_hierarchy=[],
        properties={},
    )


def get_relationship_instance(source_instance, target_instance, relationship):
    return models.RelationshipInstance(
        relationship_id=relationship.id,
        target_node_instance_id=target_instance.id,
        source_node_instance_id=source_instance.id,
    )


def get_dependent_node(deployment):
    return models.Node(
        name=DEPENDENT_NODE_NAME,
        deployment_id=deployment.id,
        type='test_node_type',
        type_hierarchy=[],
        number_of_instances=1,
        planned_number_of_instances=1,
        deploy_number_of_instances=1,
        properties={},
        operations=dict((key, {}) for key in operations.NODE_OPERATIONS),
        min_number_of_instances=1,
        max_number_of_instances=1,
    )


def get_dependent_node_instance(dependent_node):
    return models.NodeInstance(
        name=DEPENDENT_NODE_INSTANCE_NAME,
        runtime_properties={},
        version=None,
        node_id=dependent_node.id,
        deployment_id=dependent_node.deployment.id,
        state='',
        scaling_groups={}
    )


def get_blueprint():
    now = datetime.now()
    return models.Blueprint(
        plan={},
        name=BLUEPRINT_NAME,
        description=None,
        created_at=now,
        updated_at=now,
        main_file_name='main_file_name'
    )


def get_execution(deployment):
    return models.Execution(
        deployment_id=deployment.id,
        blueprint_id=deployment.blueprint.id,
        status=models.Execution.STARTED,
        workflow_name=WORKFLOW_NAME,
        started_at=datetime.utcnow(),
        parameters=None
    )


def get_deployment(blueprint):
    now = datetime.utcnow()
    return models.Deployment(
        name=DEPLOYMENT_NAME,
        blueprint_id=blueprint.id,
        description='',
        created_at=now,
        updated_at=now,
        workflows={},
        inputs={},
        groups={},
        permalink='',
        policy_triggers={},
        policy_types={},
        outputs={},
        scaling_groups={},
    )


def get_plugin(package_name='package', package_version='0.1'):
    return models.Plugin(
        archive_name='archive_name',
        distribution='distribution',
        distribution_release='dist_release',
        distribution_version='dist_version',
        package_name=package_name,
        package_source='source',
        package_version=package_version,
        supported_platform='any',
        supported_py_versions=['python27'],
        uploaded_at=datetime.now(),
        wheels=[],
    )
