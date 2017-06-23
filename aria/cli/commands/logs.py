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
CLI ``logs`` sub-commands.
"""

from .. import execution_logging
from ..logger import ModelLogIterator
from ..core import aria


@aria.group(name='logs')
@aria.options.verbose()
def logs():
    """
    Manage logs of workflow executions
    """
    pass


@logs.command(name='list',
              short_help='List logs for an execution')
@aria.argument('execution-id')
@aria.options.verbose()
@aria.options.mark_pattern()
@aria.pass_model_storage
@aria.pass_logger
def list(execution_id, mark_pattern, model_storage, logger):
    """
    List logs for an execution

    EXECUTION_ID is the unique ID of the execution.
    """
    logger.info('Listing logs for execution id {0}'.format(execution_id))
    log_iterator = ModelLogIterator(model_storage, execution_id)

    any_logs = execution_logging.log_list(log_iterator, mark_pattern=mark_pattern)

    if not any_logs:
        logger.info('\tNo logs')


@logs.command(name='delete',
              short_help='Delete logs of an execution')
@aria.argument('execution-id')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def delete(execution_id, model_storage, logger):
    """
    Delete logs of an execution

    EXECUTION_ID is the unique ID of the execution.
    """
    logger.info('Deleting logs for execution id {0}'.format(execution_id))
    logs_list = model_storage.log.list(filters=dict(execution_fk=execution_id))
    for log in logs_list:
        model_storage.log.delete(log)
    logger.info('Deleted logs for execution id {0}'.format(execution_id))
