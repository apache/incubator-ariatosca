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
Gathers all CLI command help texts in one place.
"""

DEFAULT_MUTUALITY_ERROR_MESSAGE = 'mutually exclusive'
VERBOSE = \
    "Show verbose output; you can supply this up to three times (i.e. -vvv)"

VERSION = "Display the version and exit"
FORCE_RESET = "Confirmation for resetting ARIA's working directory"
RESET_CONFIG = "Reset ARIA's user configuration"

SERVICE_TEMPLATE_ID = "The unique identifier for the service template"
SERVICE_ID = "The unique identifier for the service"
EXECUTION_ID = "The unique identifier for the execution"

SERVICE_TEMPLATE_PATH = "The path to the application's service template file"
SERVICE_TEMPLATE_FILENAME = (
    "The name of the archive's main service template file "
    "(only relevant if uploading a non-CSAR archive)")
INPUTS_PARAMS_USAGE = (
    '(can be provided as wildcard based paths '
    '("inp?.yaml", "/my_inputs/", etc.) to YAML files, a JSON string or as '
    '"key1=value1;key2=value2"); this argument can be used multiple times')
SERVICE_INPUTS = "Inputs for the service {0}".format(INPUTS_PARAMS_USAGE)
EXECUTION_INPUTS = "Inputs for the execution {0}".format(INPUTS_PARAMS_USAGE)

TASK_RETRY_INTERVAL = \
    "How long of a minimal interval should occur between task retry attempts [default: {0}]"
TASK_MAX_ATTEMPTS = \
    "How many times should a task be attempted in case of failures [default: {0}]"
DRY_EXECUTION = "Execute a workflow dry run (prints operations information without causing side " \
                "effects)"
RETRY_FAILED_TASK = "Retry tasks that failed in the previous execution attempt"
IGNORE_AVAILABLE_NODES = "Delete the service even if it has available nodes"
SORT_BY = "Key for sorting the list"
DESCENDING = "Sort list in descending order [default: False]"
JSON_OUTPUT = "Output logs in JSON format"
MARK_PATTERN = "Mark a regular expression pattern in the logs"

SHOW_FULL = "Show full information"
SHOW_JSON = "Show in JSON format (implies --full)"
SHOW_YAML = "Show in YAML format (implies --full)"
SHOW_TYPES = "Show only the type hierarchies"
SHOW_GRAPH = "Show only the node graph"
MODE_MUTUALITY_ERROR_MESSAGE = 'only one mode is possible'
FORMAT_MUTUALITY_ERROR_MESSAGE = 'only one format is possible'
