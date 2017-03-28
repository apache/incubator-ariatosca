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
from aria.orchestrator import decorators
from aria.orchestrator.workflows.builtin.workflows import (
    NORMATIVE_STANDARD_INTERFACE,
    NORMATIVE_CREATE,
    NORMATIVE_START,
    NORMATIVE_STOP,
    NORMATIVE_DELETE,
    NORMATIVE_CONFIGURE,

    NORMATIVE_CONFIGURE_INTERFACE,
    NORMATIVE_PRE_CONFIGURE_SOURCE,
    NORMATIVE_PRE_CONFIGURE_TARGET,
    NORMATIVE_POST_CONFIGURE_SOURCE,
    NORMATIVE_POST_CONFIGURE_TARGET,

    NORMATIVE_ADD_SOURCE,
    NORMATIVE_ADD_TARGET,
    NORMATIVE_REMOVE_TARGET,
    NORMATIVE_REMOVE_SOURCE
)

SERVICE_TEMPLATE_NAME = 'test_service_template'
SERVICE_NAME = 'test_service1'
NODE_TEMPLATE_NAME = 'test_node_template'
NODE_NAME = 'test_node1'
WORKFLOW_NAME = 'test_workflow'
TASK_RETRY_INTERVAL = 1
TASK_MAX_ATTEMPTS = 1

DEPENDENCY_NODE_TEMPLATE_NAME = 'dependency_node_template'
DEPENDENCY_NODE_NAME = 'dependency_node'
DEPENDENT_NODE_TEMPLATE_NAME = 'dependent_node_template'
DEPENDENT_NODE_NAME = 'dependent_node'


