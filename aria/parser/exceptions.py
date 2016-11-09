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

import sys

from .validation import Issue


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
        self.cause_tb = cause_traceback


class InvalidValueError(AriaException):
    """
    ARIA error: value is invalid.
    """

    def __init__(self, message, cause=None, cause_tb=None, location=None, line=None, column=None,
                 locator=None, snippet=None, level=Issue.FIELD):
        super(InvalidValueError, self).__init__(message, cause, cause_tb)
        self.issue = Issue(message, location=location, line=line, column=column, locator=locator,
                           snippet=snippet, level=level, exception=cause)
