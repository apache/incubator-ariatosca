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
Aria's storage.structures module
Path: aria.storage.structures

models module holds aria's models.

classes:
    * Field - represents a single field.
    * IterField - represents an iterable field.
    * PointerField - represents a single pointer field.
    * IterPointerField - represents an iterable pointers field.
    * Model - abstract model implementation.
"""
import json
from itertools import count
from uuid import uuid4
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from .exceptions import StorageError
from ..logger import LoggerMixin
from ..utils.validation import ValidatorMixin

__all__ = (
    'uuid_generator',
    'Field',
    'IterField',
    'PointerField',
    'IterPointerField',
    'Model',
    'Storage',
)


def uuid_generator():
    """
    wrapper function which generates ids
    """
    return str(uuid4())


class Field(ValidatorMixin):
    """
    A single field implementation
    """
    NO_DEFAULT = 'NO_DEFAULT'

    try:
        # python 3 syntax
        _next_id = count().__next__
    except AttributeError:
        # python 2 syntax
        _next_id = count().next
    _ATTRIBUTE_NAME = '_cache_{0}'.format

    def __init__(
            self,
            type=None,
            choices=(),
            validation_func=None,
            default=NO_DEFAULT,
            **kwargs):
        """
        Simple field manager.

        :param type: possible type of the field.
        :param choices: a set of possible field values.
        :param default: default field value.
        :param kwargs: kwargs to be passed to next in line classes.
        """
        self.type = type
        self.choices = choices
        self.default = default
        self.validation_func = validation_func
        super(Field, self).__init__(**kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        field_name = self._field_name(instance)
        try:
            return getattr(instance, self._ATTRIBUTE_NAME(field_name))
        except AttributeError as exc:
            if self.default == self.NO_DEFAULT:
                raise AttributeError(
                    str(exc).replace(self._ATTRIBUTE_NAME(field_name), field_name))

        default_value = self.default() if callable(self.default) else self.default
        setattr(instance, self._ATTRIBUTE_NAME(field_name), default_value)
        return default_value

    def __set__(self, instance, value):
        field_name = self._field_name(instance)
        self.validate_value(field_name, value, instance)
        setattr(instance, self._ATTRIBUTE_NAME(field_name), value)

    def validate_value(self, name, value, instance):
        """
        Validates the value of the field.

        :param name: the name of the field.
        :param value: the value of the field.
        :param instance: the instance containing the field.
        """
        if self.default != self.NO_DEFAULT and value == self.default:
            return
        if self.type:
            self.validate_instance(name, value, self.type)
        if self.choices:
            self.validate_in_choice(name, value, self.choices)
        if self.validation_func:
            self.validation_func(name, value, instance)

    def _field_name(self, instance):
        """
        retrieves the field name from the instance.

        :param Field instance: the instance which holds the field.
        :return: name of the field
        :rtype: basestring
        """
        for name, member in vars(instance.__class__).iteritems():
            if member is self:
                return name


class IterField(Field):
    """
    Represents an iterable field.
    """
    def __init__(self, **kwargs):
        """
        Simple iterable field manager.
        This field type don't have choices option.

        :param kwargs: kwargs to be passed to next in line classes.
        """
        super(IterField, self).__init__(choices=(), **kwargs)

    def validate_value(self, name, values, *args):
        """
        Validates the value of each iterable value.

        :param name: the name of the field.
        :param values: the values of the field.
        """
        for value in values:
            self.validate_instance(name, value, self.type)


class PointerField(Field):
    """
    A single pointer field implementation.

    Any PointerField points via id to another document.
    """

    def __init__(self, type, **kwargs):
        assert issubclass(type, Model)
        super(PointerField, self).__init__(type=type, **kwargs)


class IterPointerField(IterField, PointerField):
    """
    An iterable pointers field.

    Any IterPointerField points via id to other documents.
    """
    pass


class Model(object):
    """
    Base class for all of the storage models.
    """
    id = None

    def __init__(self, **fields):
        """
        Abstract class for any model in the storage.
        The Initializer creates attributes according to the (keyword arguments) that given
        Each value is validated according to the Field.
        Each model has to have and ID Field.

        :param fields: each item is validated and transformed into instance attributes.
        """
        self._assert_model_have_id_field(**fields)
        missing_fields, unexpected_fields = self._setup_fields(fields)

        if missing_fields:
            raise StorageError(
                'Model {name} got missing keyword arguments: {fields}'.format(
                    name=self.__class__.__name__, fields=missing_fields))

        if unexpected_fields:
            raise StorageError(
                'Model {name} got unexpected keyword arguments: {fields}'.format(
                    name=self.__class__.__name__, fields=unexpected_fields))

    def __repr__(self):
        return '{name}(fields={0})'.format(sorted(self.fields), name=self.__class__.__name__)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.fields_dict == other.fields_dict)

    @property
    def fields(self):
        """
        Iterates over the fields of the model.
        :yields: the class's field name
        """
        for name, field in vars(self.__class__).items():
            if isinstance(field, Field):
                yield name

    @property
    def fields_dict(self):
        """
        Transforms the instance attributes into a dict.

        :return: all fields in dict format.
        :rtype dict
        """
        return self._fields_dict(self)

    def _fields_dict(self, obj):
        dict_to_return = {}
        for name in obj.fields:
            value = getattr(obj, name)
            if isinstance(value, Model) and isinstance(getattr(self.__class__, name), PointerField):
                dict_to_return[name] = self._fields_dict(value)
            else:
                dict_to_return[name] = value

        return dict_to_return.copy()

    @property
    def json(self):
        """
        Transform the dict of attributes into json
        :return:
        """
        return json.dumps(self.fields_dict)

    @classmethod
    def _assert_model_have_id_field(cls, **fields_initializer_values):
        if not getattr(cls, 'id', None):
            raise StorageError('Model {cls.__name__} must have id field'.format(cls=cls))

        if cls.id.default == cls.id.NO_DEFAULT and 'id' not in fields_initializer_values:
            raise StorageError(
                'Model {cls.__name__} is missing required '
                'keyword-only argument: "id"'.format(cls=cls))

    def _setup_fields(self, input_fields):
        missing = []
        for field_name in self.fields:
            try:
                field_value = input_fields.pop(field_name)
                field = getattr(self.__class__, field_name)
                field_obj = None
                if isinstance(field, IterPointerField):
                    if all(isinstance(item, Model) for item in field_value):
                        field_obj = field_value
                    else:
                        field_obj = [field.type(**field_dict) for field_dict in field_value]
                elif isinstance(field, PointerField):
                    if isinstance(field_value, Model):
                        field_obj = field_value
                    else:
                        field_obj = field.type(**field_value)

                setattr(self, field_name, field_obj or field_value)
            except KeyError:
                field = getattr(self.__class__, field_name)
                if field.default == field.NO_DEFAULT:
                    missing.append(field_name)

        unexpected_fields = input_fields.keys()
        return missing, unexpected_fields


class Storage(LoggerMixin):
    """
    Represents the storage
    """
    def __init__(self, driver, items=(), **kwargs):
        super(Storage, self).__init__(**kwargs)
        self._driver = driver
        self._registered = OrderedDict()
        for item in items:
            self.register(item)
        self.logger.debug('{name} object is ready: {0!r}'.format(
            self, name=self.__class__.__name__))

    def __repr__(self):
        return '{name}(driver={self._driver})'.format(
            name=self.__class__.__name__, self=self)

    def __getattr__(self, item):
        try:
            return self._registered[item]
        except KeyError:
            return super(Storage, self).__getattribute__(item)

    def setup(self):
        """
        Setup and create all storage items
        """
        for name, api in self._registered.items():
            try:
                api.create()
                self.logger.debug(
                    'setup {name} in storage {self!r}'.format(name=name, self=self))
            except StorageError:
                pass
