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

from contextlib import contextmanager

from .formatting import safe_str
from ..cli import color


_indent_string = ''


def puts(string='', newline=True, stream=sys.stdout):
    stream.write(_indent_string)
    stream.write(safe_str(string))
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
