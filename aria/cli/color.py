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
from StringIO import StringIO
import re

import colorama

colorama.init()


class StringStylizer(object):
    def __init__(self, str_, color_spec=None):
        self._str = str_
        self._color_spec = color_spec

    def __repr__(self):
        if self._color_spec:
            return '{schema}{str}{reset}'.format(
                schema=self._color_spec, str=str(self._str), reset=Colors.Style.RESET_ALL)
        return self._str

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    def color(self, color_spec):
        self._color_spec = color_spec

    def replace(self, old, new, **kwargs):
        self._str = self._str.replace(str(old), str(new), **kwargs)

    def format(self, *args, **kwargs):
        self._str = self._str.format(*args, **kwargs)

    def highlight(self, pattern, schema):
        if pattern is None:
            return
        for match in set(re.findall(re.compile(pattern), self._str)):
            self.replace(match, schema + match + Colors.Style.RESET_ALL + self._color_spec)


def _get_colors(color_type):
    for name in dir(color_type):
        if not name.startswith('_'):
            yield (name.lower(), getattr(color_type, name))


class Colors(object):
    Fore = colorama.Fore
    Back = colorama.Back
    Style = colorama.Style

    _colors = {
        'fore': dict(_get_colors(Fore)),
        'back': dict(_get_colors(Back)),
        'style': dict(_get_colors(Style))
    }


class ColorSpec(object):
    def __init__(self, fore=None, back=None, style=None):
        """
        It is possible to provide fore, back and style arguments. each could be either
        the color is lower case letter, or the actual color from colorama.

        """
        self._kwargs = dict(fore=fore, back=back, style=style)
        self._str = StringIO()
        for type_, colors in Colors._colors.items():
            value = self._kwargs.get(type_, None)
            # the former case is if the value is a string, the latter is in case of an object.
            self._str.write(colors.get(value) or value)

    def __str__(self):
        return self._str.getvalue()

    def __add__(self, other):
        return str(self) + str(other)

    def __radd__(self, other):
        return str(other) + str(self)
