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
Utilities for working with open/close patterns.
"""

class OpenClose(object):
    """
    Wraps an object that has ``open()`` and ``close()`` methods to support the ``with`` keyword.
    """

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __enter__(self):
        if hasattr(self.wrapped, 'open'):
            self.wrapped.open()
        return self.wrapped

    def __exit__(self, the_type, value, traceback):
        if hasattr(self.wrapped, 'close'):
            self.wrapped.close()
        return False
