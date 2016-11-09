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

import threading
from functools import wraps
from types import MethodType
from collections import OrderedDict

from ..exceptions import InvalidValueError, AriaException
from ..utils import (FrozenList, FrozenDict, print_exception, deepcopy_with_locators, merge,
                     cachedmethod, puts, as_raw, full_type_name, safe_repr)
from .null import NULL
from .utils import validate_primitive

#
# Class decorators
#

# pylint: disable=unused-argument

def has_fields(cls):
    """
    Class decorator for validated field support.

    1. Adds a :code:`FIELDS` class property that is a dict of all the fields.
       Will inherit and merge :code:`FIELDS` properties from base classes if
       they have them.

    2. Generates automatic :code:`@property` implementations for the fields
       with the help of a set of special function decorators.

    The class also works with the Python dict protocol, so that
    fields can be accessed via dict semantics. The functionality is
    identical to that of using attribute access.

    The class will also gain two utility methods, :code:`_iter_field_names`
    and :code:`_iter_fields`.
    """

    # Make sure we have FIELDS
    if 'FIELDS' not in cls.__dict__:
        setattr(cls, 'FIELDS', OrderedDict())

    # Inherit FIELDS from base classes
    for base in cls.__bases__:
        if hasattr(base, 'FIELDS'):
            cls.FIELDS.update(base.FIELDS)

    # We could do this:
    #
    #  for name, field in cls.__dict__.iteritems():
    #
    # But dir() is better because it has a deterministic order (alphabetical)

    for name in dir(cls):
        field = getattr(cls, name)

        if isinstance(field, Field):
            # Accumulate
            cls.FIELDS[name] = field

            field.name = name
            field.container_cls = cls

            # This function is here just to create an enclosed scope for "field"
            def closure(field):

                # By convention, we have the getter wrap the original function.
                # (It is, for example, where the Python help() function will look for
                # docstrings when encountering a property.)
                @cachedmethod
                @wraps(field.func)
                def getter(self):
                    return field.get(self, None)

                def setter(self, value):
                    field.set(self, None, value)

                # Convert to Python property
                return property(fget=getter, fset=setter)

            setattr(cls, name, closure(field))

    # Bind methods
    setattr(cls, '_iter_field_names', MethodType(has_fields_iter_field_names, None, cls))
    setattr(cls, '_iter_fields', MethodType(has_fields_iter_fields, None, cls))

    # Behave like a dict
    setattr(cls, '__len__', MethodType(has_fields_len, None, cls))
    setattr(cls, '__getitem__', MethodType(has_fields_getitem, None, cls))
    setattr(cls, '__setitem__', MethodType(has_fields_setitem, None, cls))
    setattr(cls, '__delitem__', MethodType(has_fields_delitem, None, cls))
    setattr(cls, '__iter__', MethodType(has_fields_iter, None, cls))
    setattr(cls, '__contains__', MethodType(has_fields_contains, None, cls))

    return cls


def short_form_field(name):
    """
    Class decorator for specifying the short form field.

    The class must be decorated with :func:`has_fields`.
    """

    def decorator(cls):
        if hasattr(cls, name) and hasattr(cls, 'FIELDS') and (name in cls.FIELDS):
            setattr(cls, 'SHORT_FORM_FIELD', name)
            return cls
        else:
            raise AttributeError('@short_form_field must be used with '
                                 'a Field name in @has_fields class')
    return decorator


def allow_unknown_fields(cls):
    """
    Class decorator specifying that the class allows unknown fields.

    The class must be decorated with :func:`has_fields`.
    """

    if hasattr(cls, 'FIELDS'):
        setattr(cls, 'ALLOW_UNKNOWN_FIELDS', True)
        return cls
    else:
        raise AttributeError('@allow_unknown_fields must be used with a @has_fields class')

#
# Method decorators
#


def primitive_field(cls=None, default=None, allowed=None, required=False):
    """
    Method decorator for primitive fields.

    The function must be a method in a class decorated with :func:`has_fields`.
    """

    def decorator(func):
        return Field(field_variant='primitive', func=func, cls=cls, default=default,
                     allowed=allowed, required=required)
    return decorator


def primitive_list_field(cls=None, default=None, allowed=None, required=False):
    """
    Method decorator for list of primitive fields.

    The function must be a method in a class decorated with :func:`has_fields`.
    """

    def decorator(func):
        return Field(field_variant='primitive_list', func=func, cls=cls, default=default,
                     allowed=allowed, required=required)
    return decorator


