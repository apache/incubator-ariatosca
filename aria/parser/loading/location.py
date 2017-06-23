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


import os

from ...utils.uris import as_file


class Location(object):
    """
    Base class for ARIA locations.

    Locations are used by :class:`~aria.parser.loading.LoaderSource` to delegate to
    an appropriate :class:`~aria.parser.loading.Loader`.
    """

    def is_equivalent(self, location):
        raise NotImplementedError

    @property
    def prefix(self):
        return None


class UriLocation(Location):
    """
    A URI location can be absolute or relative, and can include a scheme or not.

    If no scheme is included, it should be treated as a filesystem path.

    See :class:`~aria.parser.loading.UriTextLoader`.
    """

    def __init__(self, uri):
        self.uri = uri

    def is_equivalent(self, location):
        return isinstance(location, UriLocation) and (location.uri == self.uri)

    @property
    def prefix(self):
        prefix = os.path.dirname(self.uri)
        if prefix and (as_file(prefix) is None):
            # Yes, it's weird, but dirname handles URIs,
            # too: http://stackoverflow.com/a/35616478/849021
            # We just need to massage it with a trailing slash
            prefix += '/'
        return prefix

    def __str__(self):
        return self.uri


class LiteralLocation(Location):
    """
    A location that embeds content.

    See :class:`~aria.parser.loading.LiteralLoader`.
    """

    def __init__(self, content, name='literal'):
        self.content = content
        self.name = name

    def is_equivalent(self, location):
        return isinstance(location, LiteralLocation) and (location.content == self.content)

    def __str__(self):
        return '<%s>' % self.name
