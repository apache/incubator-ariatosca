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
import json

from sqlalchemy import (
    TypeDecorator,
    VARCHAR,
    event
)

from sqlalchemy.ext import mutable

from . import exceptions


class _MutableType(TypeDecorator):
    """
    Dict representation of type.
    """
    @property
    def python_type(self):
        raise NotImplementedError

    def process_literal_param(self, value, dialect):
        pass

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class Dict(_MutableType):
    @property
    def python_type(self):
        return dict


class List(_MutableType):
    @property
    def python_type(self):
        return list


class _MutableDict(mutable.MutableDict):
    """
    Enables tracking for dict values.
    """
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."
        try:
            return mutable.MutableDict.coerce(key, value)
        except ValueError as e:
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))


class _MutableList(mutable.MutableList):

    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."
        try:
            return mutable.MutableList.coerce(key, value)
        except ValueError as e:
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))


def _mutable_association_listener(mapper, cls):
    for prop in mapper.column_attrs:
        column_type = prop.columns[0].type
        if isinstance(column_type, Dict):
            _MutableDict.associate_with_attribute(getattr(cls, prop.key))
        if isinstance(column_type, List):
            _MutableList.associate_with_attribute(getattr(cls, prop.key))
_LISTENER_ARGS = (mutable.mapper, 'mapper_configured', _mutable_association_listener)


def _register_mutable_association_listener():
    event.listen(*_LISTENER_ARGS)


def remove_mutable_association_listener():
    """
    Remove the event listener that associates ``Dict`` and ``List`` column types with
    ``MutableDict`` and ``MutableList``, respectively.

    This call must happen before any model instance is instantiated.
    This is because once it does, that would trigger the listener we are trying to remove.
    Once it is triggered, many other listeners will then be registered.
    At that point, it is too late.

    The reason this function exists is that the association listener, interferes with ARIA change
    tracking instrumentation, so a way to disable it is required.

    Note that the event listener this call removes is registered by default.
    """
    if event.contains(*_LISTENER_ARGS):
        event.remove(*_LISTENER_ARGS)

_register_mutable_association_listener()
