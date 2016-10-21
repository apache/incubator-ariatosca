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


def get_dependency_node():
    return models.Node(
        id='dependency_node',
        host_id='dependency_node',
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
        id='dependency_node_instance',
        host_id='dependency_node_instance',
        deployment_id=DEPLOYMENT_ID,
        runtime_properties={},
        version=None,
        relationship_instances=[],
        node=dependency_node or get_dependency_node()
    )


def get_relationship(target=None):
    return models.Relationship(
        target_id=target.id or get_dependency_node().id,
        source_interfaces={},
        source_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        target_interfaces={},
        target_operations=dict((key, {}) for key in operations.RELATIONSHIP_OPERATIONS),
        type='rel_type',
        type_hierarchy=[],
        properties={},
    )


def get_relationship_instance(target_instance=None, relationship=None):
    return models.RelationshipInstance(
        target_id=target_instance.id or get_dependency_node_instance().id,
        target_name='test_target_name',
        type='some_type',
        relationship=relationship or get_relationship(target_instance.node
                                                      if target_instance else None)
    )


def get_dependent_node(relationship=None):
    return models.Node(
        id='dependent_node',
        host_id='dependent_node',
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


def get_dependent_node_instance(relationship_instance, dependent_node=None):
    return models.NodeInstance(
        id='dependent_node_instance',
        host_id='dependent_node_instance',
        deployment_id=DEPLOYMENT_ID,
        runtime_properties={},
        version=None,
        relationship_instances=[relationship_instance or get_relationship_instance()],
        node=dependent_node or get_dependency_node()
    )


def get_execution():
    return models.Execution(
        id=EXECUTION_ID,
        status=models.Execution.STARTED,
        deployment_id=DEPLOYMENT_ID,
        workflow_id=WORKFLOW_ID,
        blueprint_id=BLUEPRINT_ID,
        started_at=datetime.now(),
        parameters=None
    )


def get_deployment():
    now = datetime.now()
    return models.Deployment(
        id=DEPLOYMENT_ID,
        description=None,
        created_at=now,
        updated_at=now,
        blueprint_id=BLUEPRINT_ID,
        workflows={}
    )
