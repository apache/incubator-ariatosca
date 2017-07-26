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

from ...utils.console import Colored, indent
from ...utils.formatting import safe_repr


class Style(object):
    def __init__(self, indentation=2):
        self.indentation = indentation

    @property
    def indent(self):
        return indent(self.indentation)

    @staticmethod
    def section(value):
        return Colored.cyan(value, bold=True)

    @staticmethod
    def type(value):
        return Colored.blue(value, bold=True)

    @staticmethod
    def node(value):
        return Colored.red(value, bold=True)

    @staticmethod
    def property(value):
        return Colored.magenta(value, bold=True)

    @staticmethod
    def literal(value):
        return Colored.magenta(safe_repr(value))

    @staticmethod
    def meta(value):
        return Colored.green(value)

    @staticmethod
    def required(value):
        return Colored.white(value)
