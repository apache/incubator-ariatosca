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
from collections import namedtuple

from sqlalchemy import (
    TypeDecorator,
    VARCHAR,
    event
)
from sqlalchemy.ext import mutable

from .. import exceptions


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


class _StrictDictMixin(object):

    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."
        try:
            if not isinstance(value, cls):
                if isinstance(value, dict):
                    for k, v in value.items():
                        cls._assert_strict_key(k)
                        cls._assert_strict_value(v)
                    return cls(value)
                return mutable.MutableDict.coerce(key, value)
            else:
                return value
        except ValueError as e:
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))

    def __setitem__(self, key, value):
        self._assert_strict_key(key)
        self._assert_strict_value(value)
        super(_StrictDictMixin, self).__setitem__(key, value)

    def setdefault(self, key, value):
        self._assert_strict_key(key)
        self._assert_strict_value(value)
        super(_StrictDictMixin, self).setdefault(key, value)

    def update(self, *args, **kwargs):
        for k, v in kwargs.items():
            self._assert_strict_key(k)
            self._assert_strict_value(v)
        super(_StrictDictMixin, self).update(*args, **kwargs)

    @classmethod
    def _assert_strict_key(cls, key):
        if cls._key_cls is not None and not isinstance(key, cls._key_cls):
            raise exceptions.StorageError("Key type was set strictly to {0}, but was {1}".format(
                cls._key_cls, type(key)
            ))

    @classmethod
    def _assert_strict_value(cls, value):
        if cls._value_cls is not None and not isinstance(value, cls._value_cls):
            raise exceptions.StorageError("Value type was set strictly to {0}, but was {1}".format(
                cls._value_cls, type(value)
            ))


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


class _StrictListMixin(object):

    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."
        try:
            if not isinstance(value, cls):
                if isinstance(value, list):
                    for item in value:
                        cls._assert_item(item)
                    return cls(value)
                return mutable.MutableList.coerce(key, value)
            else:
                return value
        except ValueError as e:
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))

    def __setitem__(self, index, value):
        """Detect list set events and emit change events."""
        self._assert_item(value)
        super(_StrictListMixin, self).__setitem__(index, value)

    def append(self, item):
        self._assert_item(item)
        super(_StrictListMixin, self).append(item)

    def extend(self, item):
        self._assert_item(item)
        super(_StrictListMixin, self).extend(item)

    def insert(self, index, item):
        self._assert_item(item)
        super(_StrictListMixin, self).insert(index, item)

    @classmethod
    def _assert_item(cls, item):
        if cls._item_cls is not None and not isinstance(item, cls._item_cls):
            raise exceptions.StorageError("Key type was set strictly to {0}, but was {1}".format(
                cls._item_cls, type(item)
            ))


class _MutableList(mutable.MutableList):

    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."
        try:
            return mutable.MutableList.coerce(key, value)
        except ValueError as e:
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))

_StrictDictID = namedtuple('_StrictDictID', 'key_cls, value_cls')
_StrictValue = namedtuple('_StrictValue', 'type_cls, listener_cls')


class _StrictDict(object):
    """
    This entire class functions as a factory for strict dicts and their listeners.
    No type class, and no listener type class is created more than once. If a relevant type class
    exists it is returned.
    """
    _strict_map = {}

    def __call__(self, key_cls=None, value_cls=None):
        strict_dict_map_key = _StrictDictID(key_cls=key_cls, value_cls=value_cls)
        if strict_dict_map_key not in self._strict_map:
            key_cls_name = getattr(key_cls, '__name__', str(key_cls))
            value_cls_name = getattr(value_cls, '__name__', str(value_cls))
            # Creating the type class itself. this class would be returned (used by the sqlalchemy
            # Column).
            strict_dict_cls = type(
                'StrictDict_{0}_{1}'.format(key_cls_name, value_cls_name),
                (Dict, ),
                {}
            )
            # Creating the type listening class.
            # The new class inherits from both the _MutableDict class and the _StrictDictMixin,
            # while setting the necessary _key_cls and _value_cls as class attributes.
            listener_cls = type(
                'StrictMutableDict_{0}_{1}'.format(key_cls_name, value_cls_name),
                (_StrictDictMixin, _MutableDict),
                {'_key_cls': key_cls, '_value_cls': value_cls}
            )
            self._strict_map[strict_dict_map_key] = _StrictValue(type_cls=strict_dict_cls,
                                                                 listener_cls=listener_cls)

        return self._strict_map[strict_dict_map_key].type_cls

StrictDict = _StrictDict()


class _StrictList(object):
    """
    This entire class functions as a factory for strict lists and their listeners.
    No type class, and no listener type class is created more than once. If a relevant type class
    exists it is returned.
    """
    _strict_map = {}

    def __call__(self, item_cls=None):

        if item_cls not in self._strict_map:
            item_cls_name = getattr(item_cls, '__name__', str(item_cls))
            # Creating the type class itself. this class would be returned (used by the sqlalchemy
            # Column).
            strict_list_cls = type(
                'StrictList_{0}'.format(item_cls_name),
                (List, ),
                {}
            )
            # Creating the type listening class.
            # The new class inherits from both the _MutableList class and the _StrictListMixin,
            # while setting the necessary _item_cls as class attribute.
            listener_cls = type(
                'StrictMutableList_{0}'.format(item_cls_name),
                (_StrictListMixin, _MutableList),
                {'_item_cls': item_cls}
            )
            self._strict_map[item_cls] = _StrictValue(type_cls=strict_list_cls,
                                                      listener_cls=listener_cls)

        return self._strict_map[item_cls].type_cls

StrictList = _StrictList()


def _mutable_association_listener(mapper, cls):
    strict_dict_type_to_listener = \
        dict((v.type_cls, v.listener_cls) for v in _StrictDict._strict_map.values())

    strict_list_type_to_listener = \
        dict((v.type_cls, v.listener_cls) for v in _StrictList._strict_map.values())

    for prop in mapper.column_attrs:
        column_type = prop.columns[0].type
        # Dict Listeners
        if type(column_type) in strict_dict_type_to_listener:                                       # pylint: disable=unidiomatic-typecheck
            strict_dict_type_to_listener[type(column_type)].associate_with_attribute(
                getattr(cls, prop.key))
        elif isinstance(column_type, Dict):
            _MutableDict.associate_with_attribute(getattr(cls, prop.key))

        # List Listeners
        if type(column_type) in strict_list_type_to_listener:                                       # pylint: disable=unidiomatic-typecheck
            strict_list_type_to_listener[type(column_type)].associate_with_attribute(
                getattr(cls, prop.key))
        elif isinstance(column_type, List):
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