def primitive_dict_field(cls=None, default=None, allowed=None, required=False):
    """
    Method decorator for dict of primitive fields.

    The function must be a method in a class decorated with :func:`has_fields`.
    """
    def decorator(func):
        return Field(field_variant='primitive_dict', func=func, cls=cls, default=default,
                     allowed=allowed, required=required)
    return decorator


def primitive_dict_unknown_fields(cls=None, default=None, allowed=None, required=False):
    """
    Method decorator for dict of primitive fields, for all the fields that are
    not already decorated.

    The function must be a method in a class decorated with :func:`has_fields`.
    """

    def decorator(func):
        return Field(field_variant='primitive_dict_unknown_fields', func=func, cls=cls,
                     default=default, allowed=allowed, required=required)
    return decorator


def object_field(cls, default=None, allowed=None, required=False):
    """
    Method decorator for object fields.

    The function must be a method in a class decorated with :func:`has_fields`.
    """
    def decorator(func):
        return Field(field_variant='object', func=func, cls=cls, default=default, allowed=allowed,
                     required=required)
    return decorator


def object_list_field(cls, default=None, allowed=None, required=False):
    """
    Method decorator for list of object fields.

    The function must be a method in a class decorated with :func:`has_fields`.
    """

    def decorator(func):
        return Field(field_variant='object_list', func=func, cls=cls, default=default,
                     allowed=allowed, required=required)
    return decorator


def object_dict_field(cls, default=None, allowed=None, required=False):
    """
    Method decorator for dict of object fields.

    The function must be a method in a class decorated with :func:`has_fields`.
    """

    def decorator(func):
        return Field(field_variant='object_dict', func=func, cls=cls, default=default,
                     allowed=allowed, required=required)
    return decorator


def object_sequenced_list_field(cls, default=None, allowed=None, required=False):
    """
    Method decorator for sequenced list of object fields.

    The function must be a method in a class decorated with :func:`has_fields`.
    """

    def decorator(func):
        return Field(field_variant='sequenced_object_list', func=func, cls=cls, default=default,
                     allowed=allowed, required=required)
    return decorator


def object_dict_unknown_fields(cls, default=None, allowed=None, required=False):
    """
    Method decorator for dict of object fields, for all the fields that are not already decorated.

    The function must be a method in a class decorated with :func:`has_fields`.
    """
    def decorator(func):
        return Field(field_variant='object_dict_unknown_fields', func=func, cls=cls,
                     default=default, allowed=allowed, required=required)
    return decorator


def field_getter(getter_func):
    """
    Method decorator for overriding the getter function of a field.

    The signature of the getter function must be: :code:`f(field, presentation, context)`.
    The default getter can be accessed as :code:`field.default_get(presentation, context)`.

    The function must already be decorated with a field decorator.
    """

    def decorator(field):
        if isinstance(field, Field):
            field.get = MethodType(getter_func, field, Field)
            return field
        else:
            raise AttributeError('@field_getter must be used with a Field')
    return decorator


def field_setter(setter_func):
    """
    Method decorator for overriding the setter function of a field.

    The signature of the setter function must be: :code:`f(field, presentation, context, value)`.
    The default setter can be accessed as :code:`field.default_set(presentation, context, value)`.

    The function must already be decorated with a field decorator.
    """

    def decorator(field):
        if isinstance(field, Field):
            field.set = MethodType(setter_func, field, Field)
            return field
        else:
            raise AttributeError('@field_setter must be used with a Field')
    return decorator


def field_validator(validator_fn):
    """
    Method decorator for overriding the validator function of a field.

    The signature of the validator function must be: :code:f(field, presentation, context)`.
    The default validator can be accessed as :code:`field.default_validate(presentation, context)`.

    The function must already be decorated with a field decorator.
    """

    def decorator(field):
        if isinstance(field, Field):
            field.validate = MethodType(validator_fn, field, Field)
            return field
        else:
            raise AttributeError('@field_validator must be used with a Field')
    return decorator

#
# Utils
#


def has_fields_iter_field_names(self):
    for name in self.__class__.FIELDS:
        yield name


def has_fields_iter_fields(self):
    return self.FIELDS.iteritems()


def has_fields_len(self):
    return len(self.__class__.FIELDS)


