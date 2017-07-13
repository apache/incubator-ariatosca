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

from __future__ import absolute_import  # so we can import standard 'collections'

from ...utils import (
    collections,
    type,
    threading,
    exceptions,
    console,
    formatting
)


class Issue(object):
    PLATFORM = 0
    """
    Platform error (e.g. I/O, hardware, a bug in ARIA)
    """

    SYNTAX = 1
    """
    Syntax and format (e.g. YAML, XML, JSON)
    """

    FIELD = 2
    """
    Single field
    """

    BETWEEN_FIELDS = 3
    """
    Relationships between fields within the type (internal grammar)
    """

    BETWEEN_TYPES = 4
    """
    Relationships between types (e.g. inheritance, external grammar)
    """

    BETWEEN_INSTANCES = 5
    """
    Topology (e.g. static requirements and capabilities)
    """

    EXTERNAL = 6
    """
    External (e.g. live requirements and capabilities)
    """

    ALL = 100

    def __init__(self, message=None, exception=None, location=None, line=None,
                 column=None, locator=None, snippet=None, level=0):
        if message is not None:
            self.message = str(message)
        elif exception is not None:
            self.message = str(exception)
        else:
            self.message = 'unknown issue'

        self.exception = exception

        if locator is not None:
            self.location = locator.location
            self.line = locator.line
            self.column = locator.column
        else:
            self.location = location
            self.line = line
            self.column = column

        self.snippet = snippet
        self.level = level

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('level', self.level),
            ('message', self.message),
            ('location', self.location),
            ('line', self.line),
            ('column', self.column),
            ('snippet', self.snippet),
            ('exception', type.full_type_name(self.exception) if self.exception else None)))

    @property
    def locator_as_str(self):
        if self.location is not None:
            if self.line is not None:
                if self.column is not None:
                    return '"%s":%d:%d' % (self.location, self.line, self.column)
                else:
                    return '"%s":%d' % (self.location, self.line)
            else:
                return '"%s"' % self.location
        else:
            return None

    @property
    def heading_as_str(self):
        return '%d: %s' % (self.level, self.message)

    @property
    def details_as_str(self):
        details_str = ''
        locator = self.locator_as_str
        if locator is not None:
            details_str += '@%s' % locator
        if self.snippet is not None:
            details_str += '\n%s' % self.snippet
        return details_str

    def __str__(self):
        heading_str = self.heading_as_str
        details = self.details_as_str
        if details:
            heading_str += ', ' + details
        return heading_str


class ReporterMixin(object):

    Issue = Issue

    def __init__(self, *args, **kwargs):
        super(ReporterMixin, self).__init__(*args, **kwargs)
        self._issues = threading.LockedList()
        self.max_level = self.Issue.ALL

    def report(self, message=None, exception=None, location=None, line=None,
               column=None, locator=None, snippet=None, level=Issue.PLATFORM, issue=None):
        if issue is None:
            issue = self.Issue(message, exception, location, line, column, locator, snippet, level)

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
        return collections.FrozenList(issues)

    @property
    def issues_as_raw(self):
        return [formatting.as_raw(i) for i in self.issues]

    def extend_issues(self, *issues):
        with self._issues:
            self._issues.extend(*issues)

    def dump_issues(self):
        issues = self.issues
        if issues:
            console.puts(console.Colored.blue('Validation issues:', bold=True))
            with console.indent(2):
                for issue in issues:
                    console.puts(console.Colored.blue(issue.heading_as_str))
                    details = issue.details_as_str
                    if details:
                        with console.indent(3):
                            console.puts(details)
                    if issue.exception is not None:
                        with console.indent(3):
                            exceptions.print_exception(issue.exception)
            return True
        return False
