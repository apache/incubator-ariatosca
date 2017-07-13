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
Abstraction API above terminal color libraries.
"""

import os
import sys
from StringIO import StringIO

from contextlib import contextmanager

from ..cli import color
from . import formatting


_indent_string = ''


class TopologyStylizer(object):
    def __init__(self, indentation=0):
        self._str = StringIO()
        self._indentation = indentation

    def write(self, string):
        self._str.write(' ' * self._indentation)
        self._str.write(string)
        self._str.write(os.linesep)

    @contextmanager
    def indent(self, indentation=2):
        self._indentation += indentation
        yield
        self._indentation -= indentation

    @staticmethod
    def type_style(value):
        return Colored.blue(value, bold=True)

    @staticmethod
    def node_style(value):
        return Colored.red(value, bold=True)

    @staticmethod
    def property_style(value):
        return Colored.magenta(value, bold=True)

    @staticmethod
    def literal_style(value):
        return Colored.magenta(formatting.safe_repr(value))

    @staticmethod
    def required_style(value):
        return Colored.white(value)

    @staticmethod
    def meta_style(value):
        return Colored.green(value)

    def __str__(self):
        return self._str.getvalue()


def puts(string='', newline=True, stream=sys.stdout):
    stream.write(_indent_string)
    stream.write(formatting.safe_str(string))
    if newline:
        stream.write(os.linesep)


@contextmanager
def indent(size=4):
    global _indent_string
    original_indent_string = _indent_string
    try:
        _indent_string += ' ' * size
        yield
    finally:
        _indent_string = original_indent_string


class Colored(object):
    @staticmethod
    def black(string, always=False, bold=False):
        return Colored._color(string, color.Colors.Fore.BLACK, bold)

    @staticmethod
    def red(string, always=False, bold=False):
        return Colored._color(string, color.Colors.Fore.RED, bold)

    @staticmethod
    def green(string, always=False, bold=False):
        return Colored._color(string, color.Colors.Fore.GREEN, bold)

    @staticmethod
    def yellow(string, always=False, bold=False):
        return Colored._color(string, color.Colors.Fore.YELLOW, bold)

    @staticmethod
    def blue(string, always=False, bold=False):
        return Colored._color(string, color.Colors.Fore.BLUE, bold)

    @staticmethod
    def magenta(string, always=False, bold=False):
        return Colored._color(string, color.Colors.Fore.MAGENTA, bold)

    @staticmethod
    def cyan(string, always=False, bold=False):
        return Colored._color(string, color.Colors.Fore.CYAN, bold)

    @staticmethod
    def white(string, always=False, bold=False):
        return Colored._color(string, color.Colors.Fore.WHITE, bold)

    @staticmethod
    def _color(string, fore, bold):
        return color.StringStylizer(string, color.ColorSpec(
            fore=fore,
            style=color.Colors.Style.BRIGHT if bold else color.Colors.Style.NORMAL))
