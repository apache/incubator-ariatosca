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

from aria.modeling import models
from . import operations

SERVICE_NAME = 'test_service_name'
SERVICE_TEMPLATE_NAME = 'test_service_template_name'
WORKFLOW_NAME = 'test_workflow_name'
EXECUTION_NAME = 'test_execution_name'
TASK_RETRY_INTERVAL = 1
TASK_MAX_ATTEMPTS = 1

DEPENDENCY_NODE_TEMPLATE_NAME = 'dependency_node_template'
DEPENDENCY_NODE_NAME = 'dependency_node'
DEPENDENT_NODE_TEMPLATE_NAME = 'dependent_node_template'
DEPENDENT_NODE_NAME = 'dependent_node'


def create_service_template():
    now = datetime.now()
    return models.ServiceTemplate(
        name=SERVICE_TEMPLATE_NAME,
        description=None,
        created_at=now,
        updated_at=now,
        main_file_name='main_file_name',
        node_types=models.Type(variant='node', name='test_node_type'),
        group_types=models.Type(variant='group', name='test_group_type'),
        policy_types=models.Type(variant='policy', name='test_policy_type'),
        relationship_types=models.Type(variant='relationship', name='test_relationship_type'),
        capability_types=models.Type(variant='capability', name='test_capability_type'),
        artifact_types=models.Type(variant='artifact', name='test_artifact_type'),
        interface_types=models.Type(variant='interface', name='test_interface_type')
    )


def create_service(service_template):
    now = datetime.utcnow()
    return models.Service(
        name=SERVICE_NAME,
        service_template=service_template,
        description='',
        created_at=now,
        updated_at=now,
        permalink='',
        scaling_groups={},
    )


def create_dependency_node_template(service_template):
    node_type = service_template.node_types.get_descendant('test_node_type')
    capability_type = service_template.capability_types.get_descendant('test_capability_type')

    capability_template = models.CapabilityTemplate(
        name='capability',
        type=capability_type
    )

    node_template = models.NodeTemplate(
        name=DEPENDENCY_NODE_TEMPLATE_NAME,
        type=node_type,
        capability_templates=_dictify(capability_template),
        default_instances=1,
        min_instances=1,
        max_instances=1,
        service_template=service_template
    )
    service_template.node_templates[node_template.name] = node_template
    return node_template


def create_dependent_node_template(service_template, dependency_node_template):
    the_type = service_template.node_types.get_descendant('test_node_type')

    operation_templates = dict((op, models.OperationTemplate(
        name=op,
        implementation='test'))
                               for _, op in operations.NODE_OPERATIONS)
    interface_template = models.InterfaceTemplate(
        type=service_template.interface_types.get_descendant('test_interface_type'),
        operation_templates=operation_templates)

    requirement_template = models.RequirementTemplate(
        name='requirement',
        target_node_template=dependency_node_template
    )

    node_template = models.NodeTemplate(
        name=DEPENDENT_NODE_TEMPLATE_NAME,
        type=the_type,
        default_instances=1,
        min_instances=1,
        max_instances=1,
        interface_templates=_dictify(interface_template),
        requirement_templates=[requirement_template],
        service_template=service_template
    )
    service_template.node_templates[node_template.name] = node_template
    return node_template


def create_dependency_node(dependency_node_template, service):
    node = models.Node(
        name=DEPENDENCY_NODE_NAME,
        type=dependency_node_template.type,
        runtime_properties={'ip': '1.1.1.1'},
        version=None,
        node_template=dependency_node_template,
        state='',
        scaling_groups=[],
        service=service
    )
    service.nodes[node.name] = node
    return node


def create_dependent_node(dependent_node_template, service):
    node = models.Node(
        name=DEPENDENT_NODE_NAME,
        type=dependent_node_template.type,
        runtime_properties={},
        version=None,
        node_template=dependent_node_template,
        state='',
        scaling_groups=[],
        service=service
    )
    service.nodes[node.name] = node
    return node


def create_relationship(source, target):
    return models.Relationship(
        source_node=source,
        target_node=target
    )


def create_interface_template(service_template, interface_name, operation_name,
                              operation_kwargs=None, interface_kwargs=None):
    the_type = service_template.interface_types.get_descendant('test_interface_type')
    operation_template = models.OperationTemplate(
        name=operation_name,
        **(operation_kwargs or {})
    )
    return models.InterfaceTemplate(
        type=the_type,
        operation_templates=_dictify(operation_template),
        name=interface_name,
        **(interface_kwargs or {})
    )


def create_interface(service, interface_name, operation_name, operation_kwargs=None,
                     interface_kwargs=None):
    the_type = service.service_template.interface_types.get_descendant('test_interface_type')
    operation = models.Operation(
        name=operation_name,
        **(operation_kwargs or {})
    )
    return models.Interface(
        type=the_type,
        operations=_dictify(operation),
        name=interface_name,
        **(interface_kwargs or {})
    )


def create_execution(service):
    return models.Execution(
        service=service,
        status=models.Execution.STARTED,
        workflow_name=WORKFLOW_NAME,
        started_at=datetime.utcnow(),
        parameters=None
    )


def create_plugin(package_name='package', package_version='0.1'):
    return models.Plugin(
        name='test_plugin',
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


def create_plugin_specification(package_name='package', package_version='0.1'):
    return models.PluginSpecification(
        name='test_plugin',
        archive_name='archive_name',
        distribution='distribution',
        distribution_release='dist_release',
        distribution_version='dist_version',
        package_name=package_name,
        package_source='source',
        package_version=package_version,
        supported_platform='any',
        supported_py_versions=['python27']
    )


def _dictify(item):
    return dict(((item.name, item),))
