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
Base exception classes and other common exceptions used throughout ARIA.
"""

import sys


class AriaError(Exception):
    """
    Base class for ARIA errors.
    """
    pass


class AriaException(Exception):
    """
    Base class for ARIA exceptions.
    """

    def __init__(self, message=None, cause=None, cause_traceback=None):
        super(AriaException, self).__init__(message)
        self.cause = cause
        self.issue = None
        if cause_traceback is None:
            _, e, traceback = sys.exc_info()
            if cause == e:
                # Make sure it's our traceback
                cause_traceback = traceback
        self.cause_traceback = cause_traceback


class DependentServicesError(AriaError):
    """
    Raised when attempting to delete a service template which has existing services.
    """
    pass


class DependentActiveExecutionsError(AriaError):
    """
    Raised when attempting to delete a service which has active executions.
    """
    pass


class DependentAvailableNodesError(AriaError):
    """
    Raised when attempting to delete a service which has available nodes.
    """
    pass


class ParsingError(AriaError):
    pass


class InstantiationError(AriaError):
    pass


class TypeDefinitionException(AriaError):
    """The base exception class of the type definition"""
    pass


class TypeDefinitionNotFoundException(TypeDefinitionException):
    """The exception class of the type definition thrown
       if type definition does not exists"""
    pass


class TypeDefinitionAlreadyExistsException(TypeDefinitionException):
    """The exception class of the type definition thrown
       if type definition already exists"""
    pass


class InvalidTypeDefinitionException(TypeDefinitionException):
    """The exception class of the type definition thrown
       if type definition is not a valid archive or validation error
       exists during the type definition load"""
    pass
