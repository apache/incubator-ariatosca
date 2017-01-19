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

from aria.storage.modeling import model
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
    return model.NodeTemplate(
        name=DEPENDENCY_NODE_NAME,
        type_name='test_node_type',
        type_hierarchy=[],
        default_instances=1,
        min_instances=1,
        max_instances=1,
        service_template=deployment.service_template,
    )


def get_dependency_node_instance(dependency_node, deployment):
    return model.Node(
        name=DEPENDENCY_NODE_INSTANCE_NAME,
        service_instance=deployment,
        runtime_properties={'ip': '1.1.1.1'},
        version=None,
        node_template=dependency_node,
        state='',
        scaling_groups=[]
    )


def get_relationship(target):
    requirement_template = model.RequirementTemplate(target_node_template_name=target.name)
    capability_template = model.CapabilityTemplate()

    return requirement_template, capability_template


def get_relationship_instance(source_instance, target_instance):
    return model.Relationship(
        target_node=target_instance,
        source_node=source_instance,
    )


def get_dependent_node(deployment, requirement_template, capability_template):
    operation_templates = [model.OperationTemplate(implementation=op,
                                                   service_template=deployment.service_template)
                           for op in operations.NODE_OPERATIONS]
    interface_template = model.InterfaceTemplate(operation_templates=operation_templates)

    return model.NodeTemplate(
        name=DEPENDENT_NODE_NAME,
        type_name='test_node_type',
        type_hierarchy=[],
        default_instances=1,
        min_instances=1,
        max_instances=1,
        service_template=deployment.service_template,
        interface_templates=[interface_template],
        requirement_templates=[requirement_template],
        capability_templates=[capability_template],
    )


def get_dependent_node_instance(dependent_node, deployment):
    return model.Node(
        name=DEPENDENT_NODE_INSTANCE_NAME,
        service_instance=deployment,
        runtime_properties={},
        version=None,
        node_template=dependent_node,
        state='',
        scaling_groups=[],
    )


def get_blueprint():
    now = datetime.now()
    return model.ServiceTemplate(
        plan={},
        name=BLUEPRINT_NAME,
        description=None,
        created_at=now,
        updated_at=now,
        main_file_name='main_file_name'
    )


def get_execution(deployment):
    return model.Execution(
        service_instance=deployment,
        status=model.Execution.STARTED,
        workflow_name=WORKFLOW_NAME,
        started_at=datetime.utcnow(),
        parameters=None
    )


def get_deployment(blueprint):
    now = datetime.utcnow()
    return model.ServiceInstance(
        name=DEPLOYMENT_NAME,
        service_template=blueprint,
        description='',
        created_at=now,
        updated_at=now,
        workflows={},
        permalink='',
        policy_triggers={},
        policy_types={},
        scaling_groups={},
    )


def get_plugin(package_name='package', package_version='0.1'):
    return model.Plugin(
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


def get_interface_template(operation_name, operation_kwargs=None, interface_kwargs=None):
    operation_template = model.OperationTemplate(
        name=operation_name,
        **(operation_kwargs or {})

    )
    return model.InterfaceTemplate(
        operation_templates=[operation_template],
        name=operation_name.rsplit('.', 1)[0],
        **(interface_kwargs or {})
    )


def get_interface(operation_name,
                  operation_kwargs=None,
                  interface_kwargs=None,
                  edge=None):
    operation = model.Operation(name=operation_name, **(operation_kwargs or {}))
    interface_name = operation_name.rsplit('.', 1)[0]
    return model.Interface(operations=[operation],
                           name=interface_name,
                           edge=edge,
                           **(interface_kwargs or {}))
