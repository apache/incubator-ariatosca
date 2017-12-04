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

from aria.utils.formatting import safe_repr
from aria.utils.type import full_type_name
from aria.parser.exceptions import InvalidValueError
from aria.parser.presentation import NULL


def data_type_class_getter(cls, allow_null=False):
    """
    Wraps the field value in a specialized data type class.

    Can be used with the :func:`field_getter` decorator.
    """

    def getter(field, presentation, context=None):
        raw = field.default_get(presentation, context)
        if (raw is None) or (allow_null and (raw is NULL)):
            return raw
        try:
            return cls(None, None, raw, None)
        except ValueError as e:
            raise InvalidValueError(
                u'{0} is not a valid "{1}" in "{2}": {3}'
                .format(field.full_name, full_type_name(cls), presentation._name,
                        safe_repr(raw)),
                cause=e, locator=field.get_locator(raw))
    return getter
