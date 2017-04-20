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

from .. import csar
from .. import service_template_utils
from .. import table
from .. import utils
from ..core import aria
from ...core import Core
from ...storage import exceptions as storage_exceptions
from ...parser import consumption
from ...utils import (formatting, collections, console)


DESCRIPTION_FIELD_LENGTH_LIMIT = 20
SERVICE_TEMPLATE_COLUMNS = \
    ('id', 'name', 'description', 'main_file_name', 'created_at', 'updated_at')


@aria.group(name='service-templates')
@aria.options.verbose()
def service_templates():
    """Handle service templates on the manager
    """
    pass


@service_templates.command(name='show',
                           short_help='Show service template information')
@aria.argument('service-template-name')
@aria.options.verbose()
@aria.pass_model_storage
@aria.options.service_template_mode_full
@aria.options.mode_types
@aria.options.format_json
@aria.options.format_yaml
@aria.pass_logger
def show(service_template_name, model_storage, mode_full, mode_types, format_json, format_yaml,
         logger):
    """Show information for a specific service template

    `SERVICE_TEMPLATE_NAME` is the name of the service template to show information on.
    """
    service_template = model_storage.service_template.get_by_name(service_template_name)

    if format_json or format_yaml:
        mode_full = True

    if mode_full:
        consumption.ConsumptionContext()
        if format_json:
            console.puts(formatting.json_dumps(collections.prune(service_template.as_raw)))
        elif format_yaml:
            console.puts(formatting.yaml_dumps(collections.prune(service_template.as_raw)))
        else:
            service_template.dump()
    elif mode_types:
        consumption.ConsumptionContext()
        service_template.dump_types()
    else:
        logger.info('Showing service template {0}...'.format(service_template_name))
        service_template_dict = service_template.to_dict()
        service_template_dict['#services'] = len(service_template.services)
        columns = SERVICE_TEMPLATE_COLUMNS + ('#services',)
        column_formatters = \
            dict(description=table.trim_formatter_generator(DESCRIPTION_FIELD_LENGTH_LIMIT))
        table.print_data(columns, service_template_dict, 'Service-template:',
                         column_formatters=column_formatters, col_max_width=50)

        if service_template_dict['description'] is not None:
            logger.info('Description:')
            logger.info('{0}{1}'.format(service_template_dict['description'].encode('UTF-8') or '',
                                        os.linesep))

        if service_template.services:
            logger.info('Existing services:')
            for service in service_template.services:
                logger.info('\t{0}'.format(service.name))


@service_templates.command(name='list',
                           short_help='List service templates')
@aria.options.sort_by()
@aria.options.descending
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def list(sort_by, descending, model_storage, logger):
    """List all service templates
    """

    logger.info('Listing all service templates...')
    service_templates_list = model_storage.service_template.list(
        sort=utils.storage_sort_param(sort_by, descending))

    column_formatters = \
        dict(description=table.trim_formatter_generator(DESCRIPTION_FIELD_LENGTH_LIMIT))
    table.print_data(SERVICE_TEMPLATE_COLUMNS, service_templates_list, 'Service templates:',
                     column_formatters=column_formatters)


@service_templates.command(name='store',
                           short_help='Store a service template')
@aria.argument('service-template-path')
@aria.argument('service-template-name')
@aria.options.service_template_filename
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def store(service_template_path, service_template_name, service_template_filename,
          model_storage, resource_storage, plugin_manager, logger):
    """Store a service template

    `SERVICE_TEMPLATE_PATH` is the path of the service template to store.

    `SERVICE_TEMPLATE_NAME` is the name of the service template to store.
    """
    logger.info('Storing service template {0}...'.format(service_template_name))

    service_template_path = service_template_utils.get(service_template_path,
                                                       service_template_filename)
    core = Core(model_storage, resource_storage, plugin_manager)
    try:
        core.create_service_template(service_template_path,
                                     os.path.dirname(service_template_path),
                                     service_template_name)
    except storage_exceptions.StorageError as e:
        utils.check_overriding_storage_exceptions(e, 'service template', service_template_name)
        raise
    logger.info('Service template {0} stored'.format(service_template_name))


@service_templates.command(name='delete',
                           short_help='Delete a service template')
@aria.argument('service-template-name')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def delete(service_template_name, model_storage, resource_storage, plugin_manager, logger):
    """Delete a service template

    `SERVICE_TEMPLATE_NAME` is the name of the service template to delete.
    """
    logger.info('Deleting service template {0}...'.format(service_template_name))
    service_template = model_storage.service_template.get_by_name(service_template_name)
    core = Core(model_storage, resource_storage, plugin_manager)
    core.delete_service_template(service_template.id)
    logger.info('Service template {0} deleted'.format(service_template_name))


@service_templates.command(name='inputs',
                           short_help='Show service template inputs')
@aria.argument('service-template-name')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def inputs(service_template_name, model_storage, logger):
    """Show inputs for a specific service template

    `SERVICE_TEMPLATE_NAME` is the name of the service template to show inputs for.
    """
    logger.info('Showing inputs for service template {0}...'.format(service_template_name))
    print_service_template_inputs(model_storage, service_template_name, logger)


@service_templates.command(name='validate',
                           short_help='Validate a service template')
@aria.argument('service-template')
@aria.options.service_template_filename
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def validate(service_template, service_template_filename,
             model_storage, resource_storage, plugin_manager, logger):
    """Validate a service template

    `SERVICE_TEMPLATE` is the path or URL of the service template or archive to validate.
    """
    logger.info('Validating service template: {0}'.format(service_template))
    service_template_path = service_template_utils.get(service_template, service_template_filename)
    core = Core(model_storage, resource_storage, plugin_manager)
    core.validate_service_template(service_template_path)
    logger.info('Service template validated successfully')


@service_templates.command(name='create-archive',
                           short_help='Create a CSAR archive')
@aria.argument('service-template-path')
@aria.argument('destination')
@aria.options.verbose()
@aria.pass_logger
def create_archive(service_template_path, destination, logger):
    """Create a CSAR archive

    `service_template_path` is the path of the service template to create the archive from
    `destination` is the path of the output CSAR archive
    """
    logger.info('Creating a CSAR archive')
    if not destination.endswith(csar.CSAR_FILE_EXTENSION):
        destination += csar.CSAR_FILE_EXTENSION
    csar.write(service_template_path, destination, logger)
    logger.info('CSAR archive created at {0}'.format(destination))


def print_service_template_inputs(model_storage, service_template_name, logger):
    service_template = model_storage.service_template.get_by_name(service_template_name)

    logger.info('Service template inputs:')
    if service_template.inputs:
        logger.info(utils.get_parameter_templates_as_string(service_template.inputs))
    else:
        logger.info('\tNo inputs')
