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

from aria.utils.caching import cachedmethod
from aria.parser.presentation import (Presentation, has_fields, primitive_dict_field)

@has_fields
class ExtensiblePresentation(Presentation):
    """
    A presentation that supports an optional ``_extensions`` dict field.
    """

    @primitive_dict_field()
    def _extensions(self):
        pass

    @cachedmethod
    def _get_extension(self, name, default=None):
        extensions = self._extensions
        return extensions.get(name, default) if extensions is not None else None # pylint: disable=no-member
