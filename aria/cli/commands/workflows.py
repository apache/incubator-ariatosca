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

from ..table import print_data
from .. import utils
from ..cli import aria
from ..exceptions import AriaCliError
from ...storage.exceptions import StorageError

WORKFLOW_COLUMNS = ['name', 'service_template_name', 'service_name']


@aria.group(name='workflows')
def workflows():
    """Handle service workflows
    """
    pass


@workflows.command(name='show',
                   short_help='Show workflow information')
@aria.argument('workflow-name')
@aria.options.service_name(required=True)
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def show(workflow_name, service_name, model_storage, logger):
    """Show information for a specific workflow of a specific deployment

    `WORKFLOW_NAME` is the name of the workflow to get information on.
    """
    try:
        logger.info('Retrieving workflow {0} for service {1}'.format(
            workflow_name, service_name))
        service = model_storage.service.get(service_name)
        workflow = next((wf for wf in service.workflows if
                         wf.name == workflow_name), None)
        if not workflow:
            raise AriaCliError(
                'Workflow {0} not found for service {1}'.format(workflow_name, service_name))
    except StorageError:
        raise AriaCliError('service {0} not found'.format(service_name))

    defaults = {
        'service_template_name': service.service_template_name,
        'service_name': service.name
    }
    print_data(WORKFLOW_COLUMNS, workflow, 'Workflows:', defaults=defaults)

    # print workflow parameters
    mandatory_params = dict()
    optional_params = dict()
    for param_name, param in workflow.parameters.iteritems():
        params_group = optional_params if 'default' in param else \
            mandatory_params
        params_group[param_name] = param

    logger.info('Workflow Parameters:')
    logger.info('\tMandatory Parameters:')
    for param_name, param in mandatory_params.iteritems():
        if 'description' in param:
            logger.info('\t\t{0}\t({1})'.format(param_name,
                                                param['description']))
        else:
            logger.info('\t\t{0}'.format(param_name))

    logger.info('\tOptional Parameters:')
    for param_name, param in optional_params.iteritems():
        if 'description' in param:
            logger.info('\t\t{0}: \t{1}\t({2})'.format(
                param_name, param['default'], param['description']))
        else:
            logger.info('\t\t{0}: \t{1}'.format(param_name,
                                                param['default']))
    logger.info('')


@workflows.command(name='list',
                   short_help='List workflows for a deployment')
@aria.options.service_name(required=True)
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def list(service_name, model_storage, logger):
    """List all workflows of a specific service
    """
    logger.info('Listing workflows for service {0}...'.format(service_name))
    service = model_storage.service.get_by_name(service_name)
    workflows = [wf.to_dict() for wf in sorted(service.workflows.values(), key=lambda w: w.name)]

    defaults = {
        'service_template_name': service.service_template_name,
        'service_name': service.name
    }
    print_data(WORKFLOW_COLUMNS, workflows, 'Workflows:', defaults=defaults)
