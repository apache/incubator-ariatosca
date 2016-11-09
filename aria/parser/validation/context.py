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

from .issue import Issue
from ..utils import (LockedList, FrozenList, print_exception, puts, Colored, indent, as_raw)

class ValidationContext(object):
    """
    Properties:

    * :code:`allow_unknown_fields`: When False (the default) will report an issue
            if an unknown field is used
    * :code:`allow_primitive_coersion`: When False (the default) will not attempt to
            coerce primitive field types
    * :code:`max_level`: Maximum validation level to report (default is all)
    """

    def __init__(self):
        self.allow_unknown_fields = False
        self.allow_primitive_coersion = False
        self.max_level = Issue.ALL

        self._issues = LockedList()

    def report(self, message=None, exception=None, location=None, line=None,
               column=None, locator=None, snippet=None, level=Issue.PLATFORM, issue=None):
        if issue is None:
            issue = Issue(message, exception, location, line, column, locator, snippet, level)

        # Avoid duplicate issues
        with self._issues:
            for i in self._issues:
                if str(i) == str(issue):
                    return

            self._issues.append(issue)

    @property
    def has_issues(self):
        return len(self._issues) > 0

    @property
    def issues(self):
        issues = [i for i in self._issues if i.level <= self.max_level]
        issues.sort(key=lambda i: (i.level, i.location, i.line, i.column, i.message))
        return FrozenList(issues)

    @property
    def issues_as_raw(self):
        return [as_raw(i) for i in self.issues]

    def dump_issues(self):
        issues = self.issues
        if issues:
            puts(Colored.blue('Validation issues:', bold=True))
            with indent(2):
                for issue in issues:
                    puts(Colored.blue(issue.heading_as_str))
                    details = issue.details_as_str
                    if details:
                        with indent(3):
                            puts(details)
                    if issue.exception is not None:
                        with indent(3):
                            print_exception(issue.exception)
            return True
        return False
