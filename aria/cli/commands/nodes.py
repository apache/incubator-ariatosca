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

from .. import utils
from ..cli import aria
from ..table import print_data
from ..exceptions import AriaCliError
from ...storage.exceptions import StorageError


NODE_COLUMNS = ['id', 'name', 'service_name', 'node_template_name', 'state']


@aria.group(name='nodes')
@aria.options.verbose()
def nodes():
    """Handle a service's nodes
    """
    pass


@nodes.command(name='show',
               short_help='Show node information')
@aria.argument('node_id')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def show(node_id, model_storage, logger):
    """Showing information for a specific node

    `NODE_ID` is the id of the node to get information on.
    """
    logger.info('Showing node {0}'.format(node_id))
    try:
        node = model_storage.node.get(node_id).to_dict()
    except StorageError:
        raise AriaCliError('Node {0} not found'.format(node_id))

    print_data(NODE_COLUMNS, node, 'Node:', 50)

    # print node attributes
    logger.info('Node attributes:')
    for prop_name, prop_value in node.runtime_properties.iteritems():
        logger.info('\t{0}: {1}'.format(prop_name, prop_value))
    logger.info('')


@nodes.command(name='list',
               short_help='List node for a deployment')
@aria.options.service_id(required=False)
@aria.options.sort_by('service_name')
@aria.options.descending
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def list(service_id,
         sort_by,
         descending,
         model_storage,
         logger):
    """List nodes

    If `SERVICE_ID` is provided, list nodes for that service.
    Otherwise, list nodes for all services.
    """
    if service_id:
        logger.info('Listing nodes for service {0}...'.format(service_id))
        try:
            service = model_storage.service_instance.get(service_id)
            filters = dict(service=service)
        except StorageError:
            raise AriaCliError('Service {0} does not exist'.format(service_id))
    else:
        logger.info('Listing all nodes...')
        filters = {}

    nodes = [node.to_dict() for node in model_storage.node.list(
        filters=filters,
        sort=utils.storage_sort_param(sort_by, descending))]

    print_data(NODE_COLUMNS, nodes, 'Nodes:')
