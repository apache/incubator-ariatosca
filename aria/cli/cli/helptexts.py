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

VERBOSE = \
    "Show verbose output. You can supply this up to three times (i.e. -vvv)"
VERSION = "Display the version and exit"

INPUTS_PARAMS_USAGE = (
    '(Can be provided as wildcard based paths '
    '(*.yaml, /my_inputs/, etc..) to YAML files, a JSON string or as '
    'key1=value1;key2=value2). This argument can be used multiple times'
)
WORKFLOW_TO_EXECUTE = "The workflow to execute [default: {0}]"

SERVICE_TEMPLATE_PATH = "The path to the application's service template file"
SERVICE_TEMPLATE_ID = "The unique identifier for the service template"

RESET_CONTEXT = "Reset the working environment"
HARD_RESET = "Hard reset the configuration, including coloring and loggers"
SHOW_ACTIVE_CONNECTION_INFORMATION = \
    "Show connection information for the active manager"
ENABLE_COLORS = "Enable colors in logger (use --hard when working with" \
                " an initialized environment) [default: False]"

OUTPUT_PATH = "The local path to download to"
SERVICE_TEMPLATE_FILENAME = (
    "The name of the archive's main service template file. "
    "This is only relevant if uploading an archive")
INPUTS = "Inputs for the deployment {0}".format(INPUTS_PARAMS_USAGE)
PARAMETERS = "Parameters for the workflow {0}".format(INPUTS_PARAMS_USAGE)
TASK_RETRY_INTERVAL = \
    "How long of a minimal interval should occur between task retry attempts [default: {0}]"
TASK_MAX_ATTEMPTS = \
    "How many times should a task be attempted in case of failures [default: {0}]"
TASK_THREAD_POOL_SIZE = \
    "The size of the thread pool to execute tasks in [default: {0}]"

OPERATION_TIMEOUT = (
    "Operation timeout in seconds (The execution itself will keep going, but "
    "the CLI will stop waiting for it to terminate) [default: {0}]"
)
JSON_OUTPUT = "Output events in a consumable JSON format"

SERVICE_ID = "The unique identifier for the service"
EXECUTION_ID = "The unique identifier for the execution"
IGNORE_RUNNING_NODES = "Delete the deployment even if it has running nodes"

NODE_NAME = "The node's name"

DEFAULT_MUTUALITY_MESSAGE = 'Cannot be used simultaneously'

SORT_BY = "Key for sorting the list"
DESCENDING = "Sort list in descending order [default: False]"
