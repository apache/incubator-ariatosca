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
import json

from .. import utils
from .. import csar
from ..cli import aria
from .. import service_template_utils
from ..table import print_data
from ..exceptions import AriaCliError
from ...core import Core
from ...exceptions import AriaException


DESCRIPTION_LIMIT = 20
SERVICE_TEMPLATE_COLUMNS = \
    ['id', 'name', 'main_file_name', 'created_at', 'updated_at']


@aria.group(name='service-templates')
@aria.options.verbose()
def service_templates():
    """Handle service templates on the manager
    """
    pass


@service_templates.command(name='show',
                           short_help='Show service template information')
@aria.argument('service-template-id')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def show(service_template_id, model_storage, logger):
    """Show information for a specific service templates

    `SERVICE_TEMPLATE_ID` is the id of the service template to show information on.
    """
    logger.info('Showing service template {0}...'.format(service_template_id))
    service_template = model_storage.service_template.get(service_template_id)
    services = [d.to_dict() for d in service_template.services]
    service_template_dict = service_template.to_dict()
    service_template_dict['#services'] = len(services)
    columns = SERVICE_TEMPLATE_COLUMNS + ['#services']
    print_data(columns, service_template_dict, 'Service-template:', max_width=50)

    logger.info('Description:')
    logger.info('{0}\n'.format(service_template_dict['description'].encode('UTF-8') or ''))

    logger.info('Existing services:')
    logger.info('{0}\n'.format(json.dumps([d['name'] for d in services])))


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
    def trim_description(service_template):
        if service_template['description'] is not None:
            if len(service_template['description']) >= DESCRIPTION_LIMIT:
                service_template['description'] = '{0}..'.format(
                    service_template['description'][:DESCRIPTION_LIMIT - 2])
        else:
            service_template['description'] = ''
        return service_template

    logger.info('Listing all service templates...')
    service_templates = [trim_description(b.to_dict()) for b in model_storage.service_template.list(
        sort=utils.storage_sort_param(sort_by, descending))]
    print_data(SERVICE_TEMPLATE_COLUMNS, service_templates, 'Service templates:')


@service_templates.command(name='store',
                           short_help='Store a service template')
@aria.argument('service-template-path')
@aria.argument('service-template-name')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def store(service_template_path, service_template_name, model_storage, resource_storage,
          plugin_manager, logger):
    """Store a service template

    `SERVICE_TEMPLATE_PATH` is the path of the service template to store.

    `SERVICE_TEMPLATE_NAME` is the name of the service template to store.
    """
    logger.info('Storing service template {0}...'.format(service_template_name))

    service_template_path = service_template_utils.get(service_template_path)
    core = Core(model_storage, resource_storage, plugin_manager)
    core.create_service_template(service_template_path,
                                 os.path.dirname(service_template_path),
                                 service_template_name)

    logger.info('Service template stored')


@service_templates.command(name='delete',
                           short_help='Delete a service template')
@aria.argument('service-template-id')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def delete(service_template_id, model_storage, resource_storage, plugin_manager, logger):
    """Delete a service template
    `SERVICE_TEMPLATE_ID` is the id of the service template to delete.
    """
    logger.info('Deleting service template {0}...'.format(service_template_id))
    core = Core(model_storage, resource_storage, plugin_manager)
    core.delete_service_template(service_template_id)
    logger.info('Service template {0} deleted'.format(service_template_id))


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
    print_service_template_inputs(model_storage, service_template_name)


@service_templates.command(name='validate',
                           short_help='Validate a service template')
@aria.argument('service-template')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def validate_service_template(service_template, model_storage, resource_storage, plugin_manager,
                              logger):
    """Validate a service template

    `SERVICE_TEMPLATE` is the path or url of the service template or archive to validate.
    """
    logger.info('Validating service template: {0}'.format(service_template))
    service_template_path = service_template_utils.get(service_template)
    core = Core(model_storage, resource_storage, plugin_manager)

    try:
        core.validate_service_template(service_template_path)
    except AriaException as e:
        # TODO: gather errors from parser and dump them via CLI?
        raise AriaCliError(str(e))

    logger.info('Service template validated successfully')


@service_templates.command(name='create-archive',
                           short_help='Create a csar archive')
@aria.argument('service-template-path')
@aria.argument('destination')
@aria.options.verbose()
@aria.pass_logger
def create_archive(service_template_path, destination, logger):
    """Create a csar archive

    `service_template_path` is the path of the service template to create the archive from
    `destination` is the path of the output csar archive
    """
    logger.info('Creating a csar archive')
    csar.write(os.path.dirname(service_template_path), service_template_path, destination, logger)
    logger.info('Csar archive created at {0}'.format(destination))


@aria.pass_logger
def print_service_template_inputs(model_storage, service_template_name, logger):
    service_template = model_storage.service_template.get_by_name(service_template_name)

    logger.info('Service template inputs:')
    logger.info(utils.get_parameter_templates_as_string(service_template.inputs))
