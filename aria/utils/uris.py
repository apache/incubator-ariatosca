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
URI utilities.
"""

import os
import urlparse


_IS_WINDOWS = (os.name == 'nt')


def as_file(uri):
    """
    If the URI is a file (either the ``file`` scheme or no scheme), then returns the normalized
    path. Otherwise, returns ``None``.
    """

    if _IS_WINDOWS:
        # We need this extra check in Windows before urlparse because paths might have a drive
        # prefix, e.g. "C:" which will be considered a scheme for urlparse below
        path = uri.replace('/', '\\')
        if os.path.exists(path):
            return os.path.normpath(path)

    url = urlparse.urlparse(uri)
    scheme = url.scheme
    if (not scheme) or (scheme == 'file'):
        path = url.path
        if _IS_WINDOWS:
            path = path.replace('/', '\\')
        return os.path.realpath(path)

    return None
