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

DEPLOYMENT_ID = 'test_deployment_id'
BLUEPRINT_ID = 'test_blueprint_id'
WORKFLOW_ID = 'test_workflow_id'
EXECUTION_ID = 'test_execution_id'
TASK_RETRY_INTERVAL = 1
TASK_MAX_ATTEMPTS = 1

DEPENDENCY_NODE_ID = 'dependency_node'
DEPENDENCY_NODE_INSTANCE_ID = 'dependency_node_instance'
DEPENDENT_NODE_ID = 'dependent_node'
DEPENDENT_NODE_INSTANCE_ID = 'dependent_node_instance'


def get_dependency_node():
    return models.Node(
        id=DEPENDENCY_NODE_ID,
        host_id=DEPENDENCY_NODE_ID,
        blueprint_id=BLUEPRINT_ID,
        type='test_node_type',
        type_hierarchy=[],
        number_of_instances=1,
        planned_number_of_instances=1,
        deploy_number_of_instances=1,
        properties={},
        operations=dict((key, {}) for key in operations.NODE_OPERATIONS),
        relationships=[],
        min_number_of_instances=1,
        max_number_of_instances=1,
    )


def get_dependency_node_instance(dependency_node=None):
    return models.NodeInstance(
        id=DEPENDENCY_NODE_INSTANCE_ID,
        host_id=DEPENDENCY_NODE_INSTANCE_ID,
        deployment_id=DEPLOYMENT_ID,
        runtime_properties={'ip': '1.1.1.1'},
        version=None,
        relationship_instances=[],
        node=dependency_node or get_dependency_node()
    )


def get_relationship(source=None, target=None):
    return models.Relationship(
        source_id=source.id if source is not None else DEPENDENT_NODE_ID,
        target_id=target.id if target is not None else DEPENDENCY_NODE_ID,
        source_interfaces={},
        source_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        target_interfaces={},
        target_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        type='rel_type',
        type_hierarchy=[],
        properties={},
    )


def get_relationship_instance(source_instance=None, target_instance=None, relationship=None):
    return models.RelationshipInstance(
        target_id=target_instance.id if target_instance else DEPENDENCY_NODE_INSTANCE_ID,
        target_name='test_target_name',
        source_id=source_instance.id if source_instance else DEPENDENT_NODE_INSTANCE_ID,
        source_name='test_source_name',
        type='some_type',
        relationship=relationship or get_relationship(target_instance.node
                                                      if target_instance else None)
    )


def get_dependent_node(relationship=None):
    return models.Node(
        id=DEPENDENT_NODE_ID,
        host_id=DEPENDENT_NODE_ID,
        blueprint_id=BLUEPRINT_ID,
        type='test_node_type',
        type_hierarchy=[],
        number_of_instances=1,
        planned_number_of_instances=1,
        deploy_number_of_instances=1,
        properties={},
        operations=dict((key, {}) for key in operations.NODE_OPERATIONS),
        relationships=[relationship or get_relationship()],
        min_number_of_instances=1,
        max_number_of_instances=1,
    )


def get_dependent_node_instance(relationship_instance=None, dependent_node=None):
    return models.NodeInstance(
        id=DEPENDENT_NODE_INSTANCE_ID,
        host_id=DEPENDENT_NODE_INSTANCE_ID,
        deployment_id=DEPLOYMENT_ID,
        runtime_properties={},
        version=None,
        relationship_instances=[relationship_instance or get_relationship_instance()],
        node=dependent_node or get_dependency_node()
    )


def get_blueprint():
    now = datetime.now()
    return models.Blueprint(
        plan={},
        id=BLUEPRINT_ID,
        description=None,
        created_at=now,
        updated_at=now,
        main_file_name='main_file_name'
    )


def get_execution():
    return models.Execution(
        id=EXECUTION_ID,
        status=models.Execution.STARTED,
        deployment_id=DEPLOYMENT_ID,
        workflow_id=WORKFLOW_ID,
        blueprint_id=BLUEPRINT_ID,
        started_at=datetime.utcnow(),
        parameters=None
    )


def get_deployment():
    now = datetime.utcnow()
    return models.Deployment(
        id=DEPLOYMENT_ID,
        description=None,
        created_at=now,
        updated_at=now,
        blueprint_id=BLUEPRINT_ID,
        workflows={}
    )
