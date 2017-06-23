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
Execution plugin exceptions.
"""

class ProcessException(Exception):
    """
    Raised when local scripts and remote SSH commands fail.
    """

    def __init__(self, stderr=None, stdout=None, command=None, exit_code=None):
        super(ProcessException, self).__init__(stderr)
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


class TaskException(Exception):
    """
    Raised when remote ssh scripts fail.
    """


class ScriptException(Exception):
    """
    Used by the ``ctx`` proxy server when task.retry or task.abort are called by scripts.
    """

    def __init__(self, message=None, retry=None, retry_interval=None):
        super(ScriptException, self).__init__(message)
        self.retry = retry
        self.retry_interval = retry_interval
