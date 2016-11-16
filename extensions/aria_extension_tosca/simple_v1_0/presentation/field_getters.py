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
from aria.parser import InvalidValueError


def data_type_class_getter(cls):
    """
    Wraps the field value in a specialized data type class.

    Can be used with the :func:`field_getter` decorator.
    """

    def getter(field, presentation, context=None):
        raw = field.default_get(presentation, context)
        if raw is not None:
            try:
                return cls(None, None, raw, None)
            except ValueError as e:
                raise InvalidValueError(
                    '%s is not a valid "%s" in "%s": %s'
                    % (field.full_name, field.full_cls_name, presentation._name, safe_repr(raw)),
                    cause=e, locator=field.get_locator(raw))
    return getter
