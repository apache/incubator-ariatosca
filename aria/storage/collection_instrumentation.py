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

from . import exceptions


class _InstrumentedCollection(object):

    def __init__(self,
                 mapi,
                 parent,
                 field_name,
                 field_cls,
                 seq=None,
                 is_top_level=True,
                 **kwargs):
        self._mapi = mapi
        self._parent = parent
        self._field_name = field_name
        self._is_top_level = is_top_level
        self._field_cls = field_cls
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

        return instrumentation_cls(self._mapi, self, key, self._field_cls, value, False)

    def _raw_value(self, value):
        """
        Get the raw value.
        :param value:
        :return:
        """
        if isinstance(value, self._field_cls):
            return value.value
        return value

    def _encapsulate_value(self, key, value):
        """
        Create a new item cls if needed.
        :param key:
        :param value:
        :return:
        """
        if isinstance(value, self._field_cls):
            return value
        # If it is not wrapped
        return self._field_cls.wrap(key, value)

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
            self._set_field(
                field, key, value if key in field else self._encapsulate_value(key, value))
            self._mapi.update(self._parent)
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
        if key in collection and isinstance(collection[key], self._field_cls):
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

    def __init__(self, original_model, mapi, instrumentation):
        """
        The original model
        :param original_model: the model to be instrumented
        :param mapi: the mapi for that model
        """
        super(_InstrumentedModel, self).__init__()
        self._original_model = original_model
        self._mapi = mapi
        self._instrumentation = instrumentation
        self._apply_instrumentation()

    def __getattr__(self, item):
        return_value = getattr(self._original_model, item)
        if isinstance(return_value, self._original_model.__class__):
            return _create_instrumented_model(return_value, self._mapi, self._instrumentation)
        if isinstance(return_value, (list, dict)):
            return _create_wrapped_model(return_value, self._mapi, self._instrumentation)
        return return_value

    def _apply_instrumentation(self):
        for field in self._instrumentation:
            field_name = field.key
            field_cls = field.mapper.class_
            field = getattr(self._original_model, field_name)

            # Preserve the original value. e.g. original attributes would be located under
            # _attributes
            setattr(self, '_{0}'.format(field_name), field)

            # set instrumented value
            if isinstance(field, dict):
                instrumentation_cls = _InstrumentedDict
            elif isinstance(field, list):
                instrumentation_cls = _InstrumentedList
            else:
                # TODO: raise proper error
                raise exceptions.StorageError(
                    "ARIA supports instrumentation for dict and list. Field {field} of the "
                    "class {model} is of {type} type.".format(
                        field=field,
                        model=self._original_model,
                        type=type(field)))

            instrumented_class = instrumentation_cls(seq=field,
                                                     parent=self._original_model,
                                                     mapi=self._mapi,
                                                     field_name=field_name,
                                                     field_cls=field_cls)
            setattr(self, field_name, instrumented_class)


class _WrappedModel(object):

    def __init__(self, wrapped, instrumentation, **kwargs):
        """

        :param instrumented_cls: The class to be instrumented
        :param instrumentation_cls: the instrumentation cls
        :param wrapped: the currently wrapped instance
        :param kwargs: and kwargs to the passed to the instrumented class.
        """
        self._kwargs = kwargs
        self._instrumentation = instrumentation
        self._wrapped = wrapped

    def _wrap(self, value):
        if value.__class__ in (class_.class_ for class_ in self._instrumentation):
            return _create_instrumented_model(
                value, instrumentation=self._instrumentation, **self._kwargs)
        elif hasattr(value, 'metadata') or isinstance(value, (dict, list)):
            # Basically checks that the value is indeed an sqlmodel (it should have metadata)
            return _create_wrapped_model(
                value, instrumentation=self._instrumentation, **self._kwargs)
        return value

    def __getattr__(self, item):
        if hasattr(self, '_wrapped'):
            return self._wrap(getattr(self._wrapped, item))
        else:
            super(_WrappedModel, self).__getattribute__(item)

    def __getitem__(self, item):
        return self._wrap(self._wrapped[item])


def _create_instrumented_model(original_model, mapi, instrumentation, **kwargs):
    return type('Instrumented{0}'.format(original_model.__class__.__name__),
                (_InstrumentedModel,),
                {})(original_model, mapi, instrumentation, **kwargs)


def _create_wrapped_model(original_model, mapi, instrumentation, **kwargs):
    return type('Wrapped{0}'.format(original_model.__class__.__name__),
                (_WrappedModel, ),
                {})(original_model, instrumentation, mapi=mapi, **kwargs)


def instrument(instrumentation, original_model, mapi):
    for instrumented_field in instrumentation:
        if isinstance(original_model, instrumented_field.class_):
            return _create_instrumented_model(original_model, mapi, instrumentation)

    return _create_wrapped_model(original_model, mapi, instrumentation)
