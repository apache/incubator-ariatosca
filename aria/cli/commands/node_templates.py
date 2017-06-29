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
CLI ``node-templates`` sub-commands.
"""

from .. import table
from .. import utils
from ..core import aria


NODE_TEMPLATE_COLUMNS = ['id', 'name', 'description', 'service_template_name', 'type_name']


@aria.group(name='node-templates')
@aria.options.verbose()
def node_templates():
    """
    Manages stored service templates' node templates
    """
    pass


@node_templates.command(name='show',
                        short_help='Show information for a stored node template')
@aria.argument('node-template-id')
# @aria.options.service_template_name(required=True)
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def show(node_template_id, model_storage, logger):
    """
    Show information for a stored node template

    NODE_TEMPLATE_ID is the unique node template ID.
    """
    logger.info('Showing node template {0}'.format(node_template_id))
    node_template = model_storage.node_template.get(node_template_id)

    table.print_data(NODE_TEMPLATE_COLUMNS, node_template, 'Node template:', col_max_width=50)

    # print node template properties
    logger.info('Node template properties:')
    if node_template.properties:
        logger.info(utils.get_parameter_templates_as_string(node_template.properties))
    else:
        logger.info('\tNo properties')

    # print node IDs
    nodes = node_template.nodes
    logger.info('Nodes:')
    if nodes:
        for node in nodes:
            logger.info('\t{0}'.format(node.name))
    else:
        logger.info('\tNo nodes')


@node_templates.command(name='list',
                        short_help='List stored node templates')
@aria.options.service_template_name()
@aria.options.sort_by('service_template_name')
@aria.options.descending
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def list(service_template_name, sort_by, descending, model_storage, logger):
    """
    List stored node templates

    If SERVICE_TEMPLATE_NAME is provided, list node templates for that stored service template.
    Otherwise, list node templates for all service templates.
    """
    if service_template_name:
        logger.info('Listing node templates for service template {0}...'.format(
            service_template_name))
        service_template = model_storage.service_template.get_by_name(service_template_name)
        filters = dict(service_template=service_template)
    else:
        logger.info('Listing all node templates...')
        filters = {}

    node_templates_list = model_storage.node_template.list(
        filters=filters,
        sort=utils.storage_sort_param(sort_by, descending))

    table.print_data(NODE_TEMPLATE_COLUMNS, node_templates_list, 'Node templates:')
