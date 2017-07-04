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
Execution plugin constants.
"""
import os
import tempfile

from . import exceptions

# related to local
PYTHON_SCRIPT_FILE_EXTENSION = '.py'
POWERSHELL_SCRIPT_FILE_EXTENSION = '.ps1'
DEFAULT_POWERSHELL_EXECUTABLE = 'powershell'

# related to both local and ssh
ILLEGAL_CTX_OPERATION_MESSAGE = 'ctx may only abort or retry once'

# related to ssh
DEFAULT_BASE_DIR = os.path.join(tempfile.gettempdir(), 'aria-ctx')
FABRIC_ENV_DEFAULTS = {
    'connection_attempts': 5,
    'timeout': 10,
    'forward_agent': False,
    'abort_on_prompts': True,
    'keepalive': 0,
    'linewise': False,
    'pool_size': 0,
    'skip_bad_hosts': False,
    'status': False,
    'disable_known_hosts': True,
    'combine_stderr': True,
    'abort_exception': exceptions.TaskException,
}
VALID_FABRIC_GROUPS = set([
    'status',
    'aborts',
    'warnings',
    'running',
    'stdout',
    'stderr',
    'user',
    'everything'
])
