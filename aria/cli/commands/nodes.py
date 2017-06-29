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
CLI ``nodes`` sub-commands.
"""

from .. import table
from .. import utils
from ..core import aria


NODE_COLUMNS = ['id', 'name', 'service_name', 'node_template_name', 'state']


@aria.group(name='nodes')
@aria.options.verbose()
def nodes():
    """
    Manage services' nodes
    """
    pass


@nodes.command(name='show',
               short_help='Show information for a node')
@aria.argument('node_id')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def show(node_id, model_storage, logger):
    """
    Show information for a node

    NODE_ID is the unique node ID.
    """
    logger.info('Showing node {0}'.format(node_id))
    node = model_storage.node.get(node_id)

    table.print_data(NODE_COLUMNS, node, 'Node:', col_max_width=50)

    # print node attributes
    logger.info('Node attributes:')
    if node.attributes:
        for param_name, param in node.attributes.iteritems():
            logger.info('\t{0}: {1}'.format(param_name, param.value))
    else:
        logger.info('\tNo attributes')


@nodes.command(name='list',
               short_help='List node')
@aria.options.service_name(required=False)
@aria.options.sort_by('service_name')
@aria.options.descending
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def list(service_name,
         sort_by,
         descending,
         model_storage,
         logger):
    """
    List nodes

    If SERVICE_NAME is provided, list nodes for that service. Otherwise, list nodes for all
    services.
    """
    if service_name:
        logger.info('Listing nodes for service {0}...'.format(service_name))
        service = model_storage.service.get_by_name(service_name)
        filters = dict(service=service)
    else:
        logger.info('Listing all nodes...')
        filters = {}

    nodes_list = model_storage.node.list(
        filters=filters,
        sort=utils.storage_sort_param(sort_by, descending))

    table.print_data(NODE_COLUMNS, nodes_list, 'Nodes:')
