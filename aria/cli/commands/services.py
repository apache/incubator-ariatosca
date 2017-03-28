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


import os
from StringIO import StringIO

from . import service_templates
from .. import helptexts
from .. import table
from .. import utils
from ..core import aria
from ...core import Core
from ...modeling import exceptions as modeling_exceptions
from ...storage import exceptions as storage_exceptions


SERVICE_COLUMNS = ['id', 'name', 'service_template_name', 'created_at', 'updated_at']


@aria.group(name='services')
@aria.options.verbose()
def services():
    """Handle services
    """
    pass


@services.command(name='list', short_help='List services')
@aria.options.service_template_name()
@aria.options.sort_by()
@aria.options.descending
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def list(service_template_name,
         sort_by,
         descending,
         model_storage,
         logger):
    """List services

    If `--service-template-name` is provided, list services for that service template.
    Otherwise, list services for all service templates.
    """
    if service_template_name:
        logger.info('Listing services for service template {0}...'.format(
            service_template_name))
        service_template = model_storage.service_template.get_by_name(service_template_name)
        filters = dict(service_template=service_template)
    else:
        logger.info('Listing all services...')
        filters = {}

    services_list = model_storage.service.list(
        sort=utils.storage_sort_param(sort_by=sort_by, descending=descending),
        filters=filters)
    table.print_data(SERVICE_COLUMNS, services_list, 'Services:')


@services.command(name='create',
                  short_help='Create a services')
@aria.argument('service-name', required=False)
@aria.options.service_template_name(required=True)
@aria.options.inputs(help=helptexts.SERVICE_INPUTS)
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def create(service_template_name,
           service_name,
           inputs,  # pylint: disable=redefined-outer-name
           model_storage,
           resource_storage,
           plugin_manager,
           logger):
    """Create a service

    `SERVICE_NAME` is the name of the service you'd like to create.

    """
    logger.info('Creating new service from service template {0}...'.format(
        service_template_name))
    core = Core(model_storage, resource_storage, plugin_manager)
    service_template = model_storage.service_template.get_by_name(service_template_name)

    try:
        service = core.create_service(service_template.id, inputs, service_name)
    except storage_exceptions.StorageError as e:
        utils.check_overriding_storage_exceptions(e, 'service', service_name)
        raise
    except modeling_exceptions.InputsException:
        service_templates.print_service_template_inputs(model_storage, service_template_name,
                                                        logger)
        raise
    logger.info("Service created. The service's name is {0}".format(service.name))


@services.command(name='delete',
                  short_help='Delete a service')
@aria.argument('service-name')
@aria.options.force(help=helptexts.IGNORE_AVAILABLE_NODES)
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def delete(service_name, force, model_storage, resource_storage, plugin_manager, logger):
    """Delete a service

    `SERVICE_NAME` is the name of the service to delete.
    """
    logger.info('Deleting service {0}...'.format(service_name))
    service = model_storage.service.get_by_name(service_name)
    core = Core(model_storage, resource_storage, plugin_manager)
    core.delete_service(service.id, force=force)
    logger.info('Service {0} deleted'.format(service_name))


@services.command(name='outputs',
                  short_help='Show service outputs')
@aria.argument('service-name')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def outputs(service_name, model_storage, logger):
    """Show outputs for a specific service

    `SERVICE_NAME` is the name of the service to print outputs for.
    """
    logger.info('Showing outputs for service {0}...'.format(service_name))
    service = model_storage.service.get_by_name(service_name)
    #TODO fix this section..
    outputs_def = service.outputs
    response = model_storage.service.outputs.get(service_name)
    outputs_ = StringIO()
    for output_name, output in response.outputs.iteritems():
        outputs_.write(' - "{0}":{1}'.format(output_name, os.linesep))
        description = outputs_def[output_name].get('description', '')
        outputs_.write('     Description: {0}{1}'.format(description,
                                                         os.linesep))
        outputs_.write('     Value: {0}{1}'.format(output, os.linesep))
    logger.info(outputs_.getvalue())


@services.command(name='inputs',
                  short_help='Show service inputs')
@aria.argument('service-name')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def inputs(service_name, model_storage, logger):
    """Show inputs for a specific service

    `SERVICE_NAME` is the id of the service to print inputs for.
    """
    logger.info('Showing inputs for service {0}...'.format(service_name))
    service = model_storage.service.get_by_name(service_name)
    if service.inputs:
        inputs_string = StringIO()
        for input_name, input_ in service.inputs.iteritems():
            inputs_string.write(' - "{0}":{1}'.format(input_name, os.linesep))
            inputs_string.write('     Value: {0}{1}'.format(input_.value, os.linesep))
        logger.info(inputs_string.getvalue())
    else:
        logger.info('\tNo inputs')