def has_fields_getitem(self, key):
    if not isinstance(key, basestring):
        raise TypeError('key must be a string')
    if key not in self.__class__.FIELDS:
        raise KeyError('no \'%s\' property' % key)
    return getattr(self, key)


def has_fields_setitem(self, key, value):
    if not isinstance(key, basestring):
        raise TypeError('key must be a string')
    if key not in self.__class__.FIELDS:
        raise KeyError('no \'%s\' property' % key)
    return setattr(self, key, value)


def has_fields_delitem(self, key):
    if not isinstance(key, basestring):
        raise TypeError('key must be a string')
    if key not in self.__class__.FIELDS:
        raise KeyError('no \'%s\' property' % key)
    return setattr(self, key, None)


def has_fields_iter(self):
    return self.__class__.FIELDS.iterkeys()


def has_fields_contains(self, key):
    if not isinstance(key, basestring):
        raise TypeError('key must be a string')
    return key in self.__class__.FIELDS


class Field(object):
    """
    Field handler used by :code:`@has_fields` decorator.
    """

    def __init__(self, field_variant, func, cls=None, default=None, allowed=None, required=False):
        if cls == str:
            # Use "unicode" instead of "str"
            cls = unicode

        self.container_cls = None
        self.name = None
        self.field_variant = field_variant
        self.func = func
        self.cls = cls
        self.default = default
        self.allowed = allowed
        self.required = required

    @property
    def full_name(self):
        return 'field "%s" in "%s"' % (self.name, full_type_name(self.container_cls))

    @property
    def full_cls_name(self):
        name = full_type_name(self.cls)
        if name == 'unicode':
            # For simplicity, display "unicode" as "str"
            name = 'str'
        return name

    def get(self, presentation, context):
        return self.default_get(presentation, context)

    def set(self, presentation, context, value):
        return self.default_set(presentation, context, value)

    def validate(self, presentation, context):
        self.default_validate(presentation, context)

    def get_locator(self, raw):
        if hasattr(raw, '_locator'):
            locator = raw._locator
            if locator is not None:
                return locator.get_child(self.name)
        return None

    def dump(self, presentation, context):
        value = getattr(presentation, self.name)
        if value is None:
            return

        dumper = getattr(self, '_dump_%s' % self.field_variant)
        dumper(context, value)

    def default_get(self, presentation, context):
        # Handle raw

        default_raw = (presentation._get_default_raw()
                       if hasattr(presentation, '_get_default_raw')
                       else None)

        if default_raw is None:
            raw = presentation._raw
        else:
            # Handle default raw value
            raw = deepcopy_with_locators(default_raw)
            merge(raw, presentation._raw)

        # Handle unknown fields

        if self.field_variant == 'primitive_dict_unknown_fields':
            return self._get_primitive_dict_unknown_fields(presentation, raw, context)
        elif self.field_variant == 'object_dict_unknown_fields':
            return self._get_object_dict_unknown_fields(presentation, raw, context)

        is_short_form_field = (self.container_cls.SHORT_FORM_FIELD == self.name
                               if hasattr(self.container_cls, 'SHORT_FORM_FIELD')
                               else False)
        is_dict = isinstance(raw, dict)

        # Find value

        value = self._find_value(is_short_form_field, is_dict, raw)

        # Handle required

        if value is None:
            if self.required:
                raise InvalidValueError('required %s does not have a value' % self.full_name,
                                        locator=self.get_locator(raw))
            else:
                return None

        # Handle allowed values

        if self.allowed is not None:
            if value not in self.allowed:
                raise InvalidValueError('%s is not %s'
                                        % (self.full_name, ' or '.join([safe_repr(v)
                                                                        for v in self.allowed])),
                                        locator=self.get_locator(raw))

        # Handle get according to variant

        getter = getattr(self, '_get_%s' % self.field_variant, None)

        if getter is None:
            locator = self.get_locator(raw)
            location = (' @%s' % locator) if locator is not None else ''
            raise AttributeError('%s has unsupported field variant: "%s"%s'
                                 % (self.full_name, self.field_variant, location))

        return getter(presentation, raw, value, context)

    def _find_value(self, is_short_form_field, is_dict, raw):
        value = None
        if is_short_form_field and not is_dict:
            # Handle short form
            value = raw
        elif is_dict:
            if self.name in raw:
                value = raw[self.name]
                if value is None:
                    # An explicit null
                    value = NULL
            else:
                value = self.default
        return value

    def default_set(self, presentation, context, value):
        raw = presentation._raw
        old = self.get(presentation, context)
        raw[self.name] = value
        try:
            self.validate(presentation, context)
        except Exception as e:
            raw[self.name] = old
            raise e
        return old

    def default_validate(self, presentation, context):
        value = None

        try:
            value = self.get(presentation, context)
        except AriaException as e:
            if e.issue:
                context.validation.report(issue=e.issue)
        except Exception as e:
            context.validation.report(exception=e)
            print_exception(e)

        self.validate_value(value, context)

    def validate_value(self, value, context):
        if isinstance(value, list):
            if self.field_variant == 'object_list':
                for element in value:
                    if hasattr(element, '_validate'):
                        element._validate(context)
            elif self.field_variant == 'sequenced_object_list':
                for _, element in value:
                    if hasattr(element, '_validate'):
                        element._validate(context)
        elif isinstance(value, dict):
            if self.field_variant in ('object_dict', 'object_dict_unknown_fields'):
                for inner_value in value.itervalues():
                    if hasattr(inner_value, '_validate'):
                        inner_value._validate(context)

        if hasattr(value, '_validate'):
            value._validate(context)

    @staticmethod
    def _get_context():
        thread_locals = threading.local()
        return getattr(thread_locals, 'aria_consumption_context', None)

    def _coerce_primitive(self, value, context):
        if context is None:
            context = Field._get_context()
        allow_primitive_coercion = (context.validation.allow_primitive_coersion
                                    if context is not None
                                    else True)
        return validate_primitive(value, self.cls, allow_primitive_coercion)

    # primitive

    def _get_primitive(self, presentation, raw, value, context):
        if (self.cls is not None and not isinstance(value, self.cls)
                and value is not None and value is not NULL):
            try:
                return self._coerce_primitive(value, context)
            except ValueError as e:
                raise InvalidValueError('%s is not a valid "%s": %s' %
                                        (self.full_name, self.full_cls_name, safe_repr(value)),
                                        locator=self.get_locator(raw), cause=e)
        return value

    def _dump_primitive(self, context, value):
        if hasattr(value, 'as_raw'):
            value = as_raw(value)
        puts('%s: %s' % (self.name, context.style.literal(value)))

    # primitive list

    def _get_primitive_list(self, presentation, raw, value, context):
        if not isinstance(value, list):
            raise InvalidValueError('%s is not a list: %s' % (self.full_name, safe_repr(value)),
                                    locator=self.get_locator(raw))
        primitive_list = value
        if self.cls is not None:
            if context is None:
                context = Field._get_context()
            primitive_list = []
            for i, _ in enumerate(value):
                primitive = value[i]
                try:
                    primitive = self._coerce_primitive(primitive, context)
                except ValueError as e:
                    raise InvalidValueError('%s is not a list of "%s": element %d is %s'
                                            % (self.full_name,
                                               self.full_cls_name,
                                               i,
                                               safe_repr(primitive)),
                                            locator=self.get_locator(raw), cause=e)
                if primitive in primitive_list:
                    raise InvalidValueError('%s has a duplicate "%s": %s'
                                            % (self.full_name,
                                               self.full_cls_name,
                                               safe_repr(primitive)),
                                            locator=self.get_locator(raw))
                primitive_list.append(primitive)
        return FrozenList(primitive_list)

    def _dump_primitive_list(self, context, value):
        puts('%s:' % self.name)
        with context.style.indent:
            for primitive in value:
                if hasattr(primitive, 'as_raw'):
                    primitive = as_raw(primitive)
                puts(context.style.literal(primitive))

    # primitive dict

    def _get_primitive_dict(self, presentation, raw, value, context):
        if not isinstance(value, dict):
            raise InvalidValueError('%s is not a dict: %s' % (self.full_name, safe_repr(value)),
                                    locator=self.get_locator(raw))
        primitive_dict = value
        if self.cls is not None:
            if context is None:
                context = Field._get_context()
            primitive_dict = OrderedDict()
            for k, v in value.iteritems():
                try:
                    primitive_dict[k] = self._coerce_primitive(v, context)
                except ValueError as e:
                    raise InvalidValueError('%s is not a dict of "%s" values: entry "%d" is %s'
                                            % (self.full_name, self.full_cls_name, k, safe_repr(v)),
                                            locator=self.get_locator(raw),
                                            cause=e)
        return FrozenDict(primitive_dict)

    def _dump_primitive_dict(self, context, value):
        puts('%s:' % self.name)
        with context.style.indent:
            for v in value.itervalues():
                if hasattr(v, 'as_raw'):
                    v = as_raw(v)
                puts(context.style.literal(v))

    # object

    def _get_object(self, presentation, raw, value, context):
        try:
            return self.cls(name=self.name, raw=value, container=presentation)
        except TypeError as e:
            raise InvalidValueError('%s cannot not be initialized to an instance of "%s": %s'
                                    % (self.full_name, self.full_cls_name, safe_repr(value)),
                                    cause=e,
                                    locator=self.get_locator(raw))

    def _dump_object(self, context, value):
        puts('%s:' % self.name)
        with context.style.indent:
            if hasattr(value, '_dump'):
                value._dump(context)

    # object list

    def _get_object_list(self, presentation, raw, value, context):
        if not isinstance(value, list):
            raise InvalidValueError('%s is not a list: %s'
                                    % (self.full_name, safe_repr(value)),
                                    locator=self.get_locator(raw))
        return FrozenList((self.cls(name=self.name, raw=v, container=presentation) for v in value))

    def _dump_object_list(self, context, value):
        puts('%s:' % self.name)
        with context.style.indent:
            for v in value:
                if hasattr(v, '_dump'):
                    v._dump(context)

    # object dict

    def _get_object_dict(self, presentation, raw, value, context):
        if not isinstance(value, dict):
            raise InvalidValueError('%s is not a dict: %s' % (self.full_name, safe_repr(value)),
                                    locator=self.get_locator(raw))
        return FrozenDict(((k, self.cls(name=k, raw=v, container=presentation))
                           for k, v in value.iteritems()))

    def _dump_object_dict(self, context, value):
        puts('%s:' % self.name)
        with context.style.indent:
            for v in value.itervalues():
                if hasattr(v, '_dump'):
                    v._dump(context)

    # sequenced object list

    def _get_sequenced_object_list(self, presentation, raw, value, context):
        if not isinstance(value, list):
            raise InvalidValueError('%s is not a sequenced list (a list of dicts, '
                                    'each with exactly one key): %s'
                                    % (self.full_name, safe_repr(value)),
                                    locator=self.get_locator(raw))
        sequence = []
        for v in value:
            if not isinstance(v, dict):
                raise InvalidValueError('%s list elements are not all dicts with '
                                        'exactly one key: %s' % (self.full_name, safe_repr(value)),
                                        locator=self.get_locator(raw))
            if len(v) != 1:
                raise InvalidValueError('%s list elements do not all have exactly one key: %s'
                                        % (self.full_name, safe_repr(value)),
                                        locator=self.get_locator(raw))
            key, value = v.items()[0]
            sequence.append((key, self.cls(name=key, raw=value, container=presentation)))
        return FrozenList(sequence)

    def _dump_sequenced_object_list(self, context, value):
        puts('%s:' % self.name)
        for _, v in value:
            if hasattr(v, '_dump'):
                v._dump(context)

    # primitive dict for unknown fields

    def _get_primitive_dict_unknown_fields(self, presentation, raw, context):
        if isinstance(raw, dict):
            primitive_dict = raw
            if self.cls is not None:
                if context is None:
                    context = Field._get_context()
                primitive_dict = OrderedDict()
                for k, v in raw.iteritems():
                    if k not in presentation.FIELDS:
                        try:
                            primitive_dict[k] = self._coerce_primitive(v, context)
                        except ValueError as e:
                            raise InvalidValueError('%s is not a dict of "%s" values:'
                                                    ' entry "%d" is %s'
                                                    % (self.full_name, self.full_cls_name,
                                                       k, safe_repr(v)),
                                                    locator=self.get_locator(raw),
                                                    cause=e)
            return FrozenDict(primitive_dict)
        return None

    def _dump_primitive_dict_unknown_fields(self, context, value):
        self._dump_primitive_dict(context, value)

    # object dict for unknown fields

    def _get_object_dict_unknown_fields(self, presentation, raw, context):
        if isinstance(raw, dict):
            return FrozenDict(((k, self.cls(name=k, raw=v, container=presentation))
                               for k, v in raw.iteritems() if k not in presentation.FIELDS))
        return None

    def _dump_object_dict_unknown_fields(self, context, value):
        self._dump_object_dict(context, value)
