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
Workflow related Exception classes
"""
import os

from .. import exceptions


class ExecutorException(exceptions.AriaError):
    """
    General executor exception
    """
    pass


class ProcessException(ExecutorException):
    """
    Raised when subprocess execution fails
    """

    def __init__(self, command, stderr=None, stdout=None, return_code=None):
        """
        Process class Exception
        :param list command: child process command
        :param str message: custom message
        :param str stderr: child process stderr
        :param str stdout: child process stdout
        :param int return_code: child process exit code
        """
        super(ProcessException, self).__init__("child process failed")
        self.command = command
        self.stderr = stderr
        self.stdout = stdout
        self.return_code = return_code

    @property
    def explanation(self):
        """
        Describes the error in detail
        """
        return (
            'Command "{error.command}" executed with an error.{0}'
            'code: {error.return_code}{0}'
            'error: {error.stderr}{0}'
            'output: {error.stdout}'.format(os.linesep, error=self))


class AriaEngineError(exceptions.AriaError):
    """
    Raised by the workflow engine
    """


class TaskException(exceptions.AriaError):
    """
    Raised by the task
    """


class TaskCreationException(TaskException):
    """
    Could not create the task.
    """


class OperationNotFoundException(TaskCreationException):
    """
    Could not find an operation on the node or relationship.
    """


class PluginNotFoundException(TaskCreationException):
    """
    Could not find a plugin matching the plugin specification.
    """
