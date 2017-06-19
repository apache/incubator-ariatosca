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

from .. import helptexts
from .. import table
from .. import utils
from .. import logger as cli_logger
from .. import execution_logging
from ..core import aria
from ...modeling.models import Execution
from ...orchestrator.workflow_runner import WorkflowRunner
from ...orchestrator.workflows.executor.dry import DryExecutor
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
    logger.info('Showing execution {0}'.format(execution_id))
    execution = model_storage.execution.get(execution_id)

    table.print_data(EXECUTION_COLUMNS, execution, 'Execution:', col_max_width=50)

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
        service = model_storage.service.get_by_name(service_name)
        filters = dict(service=service)
    else:
        logger.info('Listing all executions...')
        filters = {}

    executions_list = model_storage.execution.list(
        filters=filters,
        sort=utils.storage_sort_param(sort_by, descending)).items

    table.print_data(EXECUTION_COLUMNS, executions_list, 'Executions:')


@executions.command(name='start',
                    short_help='Execute a workflow')
@aria.argument('workflow-name')
@aria.options.service_name(required=True)
@aria.options.inputs(help=helptexts.EXECUTION_INPUTS)
@aria.options.dry_execution
@aria.options.task_max_attempts()
@aria.options.task_retry_interval()
@aria.options.mark_pattern()
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def start(workflow_name,
          service_name,
          inputs,
          dry,
          task_max_attempts,
          task_retry_interval,
          mark_pattern,
          model_storage,
          resource_storage,
          plugin_manager,
          logger):
    """Execute a workflow

    `WORKFLOW_NAME` is the name of the workflow to execute (e.g. `uninstall`)
    """
    service = model_storage.service.get_by_name(service_name)
    executor = DryExecutor() if dry else None  # use WorkflowRunner's default executor

    workflow_runner = \
        WorkflowRunner(
            model_storage, resource_storage, plugin_manager,
            service_id=service.id, workflow_name=workflow_name, inputs=inputs, executor=executor,
            task_max_attempts=task_max_attempts, task_retry_interval=task_retry_interval
        )
    logger.info('Starting {0}execution. Press Ctrl+C cancel'.format('dry ' if dry else ''))

    _run_execution(workflow_runner, logger, model_storage, dry, mark_pattern)


@executions.command(name='resume',
                    short_help='Resume a workflow')
@aria.argument('execution-id')
@aria.options.inputs(help=helptexts.EXECUTION_INPUTS)
@aria.options.dry_execution
@aria.options.task_max_attempts()
@aria.options.task_retry_interval()
@aria.options.mark_pattern()
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_resource_storage
@aria.pass_plugin_manager
@aria.pass_logger
def resume(execution_id,
           dry,
           task_max_attempts,
           task_retry_interval,
           mark_pattern,
           model_storage,
           resource_storage,
           plugin_manager,
           logger):
    executor = DryExecutor() if dry else None  # use WorkflowRunner's default executor

    workflow_runner = \
        WorkflowRunner(
            model_storage, resource_storage, plugin_manager,
            execution_id=execution_id, executor=executor,
            task_max_attempts=task_max_attempts, task_retry_interval=task_retry_interval
        )

    logger.info('Resuming {0}execution. Press Ctrl+C cancel'.format('dry ' if dry else ''))
    _run_execution(workflow_runner, logger, model_storage, dry, mark_pattern)


def _run_execution(workflow_runner, logger, model_storage, dry, mark_pattern):
    execution_thread_name = '{0}_{1}'.format(workflow_runner.service.name,
                                             workflow_runner.execution.workflow_name)
    execution_thread = threading.ExceptionThread(target=workflow_runner.execute,
                                                 name=execution_thread_name)

    execution_thread.start()

    last_task_id = workflow_runner.execution.logs[-1].id if workflow_runner.execution.logs else 0
    log_iterator = cli_logger.ModelLogIterator(model_storage,
                                               workflow_runner.execution_id,
                                               offset=last_task_id)
    try:
        while execution_thread.is_alive():
            execution_logging.log_list(log_iterator, mark_pattern=mark_pattern)
            execution_thread.join(1)

    except KeyboardInterrupt:
        _cancel_execution(workflow_runner, execution_thread, logger, log_iterator)

    # It might be the case where some logs were written and the execution was terminated, thus we
    # need to drain the remaining logs.
    execution_logging.log_list(log_iterator, mark_pattern=mark_pattern)

    # raise any errors from the execution thread (note these are not workflow execution errors)
    execution_thread.raise_error_if_exists()

    execution = workflow_runner.execution
    logger.info('Execution has ended with "{0}" status'.format(execution.status))
    if execution.status == Execution.FAILED and execution.error:
        logger.info('Execution error:{0}{1}'.format(os.linesep, execution.error))

    if dry:
        # remove traces of the dry execution (including tasks, logs, inputs..)
        model_storage.execution.delete(execution)


def _cancel_execution(workflow_runner, execution_thread, logger, log_iterator):
    logger.info('Cancelling execution. Press Ctrl+C again to force-cancel')
    workflow_runner.cancel()
    while execution_thread.is_alive():
        try:
            execution_logging.log_list(log_iterator)
            execution_thread.join(1)
        except KeyboardInterrupt:
            pass
