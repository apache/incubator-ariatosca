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
UUID generation utilities.
"""

from __future__ import absolute_import  # so we can import standard 'uuid'

from random import randrange
from uuid import uuid4

from shortuuid import ShortUUID


# Alphanumeric without visually ambiguous characters; default length is 22
UUID_BASE57 = ShortUUID()

# Lower-case alphanumeric; default length is 25
UUID_LOWERCASE_ALPHANUMERIC = ShortUUID(alphabet='abcdefghijklmnopqrstuvwxyz0123456789')


def generate_uuid(length=None, variant='base57'):
    """
    A random string with varying degrees of guarantee of universal uniqueness.

    :param variant:
     * ``base57`` (the default) uses a mix of upper and lowercase alphanumerics ensuring no visually
       ambiguous characters; default length 22
     * ``alphanumeric`` uses lowercase alphanumeric; default length 25
     * ``uuid`` uses lowercase hexadecimal in the classic UUID format, including dashes; length is
       always 36
     * ``hex`` uses lowercase hexadecimal characters but has no guarantee of uniqueness; default
       length of 5
    """

    if variant == 'base57':
        the_id = UUID_BASE57.uuid()
        if length is not None:
            the_id = the_id[:length]

    elif variant == 'alphanumeric':
        the_id = UUID_LOWERCASE_ALPHANUMERIC.uuid()
        if length is not None:
            the_id = the_id[:length]

    elif variant == 'uuid':
        the_id = str(uuid4())

    elif variant == 'hex':
        length = length or 5
        # See: http://stackoverflow.com/a/2782859
        the_id = ('%0' + str(length) + 'x') % randrange(16 ** length)

    else:
        raise ValueError('unsupported UUID variant: {0}'.format(variant))

    return the_id
