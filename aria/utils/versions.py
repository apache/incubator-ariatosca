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
General-purpose version string handling
"""

import re


_INF = float('inf')

_NULL = (), _INF

_DIGITS_RE = re.compile(r'^\d+$')

_PREFIXES = {
    'dev':   0.0001,
    'alpha': 0.001,
    'beta':  0.01,
    'rc':    0.1
}


class VersionString(unicode):
    """
    Version string that can be compared, sorted, made unique in a set, and used as a unique dict
    key.

    The primary part of the string is one or more dot-separated natural numbers. Trailing zeroes
    are treated as redundant, e.g. "1.0.0" == "1.0" == "1".

    An optional qualifier can be added after a "-". The qualifier can be a natural number or a
    specially treated prefixed natural number, e.g. "1.1-beta1" > "1.1-alpha2". The case of the
    prefix is ignored.

    Numeric qualifiers will always be greater than prefixed integer qualifiers, e.g. "1.1-1" >
    "1.1-beta1".

    Versions without a qualifier will always be greater than their equivalents with a qualifier,
    e.g. e.g. "1.1" > "1.1-1".

    Any value that does not conform to this format will be treated as a zero version, which would
    be lesser than any non-zero version.

    For efficient list sorts use the ``key`` property, e.g.:
    ``sorted(versions, key=lambda x: x.key)``
    """

    NULL = None # initialized below

    def __init__(self, value=None):
        if value is not None:
            super(VersionString, self).__init__(value)
        self.key = parse_version_string(self)

    def __eq__(self, version):
        if not isinstance(version, VersionString):
            version = VersionString(version)
        return self.key == version.key

    def __lt__(self, version):
        if not isinstance(version, VersionString):
            version = VersionString(version)
        return self.key < version.key

    def __hash__(self):
        return self.key.__hash__()


def parse_version_string(version): # pylint: disable=too-many-branches
    """
    Parses a version string.

    :param version: The version string
    :returns: The primary tuple and qualifier float
    :rtype: ((int), float)
    """

    if version is None:
        return _NULL
    version = unicode(version)

    # Split to primary and qualifier on '-'
    split = version.split('-', 1)
    if len(split) == 2:
        primary, qualifier = split
    else:
        primary = split[0]
        qualifier = None

    # Parse primary
    split = primary.split('.')
    primary = []
    for element in split:
        if _DIGITS_RE.match(element) is None:
            # Invalid version string
            return _NULL
        try:
            element = int(element)
        except ValueError:
            # Invalid version string
            return _NULL
        primary.append(element)

    # Remove redundant zeros
    for element in reversed(primary):
        if element == 0:
            primary.pop()
        else:
            break
    primary = tuple(primary)

    # Parse qualifier
    if qualifier is not None:
        if _DIGITS_RE.match(qualifier) is not None:
            # Integer qualifier
            try:
                qualifier = float(int(qualifier))
            except ValueError:
                # Invalid version string
                return _NULL
        else:
            # Prefixed integer qualifier
            value = None
            qualifier = qualifier.lower()
            for prefix, factor in _PREFIXES.iteritems():
                if qualifier.startswith(prefix):
                    value = qualifier[len(prefix):]
                    if _DIGITS_RE.match(value) is None:
                        # Invalid version string
                        return _NULL
                    try:
                        value = float(int(value)) * factor
                    except ValueError:
                        # Invalid version string
                        return _NULL
                    break
            if value is None:
                # Invalid version string
                return _NULL
            qualifier = value
    else:
        # Version strings with no qualifiers are higher
        qualifier = _INF

    return primary, qualifier


VersionString.NULL = VersionString()
