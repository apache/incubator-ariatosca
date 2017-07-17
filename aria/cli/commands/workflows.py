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
CLI ``worfklows`` sub-commands.
"""

from .. import table
from ..core import aria
from ..exceptions import AriaCliError

WORKFLOW_COLUMNS = ['name', 'service_template_name', 'service_name']


@aria.group(name='workflows')
def workflows():
    """
    Manage service workflows
    """
    pass


@workflows.command(name='show',
                   short_help='Show information for a service workflow')
@aria.argument('workflow-name')
@aria.options.service_name(required=True)
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def show(workflow_name, service_name, model_storage, logger):
    """
    Show information for a service workflow

    SERVICE_NAME is the unique name of the service.

    WORKFLOW_NAME is the unique name of the workflow within the service (e.g. "uninstall").
    """
    logger.info('Retrieving workflow {0} for service {1}'.format(
        workflow_name, service_name))
    service = model_storage.service.get_by_name(service_name)
    workflow = next((wf for wf in service.workflows.itervalues() if
                     wf.name == workflow_name), None)
    if not workflow:
        raise AriaCliError(
            'Workflow {0} not found for service {1}'.format(workflow_name, service_name))

    defaults = {
        'service_template_name': service.service_template_name,
        'service_name': service.name
    }
    table.print_data(WORKFLOW_COLUMNS, workflow, 'Workflows:', defaults=defaults)

    # print workflow inputs
    required_inputs = dict()
    optional_inputs = dict()
    for input_name, input in workflow.inputs.iteritems():
        inputs_group = optional_inputs if input.value is not None else required_inputs
        inputs_group[input_name] = input

    logger.info('Workflow Inputs:')
    logger.info('\tMandatory Inputs:')
    for input_name, input in required_inputs.iteritems():
        if input.description is not None:
            logger.info('\t\t{0}\t({1})'.format(input_name,
                                                input.description))
        else:
            logger.info('\t\t{0}'.format(input_name))

    logger.info('\tOptional Inputs:')
    for input_name, input in optional_inputs.iteritems():
        if input.description is not None:
            logger.info('\t\t{0}: \t{1}\t({2})'.format(
                input_name, input.value, input.description))
        else:
            logger.info('\t\t{0}: \t{1}'.format(input_name,
                                                input.value))


@workflows.command(name='list',
                   short_help='List service workflows')
@aria.options.service_name(required=True)
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def list(service_name, model_storage, logger):
    """
    List service workflows

    SERVICE_NAME is the unique name of the service.
    """
    logger.info('Listing workflows for service {0}...'.format(service_name))
    service = model_storage.service.get_by_name(service_name)
    workflows_list = sorted(service.workflows.itervalues(), key=lambda w: w.name)

    defaults = {
        'service_template_name': service.service_template_name,
        'service_name': service.name
    }
    table.print_data(WORKFLOW_COLUMNS, workflows_list, 'Workflows:', defaults=defaults)
