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

import json
import time

from .. import utils
from ..table import print_data
from ..cli import aria, helptexts
from ..exceptions import AriaCliError
from ...modeling.models import Execution
from ...storage.exceptions import StorageError
from ...orchestrator.workflow_runner import WorkflowRunner
from ...utils import formatting
from ...utils import threading

EXECUTION_COLUMNS = ['id', 'workflow_name', 'status', 'service_name',
                     'created_at', 'error']


@aria.group(name='executions')
@aria.options.verbose()
def executions():
    """Handle workflow executions
    """
    pass


@executions.command(name='show',
                    short_help='Show execution information')
@aria.argument('execution-id')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def show(execution_id, model_storage, logger):
    """Show information for a specific execution

    `EXECUTION_ID` is the execution to get information on.
    """
    try:
        logger.info('Showing execution {0}'.format(execution_id))
        execution = model_storage.execution.get(execution_id)
    except StorageError:
        raise AriaCliError('Execution {0} not found'.format(execution_id))

    print_data(EXECUTION_COLUMNS, execution.to_dict(), 'Execution:', max_width=50)

    # print execution parameters
    logger.info('Execution Inputs:')
    if execution.inputs:
        #TODO check this section, havent tested it
        execution_inputs = [ei.to_dict() for ei in execution.inputs]
        for input_name, input_value in formatting.decode_dict(
                execution_inputs).iteritems():
            logger.info('\t{0}: \t{1}'.format(input_name, input_value))
    else:
        logger.info('\tNo inputs')
    logger.info('')


@executions.command(name='list',
                    short_help='List service executions')
@aria.options.service_name(required=False)
@aria.options.sort_by()
@aria.options.descending
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def list(service_name,
         sort_by,
         descending,
         model_storage,
         logger):
    """List executions

    If `SERVICE_NAME` is provided, list executions for that service.
    Otherwise, list executions for all services.
    """
    if service_name:
        logger.info('Listing executions for service {0}...'.format(
            service_name))
        try:
            service = model_storage.service.get_by_name(service_name)
            filters = dict(service=service)
        except StorageError:
            raise AriaCliError('Service {0} does not exist'.format(
                service_name))
    else:
        logger.info('Listing all executions...')
        filters = {}

    executions = [e.to_dict() for e in model_storage.execution.list(
        filters=filters,
        sort=utils.storage_sort_param(sort_by, descending))]

    print_data(EXECUTION_COLUMNS, executions, 'Executions:')


@executions.command(name='start',
                    short_help='Execute a workflow')
@aria.argument('workflow-name')
@aria.options.service_name(required=True)
@aria.options.inputs
@aria.options.task_max_attempts()
@aria.options.task_retry_interval()
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def start(workflow_name,
          service_name,
          inputs,
          task_max_attempts,
          task_retry_interval,
          model_storage,
          resource_storage,
          plugin_manager,
          logger):
    """Execute a workflow

    `WORKFLOW_ID` is the id of the workflow to execute (e.g. `uninstall`)
    """
    workflow_runner = \
        WorkflowRunner(workflow_name, service_name, inputs,
                       model_storage, resource_storage, plugin_manager,
                       task_max_attempts, task_retry_interval)

    execution_thread_name = '{0}_{1}'.format(service_name, workflow_name)
    execution_thread = threading.ExceptionThread(target=workflow_runner.execute,
                                                 name=execution_thread_name)
    execution_thread.daemon = True  # allows force-cancel to exit immediately

    logger.info('Starting execution. Press Ctrl+C cancel')
    execution_thread.start()
    try:
        while execution_thread.is_alive():
            # using join without a timeout blocks and ignores KeyboardInterrupt
            execution_thread.join(1)
    except KeyboardInterrupt:
        _cancel_execution(workflow_runner, execution_thread, logger)

    # raise any errors from the execution thread (note these are not workflow execution errors)
    execution_thread.raise_error_if_exists()

    execution = workflow_runner.execution
    logger.info('Execution has ended with "{0}" status'.format(execution.status))
    if execution.status == Execution.FAILED:
        logger.info('Execution error:\n{0}'.format(execution.error))


def _cancel_execution(workflow_runner, execution_thread, logger):
    logger.info('Cancelling execution. Press Ctrl+C again to force-cancel')
    try:
        workflow_runner.cancel()
        while execution_thread.is_alive():
            execution_thread.join(1)
    except KeyboardInterrupt:
        logger.info('Force-cancelling execution')
        # TODO handle execution (update status etc.) and exit process
