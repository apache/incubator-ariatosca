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


from ...extension import parser

from .exceptions import PresenterNotFoundError


class PresenterSource(object):
    """
    Base class for ARIA presenter sources.

    Presenter sources provide appropriate :class:`Presenter` classes for agnostic raw data.
    """

    def get_presenter(self, raw):  # pylint: disable=unused-argument,no-self-use
        raise PresenterNotFoundError('presenter not found')


class DefaultPresenterSource(PresenterSource):
    """
    The default ARIA presenter source supports TOSCA Simple Profile.
    """

    def __init__(self, classes=None):
        if classes is None:
            classes = parser.presenter_class()
        self.classes = classes

    def get_presenter(self, raw):
        for cls in self.classes:
            if cls.can_present(raw):
                return cls

        if 'tosca_definitions_version' in raw:
            if raw['tosca_definitions_version'] is None:
                raise PresenterNotFoundError("'tosca_definitions_version' is not specified")
            if not isinstance(raw['tosca_definitions_version'], basestring):
                raise PresenterNotFoundError("'tosca_definitions_version' is not a string")
            if not raw['tosca_definitions_version']:
                raise PresenterNotFoundError("'tosca_definitions_version' is not specified")
        return super(DefaultPresenterSource, self).get_presenter(raw)
