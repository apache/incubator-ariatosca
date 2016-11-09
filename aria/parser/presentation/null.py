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

from ..utils import deepcopy_with_locators


class Null(object):
    """
    Represents an explicit null value provided by the user, which is different from
    not supplying a value at all.

    It is a singleton.
    """

    @property
    def as_raw(self):
        return None

NULL = Null()


def none_to_null(value):
    """
    Convert :code:`None` to :code:`NULL`, recursively.
    """

    if value is None:
        return NULL
    if isinstance(value, list):
        value = deepcopy_with_locators(value)
        for i, _ in enumerate(value):
            value[i] = none_to_null(value[i])
    elif isinstance(value, dict):
        value = deepcopy_with_locators(value)
        for k, v in value.iteritems():
            value[k] = none_to_null(v)
    return value


def null_to_none(value):
    """
    Convert :code:`NULL` to :code:`None`, recursively.
    """

    if value is NULL:
        return None
    if isinstance(value, list):
        value = deepcopy_with_locators(value)
        for i, _ in enumerate(value):
            value[i] = none_to_null(value[i])
    elif isinstance(value, dict):
        value = deepcopy_with_locators(value)
        for k, v in value.iteritems():
            value[k] = none_to_null(v)
    return value
