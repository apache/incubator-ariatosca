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

from functools import partial

from aria.modeling import models


class _InstrumentedCollection(object):

    def __init__(self,
                 model,
                 parent,
                 field_name,
                 seq=None,
                 is_top_level=True,
                 **kwargs):
        self._model = model
        self._parent = parent
        self._field_name = field_name
        self._is_top_level = is_top_level
        self._load(seq, **kwargs)

    @property
    def _raw(self):
        raise NotImplementedError

    def _load(self, seq, **kwargs):
        """
        Instantiates the object from existing seq.

        :param seq: the original sequence to load from
        :return:
        """
        raise NotImplementedError

    def _set(self, key, value):
        """
        set the changes for the current object (not in the db)

        :param key:
        :param value:
        :return:
        """
        raise NotImplementedError

    def _del(self, collection, key):
        raise NotImplementedError

    def _instrument(self, key, value):
        """
        Instruments any collection to track changes (and ease of access)
        :param key:
        :param value:
        :return:
        """
        if isinstance(value, _InstrumentedCollection):
            return value
        elif isinstance(value, dict):
            instrumentation_cls = _InstrumentedDict
        elif isinstance(value, list):
            instrumentation_cls = _InstrumentedList
        else:
            return value

        return instrumentation_cls(self._model, self, key, value, False)

    @staticmethod
    def _raw_value(value):
        """
        Get the raw value.
        :param value:
        :return:
        """
        if isinstance(value, models.Attribute):
            return value.value
        return value

    @staticmethod
    def _encapsulate_value(key, value):
        """
        Create a new item cls if needed.
        :param key:
        :param value:
        :return:
        """
        if isinstance(value, models.Attribute):
            return value
        # If it is not wrapped
        return models.Attribute.wrap(key, value)

    def __setitem__(self, key, value):
        """
        Update the values in both the local and the db locations.
        :param key:
        :param value:
        :return:
        """
        self._set(key, value)
        if self._is_top_level:
            # We are at the top level
            field = getattr(self._parent, self._field_name)
            mapi = getattr(self._model, models.Attribute.__modelname__)
            value = self._set_field(field,
                                    key,
                                    value if key in field else self._encapsulate_value(key, value))
            mapi.update(value)
        else:
            # We are not at the top level
            self._set_field(self._parent, self._field_name, self)

    def _set_field(self, collection, key, value):
        """
        enables updating the current change in the ancestors
        :param collection: the collection to change
        :param key: the key for the specific field
        :param value: the new value
        :return:
        """
        if isinstance(value, _InstrumentedCollection):
            value = value._raw
        if key in collection and isinstance(collection[key], models.Attribute):
            if isinstance(collection[key], _InstrumentedCollection):
                self._del(collection, key)
            collection[key].value = value
        else:
            collection[key] = value
        return collection[key]

    def __deepcopy__(self, *args, **kwargs):
        return self._raw


class _InstrumentedDict(_InstrumentedCollection, dict):

    def _load(self, dict_=None, **kwargs):
        dict.__init__(
            self,
            tuple((key, self._raw_value(value)) for key, value in (dict_ or {}).items()),
            **kwargs)

    def update(self, dict_=None, **kwargs):
        dict_ = dict_ or {}
        for key, value in dict_.items():
            self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def __getitem__(self, key):
        return self._instrument(key, dict.__getitem__(self, key))

    def _set(self, key, value):
        dict.__setitem__(self, key, self._raw_value(value))

    @property
    def _raw(self):
        return dict(self)

    def _del(self, collection, key):
        del collection[key]


class _InstrumentedList(_InstrumentedCollection, list):

    def _load(self, list_=None, **kwargs):
        list.__init__(self, list(item for item in list_ or []))

    def append(self, value):
        self.insert(len(self), value)

    def insert(self, index, value):
        list.insert(self, index, self._raw_value(value))
        if self._is_top_level:
            field = getattr(self._parent, self._field_name)
            field.insert(index, self._encapsulate_value(index, value))
        else:
            self._parent[self._field_name] = self

    def __getitem__(self, key):
        return self._instrument(key, list.__getitem__(self, key))

    def _set(self, key, value):
        list.__setitem__(self, key, value)

    def _del(self, collection, key):
        del collection[key]

    @property
    def _raw(self):
        return list(self)


class _InstrumentedModel(object):

    def __init__(self, field_name, original_model, model_storage):
        super(_InstrumentedModel, self).__init__()
        self._field_name = field_name
        self._model_storage = model_storage
        self._original_model = original_model
        self._apply_instrumentation()

    def __getattr__(self, item):
        return getattr(self._original_model, item)

    def _apply_instrumentation(self):

        field = getattr(self._original_model, self._field_name)

        # Preserve the original value. e.g. original attributes would be located under
        # _attributes
        setattr(self, '_{0}'.format(self._field_name), field)

        # set instrumented value
        setattr(self, self._field_name, _InstrumentedDict(self._model_storage,
                                                          self._original_model,
                                                          self._field_name,
                                                          field))


def instrument_collection(field_name, func=None):
    if func is None:
        return partial(instrument_collection, field_name)

    def _wrapper(*args, **kwargs):
        original_model = func(*args, **kwargs)
        return type('Instrumented{0}'.format(original_model.__class__.__name__),
                    (_InstrumentedModel, ),
                    {})(field_name, original_model, args[0].model)

    return _wrapper
