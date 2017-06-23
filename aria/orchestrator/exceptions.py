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
Orchestrator exceptions.
"""

from aria.exceptions import AriaError


class OrchestratorError(AriaError):
    """
    Orchestrator based exception
    """
    pass


class InvalidPluginError(AriaError):
    """
    Raised when an invalid plugin is validated unsuccessfully
    """
    pass


class PluginAlreadyExistsError(AriaError):
    """
    Raised when a plugin with the same package name and package version already exists
    """
    pass


class TaskRetryException(RuntimeError):
    """
    Used internally when ctx.task.retry is called
    """
    def __init__(self, message, retry_interval=None):
        super(TaskRetryException, self).__init__(message)
        self.retry_interval = retry_interval


class TaskAbortException(RuntimeError):
    """
    Used internally when ctx.task.abort is called
    """
    pass


class UndeclaredWorkflowError(AriaError):
    """
    Raised when attempting to execute an undeclared workflow
    """
    pass


class ActiveExecutionsError(AriaError):
    """
    Raised when attempting to execute a workflow on a service which already has an active execution
    """
    pass


class WorkflowImplementationNotFoundError(AriaError):
    """
    Raised when attempting to import a workflow's code but the implementation is not found
    """
    pass


class InvalidWorkflowRunnerParams(AriaError):
    """
    Raised when invalid combination of arguments is passed to the workflow runner
    """
    pass