def create_service_template(name=SERVICE_TEMPLATE_NAME, description=None, inputs=None):
    now = datetime.now()
    inputs = inputs or {}
    return models.ServiceTemplate(
        name=name,
        description=description,
        inputs=inputs,
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


def create_service(service_template, name=SERVICE_NAME, inputs=None):
    now = datetime.utcnow()
    inputs = inputs or {}
    return models.Service(
        name=name,
        inputs=inputs,
        service_template=service_template,
        description='',
        created_at=now,
        updated_at=now,
        permalink='',
        scaling_groups={},
    )


def create_service_with_dependencies(include_execution=False,
                                     include_input=False,
                                     include_node=False):
    service_template = create_service_template()
    service = create_service(service_template=service_template)
    if include_execution:
        execution = create_execution(service=service, status=models.Execution.STARTED)
        service.executions = [execution]
        execution.id = '1'
    if include_input:
        input = create_parameter(name='input1', value='value1')
        service.inputs = {'input1': input}
    if include_node:
        node_template = create_node_template(service_template=service_template)
        node = create_node(node_template, service, state=models.Node.STARTED)
        node.id = '1'
    return service


def create_node_template_with_dependencies(include_node=False, include_property=False):
    service_template = create_service_template()
    node_template = create_node_template(service_template=service_template)
    if include_node:
        service = create_service(service_template=service_template)
        create_node(dependency_node_template=node_template, service=service)
    if include_property:
        node_template.properties = {'prop1': create_parameter(name='prop1', value='value1')}
    return node_template


def create_node_with_dependencies(include_attribute=False):

    node_template = create_node_template_with_dependencies()
    node_template.service_template.services[0] = create_service(node_template.service_template)
    node = create_node(node_template, node_template.service_template.services[0])
    if include_attribute:
        node.runtime_properties = {'attribute1': 'value1'}
    return node


def create_node_template(service_template,
                         name=NODE_TEMPLATE_NAME,
                         type=models.Type(variant='node', name='test_node_type'),
                         capability_templates=None,
                         requirement_templates=None,
                         interface_templates=None,
                         default_instances=1,
                         min_instances=1,
                         max_instances=1):
    capability_templates = capability_templates or {}
    requirement_templates = requirement_templates or []
    interface_templates = interface_templates or {}
    node_template = models.NodeTemplate(
        name=name,
        type=type,
        capability_templates=capability_templates,
        requirement_templates=requirement_templates,
        interface_templates=interface_templates,
        default_instances=default_instances,
        min_instances=min_instances,
        max_instances=max_instances,
        service_template=service_template)

    service_template.node_templates[node_template.name] = node_template
    return node_template


def create_dependency_node_template(service_template, name=DEPENDENCY_NODE_TEMPLATE_NAME):
    node_type = service_template.node_types.get_descendant('test_node_type')
    capability_type = service_template.capability_types.get_descendant('test_capability_type')

    capability_template = models.CapabilityTemplate(
        name='capability',
        type=capability_type
    )
    return create_node_template(
        service_template=service_template,
        name=name,
        type=node_type,
        capability_templates=_dictify(capability_template)
    )


def create_dependent_node_template(
        service_template, dependency_node_template, name=DEPENDENT_NODE_TEMPLATE_NAME):
    the_type = service_template.node_types.get_descendant('test_node_type')

    requirement_template = models.RequirementTemplate(
        name='requirement',
        target_node_template=dependency_node_template
    )
    return create_node_template(
        service_template=service_template,
        name=name,
        type=the_type,
        interface_templates=_dictify(get_standard_interface_template(service_template)),
        requirement_templates=[requirement_template],
    )


def create_node(dependency_node_template, service, name=NODE_NAME, state=models.Node.INITIAL,
                runtime_properties=None):
    runtime_properties = runtime_properties or {}
    node = models.Node(
        name=name,
        type=dependency_node_template.type,
        runtime_properties=runtime_properties,
        version=None,
        node_template=dependency_node_template,
        state=state,
        scaling_groups=[],
        service=service,
        interfaces=get_standard_interface(service),
    )
    service.nodes[node.name] = node
    return node


def create_relationship(source, target):
    return models.Relationship(
        source_node=source,
        target_node=target,
        interfaces=get_configure_interfaces(service=source.service),
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

    if operation_kwargs and operation_kwargs.get('inputs'):
        operation_kwargs['inputs'] = dict(
            (input_name, models.Parameter.wrap(input_name, input_value))
            for input_name, input_value in operation_kwargs['inputs'].iteritems()
            if input_value is not None)

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


def create_execution(service, status=models.Execution.PENDING):
    return models.Execution(
        service=service,
        status=status,
        workflow_name=WORKFLOW_NAME,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        inputs={}
    )


def create_plugin(name='test_plugin', package_version='0.1'):
    return models.Plugin(
        name=name,
        archive_name='archive_name',
        distribution='distribution',
        distribution_release='dist_release',
        distribution_version='dist_version',
        package_name='package',
        package_source='source',
        package_version=package_version,
        supported_platform='any',
        supported_py_versions=['python27'],
        uploaded_at=datetime.now(),
        wheels=[],
    )


def create_plugin_specification(name='test_plugin', version='0.1'):
    return models.PluginSpecification(
        name=name,
        version=version
    )


def create_parameter(name, value):
    p = models.Parameter()
    return p.wrap(name, value)


def _dictify(item):
    return dict(((item.name, item),))


def get_standard_interface_template(service_template):
    the_type = service_template.interface_types.get_descendant('test_interface_type')

    op_templates = dict(
        (op_name, models.OperationTemplate(
            name=op_name, implementation='{0}.{1}'.format(__file__, mock_operation.__name__)))
        for op_name in [NORMATIVE_CREATE, NORMATIVE_CONFIGURE, NORMATIVE_START,
                        NORMATIVE_STOP, NORMATIVE_DELETE]
    )
    return models.InterfaceTemplate(name=NORMATIVE_STANDARD_INTERFACE,
                                    operation_templates=op_templates,
                                    type=the_type)


def get_standard_interface(service):
    the_type = service.service_template.interface_types.get_descendant('test_interface_type')

    ops = dict(
        (op_name, models.Operation(
            name=op_name, implementation='{0}.{1}'.format(__file__, mock_operation.__name__)))
        for op_name in [NORMATIVE_CREATE, NORMATIVE_CONFIGURE, NORMATIVE_START,
                        NORMATIVE_STOP, NORMATIVE_DELETE]
    )
    return {
        NORMATIVE_STANDARD_INTERFACE:
            models.Interface(name=NORMATIVE_STANDARD_INTERFACE, operations=ops, type=the_type)
    }


def get_configure_interfaces(service):
    the_type = service.service_template.interface_types.get_descendant('test_interface_type')

    operations = dict(
        (op_name, models.Operation(
            name=op_name, implementation='{0}.{1}'.format(__file__, mock_operation.__name__)))
        for op_name in [NORMATIVE_PRE_CONFIGURE_SOURCE,
                        NORMATIVE_POST_CONFIGURE_SOURCE,
                        NORMATIVE_ADD_SOURCE,
                        NORMATIVE_REMOVE_SOURCE,

                        NORMATIVE_PRE_CONFIGURE_TARGET,
                        NORMATIVE_POST_CONFIGURE_TARGET,
                        NORMATIVE_ADD_TARGET,
                        NORMATIVE_REMOVE_TARGET
                       ]
    )
    interface = {
        NORMATIVE_CONFIGURE_INTERFACE: models.Interface(
            name=NORMATIVE_CONFIGURE_INTERFACE, operations=operations, type=the_type)
    }

    return interface


@decorators.operation
def mock_operation(*args, **kwargs):
    pass
