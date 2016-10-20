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
Aria exceptions module
Every sub-package in Aria has a module with its exceptions.
aria.exceptions module conveniently collects all these exceptions for easier imports.
"""

from .workflows.exceptions import *     # pylint: disable=W0401, W0614


class AriaError(Exception):
    """
    General aria exception
    """
    pass


class StorageError(AriaError):
    """
    General storage exception
    """
    pass
